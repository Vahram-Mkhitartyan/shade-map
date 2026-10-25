/* Offline graph search. All sunlight fields are calculated by Python. */
"use strict";

class MinHeap {
  constructor() {
    this.items = [];
  }
  push(item) {
    this.items.push(item);
    let index = this.items.length - 1;
    while (index > 0) {
      const parent = (index - 1) >> 1;
      if (this.items[parent][0] <= item[0]) break;
      this.items[index] = this.items[parent];
      index = parent;
    }
    this.items[index] = item;
  }
  pop() {
    const first = this.items[0];
    const last = this.items.pop();
    if (this.items.length) {
      let index = 0;
      while (index * 2 + 1 < this.items.length) {
        let child = index * 2 + 1;
        if (
          child + 1 < this.items.length &&
          this.items[child + 1][0] < this.items[child][0]
        )
          child++;
        if (this.items[child][0] >= last[0]) break;
        this.items[index] = this.items[child];
        index = child;
      }
      this.items[index] = last;
    }
    return first;
  }
  get size() {
    return this.items.length;
  }
}

class OfflineRouter {
  constructor(network) {
    this.network = network;
    this.adjacency = network.points.map(() => []);
    network.edges.forEach(([first, second, length], index) => {
      this.adjacency[first].push([second, length, index]);
      this.adjacency[second].push([first, length, index]);
    });
    this.decoded = new Map();
  }

  sunlight(minute) {
    // Same five-minute nearest-bin convention as Python's field export.
    const index = Math.round(
      (minute - this.network.first_minute) / this.network.bin_minutes,
    );
    if (index < 0 || index >= this.network.sunlight.length) {
      throw new Error(
        "This walk extends beyond the available solar times. Choose a shorter walk or earlier departure.",
      );
    }
    if (!this.decoded.has(index)) {
      const binary = atob(this.network.sunlight[index]);
      this.decoded.set(
        index,
        Uint8Array.from(binary, (value) => value.charCodeAt(0)),
      );
      if (this.decoded.size > 12)
        this.decoded.delete(this.decoded.keys().next().value);
    }
    return this.decoded.get(index);
  }

  nearestNode(point, maximumDistance = 100) {
    let best = -1;
    let distance = Infinity;
    this.network.points.forEach(([east, north], index) => {
      const candidate = Math.hypot(point[0] - east, point[1] - north);
      if (candidate < distance) {
        best = index;
        distance = candidate;
      }
    });
    if (distance > maximumDistance) {
      throw new Error(
        `Pin is ${Math.round(distance)} m from a connected mapped path. Move it within ${maximumDistance} m of a path.`,
      );
    }
    return { node: best, distance };
  }

  edgeConditions(edge, minute, conditions = []) {
    const result = { blocked: false, delay: 0, penalty: 0 };
    for (const condition of conditions) {
      if (condition.edge !== edge) continue;
      if (condition.startsAt != null && minute < condition.startsAt) continue;
      if (condition.expiresAt != null && minute >= condition.expiresAt)
        continue;
      if (condition.kind === "blocked") result.blocked = true;
      if (condition.kind === "delay") result.delay += condition.seconds || 0;
      if (condition.kind === "discomfort")
        result.penalty += condition.penaltySeconds || 0;
    }
    return result;
  }

  shortestPath(start, finish, departure, shadeWeight, conditions = []) {
    // Keep one best label per node/time bucket. A single label per node is not
    // sufficient when arriving later changes the shadow or an active condition.
    const bucketSeconds = this.network.routing_bin_seconds || 30;
    const best = new Map();
    const labels = [
      {
        node: start,
        cost: 0,
        elapsed: 0,
        previous: -1,
        edge: -1,
      },
    ];
    const heap = new MinHeap();
    best.set(`${start}:0`, 0);
    heap.push([0, 0]);
    let finishLabel = -1;
    while (heap.size) {
      const [cost, labelIndex] = heap.pop();
      const label = labels[labelIndex];
      if (cost !== label.cost) continue;
      const { node, elapsed } = label;
      if (node === finish) {
        finishLabel = labelIndex;
        break;
      }
      for (const [next, length, edge] of this.adjacency[node]) {
        const [, , , delay = 0, schedule] = this.network.edges[edge];
        const entry = departure + elapsed / 60;
        const live = this.edgeConditions(edge, entry, conditions);
        if (live.blocked) continue;
        const seconds = length / 1.4 + delay + live.delay;
        const nextElapsed = elapsed + seconds;
        if (nextElapsed > this.network.max_walk_seconds) continue;
        const end = departure + nextElapsed / 60;
        if (!this.isOpen(schedule, entry, end)) continue;
        const sunlight = this.sunlight(entry + seconds / 120);
        const nextCost =
          cost +
          seconds * (1 + (shadeWeight * sunlight[edge]) / 255) +
          live.penalty;
        const bucket = Math.round(nextElapsed / bucketSeconds);
        const key = `${next}:${bucket}`;
        if (nextCost >= (best.get(key) ?? Infinity)) continue;
        const nextLabel = labels.length;
        best.set(key, nextCost);
        labels.push({
          node: next,
          cost: nextCost,
          elapsed: nextElapsed,
          previous: labelIndex,
          edge,
        });
        heap.push([nextCost, nextLabel]);
      }
    }
    if (finishLabel === -1)
      throw new Error("No connected walking path joins these pins.");
    const nodes = [],
      edges = [];
    for (
      let index = finishLabel;
      index !== -1;
      index = labels[index].previous
    ) {
      nodes.push(labels[index].node);
      if (labels[index].edge !== -1) edges.push(labels[index].edge);
    }
    return { nodes: nodes.reverse(), edges: edges.reverse() };
  }

  isOpen(schedule, start, end) {
    if (!schedule) return true;
    const [opening, closing] = schedule[this.network.weekday ?? 1];
    return opening <= start && end <= closing;
  }

  score(path, departure, conditions = []) {
    let duration = 0;
    let sunny = 0;
    let distance = 0;
    const passages = new Set();
    for (const edge of path.edges) {
      const [, , length, delay = 0, schedule, passage] =
        this.network.edges[edge];
      const entry = departure + duration / 60;
      const live = this.edgeConditions(edge, entry, conditions);
      if (live.blocked) throw new Error("A live condition blocks this route.");
      const seconds = length / 1.4 + delay + live.delay;
      if (
        !this.isOpen(
          schedule,
          departure + duration / 60,
          departure + (duration + seconds) / 60,
        )
      ) {
        throw new Error("An indoor passage closes before this walk completes.");
      }
      distance += length;
      if (passage) passages.add(passage);
      // Each edge's field aggregates 3 m samples. Advance to its midpoint time.
      const sunlight = this.sunlight(entry + seconds / 120);
      sunny += (seconds * sunlight[edge]) / 255;
      duration += seconds;
    }
    if (duration > this.network.max_walk_seconds) {
      throw new Error(
        "This offline prototype supports walks up to two hours. Choose closer endpoints.",
      );
    }
    return {
      ...path,
      points: path.nodes.map((node) => this.network.points[node]),
      duration,
      sunny,
      distance,
      passages: [...passages],
      shade: duration ? Math.round(100 * (1 - sunny / duration)) : 0,
    };
  }

  routes(startPoint, finishPoint, departure, conditions = []) {
    const start = this.nearestNode(startPoint);
    const finish = this.nearestNode(finishPoint);
    const shortest = this.shortestPath(
      start.node,
      finish.node,
      departure,
      0,
      conditions,
    );
    const baseline = this.score(shortest, departure, conditions);
    baseline.name = "Shortest walk";
    const candidates = [baseline];
    const seen = new Set([shortest.nodes.join(",")]);
    for (const weight of [1, 3, 8]) {
      const path = this.shortestPath(
        start.node,
        finish.node,
        departure,
        weight,
        conditions,
      );
      const key = path.nodes.join(",");
      if (seen.has(key)) continue;
      seen.add(key);
      const length = path.edges.reduce(
        (sum, edge) => sum + this.network.edges[edge][2],
        0,
      );
      if (length > baseline.distance * 1.35 + 0.001) continue;
      const candidate = this.score(path, departure, conditions);
      candidate.name = `Shade candidate ${candidates.length}`;
      candidates.push(candidate);
    }
    return { candidates, offsets: [start.distance, finish.distance] };
  }
}

class LiveRouteSession {
  constructor(router, { replanSeconds = 30 } = {}) {
    this.router = router;
    this.replanSeconds = replanSeconds;
    this.conditions = [];
    this.events = [];
    this.position = null;
    this.destination = null;
    this.observedMinute = null;
    this.lastPlanMinute = null;
    this.lastNode = null;
    this.plan = null;
  }

  begin(position, destination, minute) {
    this.position = position;
    this.destination = destination;
    this.observedMinute = minute;
    return this.replan("started");
  }

  updatePosition(position, minute) {
    if (this.destination == null)
      throw new Error("Live route has not started.");
    if (minute < this.observedMinute)
      throw new Error("Observed time cannot move backwards.");
    this.position = position;
    this.observedMinute = minute;
    const node = this.router.nearestNode(position).node;
    if (
      node !== this.lastNode ||
      minute - this.lastPlanMinute >= this.replanSeconds / 60
    ) {
      return this.replan("position update");
    }
    return this.plan;
  }

  addDelay(seconds, reason = "unplanned stop") {
    if (!(seconds >= 0)) throw new Error("Delay must be non-negative.");
    this.observedMinute += seconds / 60;
    this.events.push({
      kind: "delay",
      reason,
      seconds,
      minute: this.observedMinute,
    });
    return this.replan(reason);
  }

  reportCondition(condition) {
    if (!Number.isInteger(condition.edge))
      throw new Error("A condition needs a graph edge index.");
    this.conditions.push({ ...condition });
    this.events.push({ ...condition, minute: this.observedMinute });
    return this.replan(condition.reason || condition.kind);
  }

  replan(reason) {
    const active = this.conditions.filter(
      (condition) =>
        condition.expiresAt == null ||
        condition.expiresAt > this.observedMinute,
    );
    this.conditions = active;
    const result = this.router.routes(
      this.position,
      this.destination,
      this.observedMinute,
      active,
    );
    this.lastNode = this.router.nearestNode(this.position).node;
    this.lastPlanMinute = this.observedMinute;
    this.plan = { ...result, reason, calculatedAt: this.observedMinute };
    return this.plan;
  }
}

if (typeof module !== "undefined")
  module.exports = { OfflineRouter, LiveRouteSession, MinHeap };
