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
  constructor(network, { access = [] } = {}) {
    this.network = network;
    this.access = new Set(access);
    this.indoorNodes = new Set(network.indoor_nodes || []);
    this.adjacency = network.points.map(() => []);
    network.edges.forEach(([first, second, length], index) => {
      this.adjacency[first].push([second, length, index]);
      this.adjacency[second].push([first, length, index]);
    });
    this.decoded = new Map();
  }

  setAccess(name, allowed) {
    if (allowed) this.access.add(name);
    else this.access.delete(name);
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
      // Map pins represent outdoor positions. Enter a building through its
      // doorway edge instead of snapping directly behind an access check.
      if (this.indoorNodes.has(index)) return;
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

  canUse(requiredAccess, accessAfter, end) {
    if (!requiredAccess || accessAfter == null || end <= accessAfter)
      return true;
    return this.access.has(requiredAccess);
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
        const [, , , delay = 0, schedule, , accessAfter, requiredAccess] =
          this.network.edges[edge];
        const entry = departure + elapsed / 60;
        const live = this.edgeConditions(edge, entry, conditions);
        if (live.blocked) continue;
        const seconds = length / 1.4 + delay + live.delay;
        const nextElapsed = elapsed + seconds;
        if (nextElapsed > this.network.max_walk_seconds) continue;
        const end = departure + nextElapsed / 60;
        if (!this.isOpen(schedule, entry, end)) continue;
        if (!this.canUse(requiredAccess, accessAfter, end)) continue;
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
      const [
        ,
        ,
        length,
        delay = 0,
        schedule,
        passage,
        accessAfter,
        requiredAccess,
      ] = this.network.edges[edge];
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
      if (
        !this.canUse(
          requiredAccess,
          accessAfter,
          departure + (duration + seconds) / 60,
        )
      ) {
        throw new Error("This indoor passage requires ASU ID at that time.");
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

  routes(
    startPoint,
    finishPoint,
    departure,
    conditions = [],
    startNode = null,
  ) {
    // A live walker is already committed to a graph edge. Its next route node
    // is a safer search anchor than an unrelated path that happens to be closer.
    const start = Number.isInteger(startNode)
      ? {
          node: startNode,
          distance: Math.hypot(
            startPoint[0] - this.network.points[startNode][0],
            startPoint[1] - this.network.points[startNode][1],
          ),
        }
      : this.nearestNode(startPoint);
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
  constructor(
    router,
    {
      replanSeconds = 30,
      preference = "shade",
      shadeWeight = 3,
      minimumSwitchGainSeconds = 20,
    } = {},
  ) {
    this.router = router;
    this.replanSeconds = replanSeconds;
    this.preference = preference;
    this.shadeWeight = shadeWeight;
    this.minimumSwitchGainSeconds = minimumSwitchGainSeconds;
    this.conditions = [];
    this.events = [];
    this.position = null;
    this.destination = null;
    this.observedMinute = null;
    this.lastPlanMinute = null;
    this.lastNode = null;
    this.plan = null;
    this.selectedRoute = null;
    this.routeAnchorNode = null;
  }

  begin(position, destination, minute) {
    this.position = position;
    this.destination = destination;
    this.observedMinute = minute;
    this.routeAnchorNode = this.router.nearestNode(position).node;
    return this.replan("started");
  }

  updatePosition(position, minute, routeAnchorNode = null) {
    if (this.destination == null)
      throw new Error("Live route has not started.");
    if (minute < this.observedMinute)
      throw new Error("Observed time cannot move backwards.");
    this.position = position;
    this.observedMinute = minute;
    // Simulators and future navigation clients can preserve the committed
    // segment. Callers without that context still receive nearest-node behavior.
    const node = Number.isInteger(routeAnchorNode)
      ? routeAnchorNode
      : this.router.nearestNode(position).node;
    this.routeAnchorNode = node;
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
    const savedConditions = [...this.conditions];
    this.conditions.push({ ...condition });
    try {
      const plan = this.replan(condition.reason || condition.kind);
      this.events.push({ ...condition, minute: this.observedMinute });
      return plan;
    } catch (error) {
      this.conditions = savedConditions;
      throw error;
    }
  }

  setPreference(preference) {
    if (!new Set(["fastest", "shade"]).has(preference))
      throw new Error("Preference must be fastest or shade.");
    this.preference = preference;
    if (this.destination == null) return this.plan;
    return this.replan("preference changed");
  }

  routeCost(route) {
    if (this.preference === "fastest") return route.duration;
    return route.duration + this.shadeWeight * route.sunny;
  }

  routeKey(route) {
    return route ? `${route.nodes.join(",")}|${route.edges.join(",")}` : "";
  }

  remainingRoute(node) {
    if (!this.selectedRoute) return null;
    const index = this.selectedRoute.nodes.lastIndexOf(node);
    if (index < 0) return null;
    try {
      const remaining = this.router.score(
        {
          nodes: this.selectedRoute.nodes.slice(index),
          edges: this.selectedRoute.edges.slice(index),
        },
        this.observedMinute,
        this.conditions,
      );
      remaining.name = this.selectedRoute.name;
      return remaining;
    } catch {
      return null;
    }
  }

  replan(reason) {
    const active = this.conditions.filter(
      (condition) =>
        condition.expiresAt == null ||
        condition.expiresAt > this.observedMinute,
    );
    this.conditions = active;
    const currentNode = Number.isInteger(this.routeAnchorNode)
      ? this.routeAnchorNode
      : this.router.nearestNode(this.position).node;
    const result = this.router.routes(
      this.position,
      this.destination,
      this.observedMinute,
      active,
      currentNode,
    );
    const current = this.remainingRoute(currentNode);
    const best = result.candidates
      .map((route, index) => ({ route, index, cost: this.routeCost(route) }))
      .sort((left, right) => left.cost - right.cost)[0];
    if (!best) throw new Error("No route candidates are available.");

    const hasPreviousRoute = this.selectedRoute != null;
    let selected = best.route;
    let routeChanged = !hasPreviousRoute || current == null;
    let switchGainSeconds = null;
    let decision = hasPreviousRoute
      ? "current route unavailable"
      : "initial route";
    if (current) {
      const currentCost = this.routeCost(current);
      switchGainSeconds = currentCost - best.cost;
      const sameRoute = this.routeKey(current) === this.routeKey(best.route);
      if (sameRoute) {
        selected = best.route;
        routeChanged = false;
        decision = "route remains best";
      } else if (switchGainSeconds < this.minimumSwitchGainSeconds) {
        selected = current;
        routeChanged = false;
        decision = `kept current route; gain below ${this.minimumSwitchGainSeconds} s`;
        if (
          !result.candidates.some(
            (candidate) => this.routeKey(candidate) === this.routeKey(current),
          )
        )
          result.candidates.push(current);
      } else {
        routeChanged = true;
        decision = `switched for ${Math.round(switchGainSeconds)} s of weighted gain`;
      }
    }

    this.selectedRoute = selected;
    this.lastNode = currentNode;
    this.lastPlanMinute = this.observedMinute;
    this.plan = {
      ...result,
      reason,
      calculatedAt: this.observedMinute,
      selectedRoute: selected,
      routeChanged,
      switchGainSeconds,
      decision,
    };
    return this.plan;
  }
}

class LiveWalkSimulator {
  constructor(session, { stepSeconds = 10 } = {}) {
    this.session = session;
    this.stepSeconds = stepSeconds;
    this.position = null;
    this.destination = null;
    this.routePoints = [];
    this.routePointNodes = [];
    this.routeDuration = 0;
    this.routeElapsed = 0;
    this.routeSegmentIndex = 0;
    this.started = false;
    this.finished = false;
  }

  begin(position, destination, minute) {
    this.position = [...position];
    this.destination = [...destination];
    this.started = true;
    this.finished = false;
    const plan = this.session.begin(position, destination, minute);
    this.usePlan(plan);
    return this.snapshot(plan);
  }

  usePlan(plan) {
    const route = plan.selectedRoute;
    const points = route.points.map((point) => [...point]);
    const pointNodes = [...route.nodes];
    if (
      !points.length ||
      Math.hypot(
        points[0][0] - this.position[0],
        points[0][1] - this.position[1],
      ) > 0.01
    ) {
      points.unshift([...this.position]);
      pointNodes.unshift(null);
    }
    this.routePoints = points;
    this.routePointNodes = pointNodes;
    this.routeDuration = route.duration;
    this.routeElapsed = 0;
    this.routeSegmentIndex = 0;
  }

  progressAt(fraction) {
    if (!this.routePoints.length)
      return {
        position: [...this.position],
        routeAnchorNode: this.session.routeAnchorNode,
        segmentIndex: 0,
      };
    if (this.routePoints.length === 1)
      return {
        position: [...this.routePoints[0]],
        routeAnchorNode: this.routePointNodes[0],
        segmentIndex: 0,
      };
    const segments = [];
    let total = 0;
    for (let index = 1; index < this.routePoints.length; index++) {
      const start = this.routePoints[index - 1];
      const finish = this.routePoints[index];
      const length = Math.hypot(finish[0] - start[0], finish[1] - start[1]);
      segments.push({
        start,
        finish,
        length,
        routeAnchorNode: this.routePointNodes[index],
      });
      total += length;
    }
    let remaining = Math.max(0, Math.min(1, fraction)) * total;
    for (const [segmentIndex, segment] of segments.entries()) {
      if (remaining <= segment.length) {
        const amount = segment.length ? remaining / segment.length : 0;
        return {
          position: [
            segment.start[0] + (segment.finish[0] - segment.start[0]) * amount,
            segment.start[1] + (segment.finish[1] - segment.start[1]) * amount,
          ],
          routeAnchorNode: segment.routeAnchorNode,
          segmentIndex,
        };
      }
      remaining -= segment.length;
    }
    return {
      position: [...this.routePoints.at(-1)],
      routeAnchorNode: this.routePointNodes.at(-1),
      segmentIndex: Math.max(0, segments.length - 1),
    };
  }

  remainingPoints() {
    if (!this.position) return [];
    const future = this.routePoints.slice(this.routeSegmentIndex + 1);
    if (
      future.length &&
      Math.hypot(
        future[0][0] - this.position[0],
        future[0][1] - this.position[1],
      ) < 0.01
    )
      future.shift();
    return [[...this.position], ...future.map((point) => [...point])];
  }

  advance(seconds = this.stepSeconds) {
    if (!this.started) throw new Error("Simulation has not started.");
    if (this.finished) return this.snapshot(this.session.plan);
    if (!(seconds > 0)) throw new Error("Simulation step must be positive.");
    const previousPlan = this.session.plan;
    this.routeElapsed = Math.min(
      this.routeDuration,
      this.routeElapsed + seconds,
    );
    const fraction = this.routeDuration
      ? this.routeElapsed / this.routeDuration
      : 1;
    const progress = this.progressAt(fraction);
    this.position = progress.position;
    this.routeSegmentIndex = progress.segmentIndex;
    const minute = this.session.observedMinute + seconds / 60;
    const plan = this.session.updatePosition(
      this.position,
      minute,
      progress.routeAnchorNode,
    );
    if (fraction >= 1) {
      this.position = [...this.destination];
      this.finished = true;
    } else if (plan !== previousPlan && plan.routeChanged) {
      this.usePlan(plan);
    }
    return this.snapshot(plan);
  }

  addDelay(seconds, reason) {
    if (!this.started) throw new Error("Simulation has not started.");
    const plan = this.session.addDelay(seconds, reason);
    this.usePlan(plan);
    return this.snapshot(plan);
  }

  reportCondition(condition) {
    if (!this.started) throw new Error("Simulation has not started.");
    const plan = this.session.reportCondition(condition);
    this.usePlan(plan);
    return this.snapshot(plan);
  }

  nextEdge() {
    return this.session.plan?.selectedRoute?.edges?.[0] ?? null;
  }

  snapshot(plan) {
    return {
      position: this.position ? [...this.position] : null,
      minute: this.session.observedMinute,
      plan,
      finished: this.finished,
      remainingPoints: this.remainingPoints(),
    };
  }
}

if (typeof module !== "undefined")
  module.exports = {
    OfflineRouter,
    LiveRouteSession,
    LiveWalkSimulator,
    MinHeap,
  };
