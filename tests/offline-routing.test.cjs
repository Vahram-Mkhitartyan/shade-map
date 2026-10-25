const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const {
  OfflineRouter,
  LiveRouteSession,
  MinHeap,
} = require("../demo/offline-routing.js");
const { constrainView } = require("../demo/map-viewport.js");

function fixture() {
  return new OfflineRouter({
    points: [
      [0, 0],
      [100, 0],
      [50, 40],
    ],
    edges: [
      [0, 1, 100],
      [0, 2, 60],
      [2, 1, 60],
    ],
    first_minute: 480,
    bin_minutes: 5,
    max_walk_seconds: 7200,
    sunlight: Array.from({ length: 133 }, () =>
      Buffer.from([255, 0, 0]).toString("base64"),
    ),
  });
}

test("heap orders costs including repeated values", () => {
  const heap = new MinHeap();
  [9, 1, 5, 1, 17, 2].forEach((cost) => heap.push([cost, cost]));
  assert.deepEqual(
    Array.from({ length: 6 }, () => heap.pop()[0]),
    [1, 1, 2, 5, 9, 17],
  );
});
test("arbitrary endpoints produce shaded candidates within detour cap", () => {
  const result = fixture().routes([1, 0], [99, 0], 480);
  assert.equal(result.candidates[0].distance, 100);
  assert.equal(result.candidates[1].distance, 120);
  assert.equal(result.candidates[1].sunny, 0);
  assert.deepEqual(result.offsets, [1, 1]);
});
test("same point is safe, distant pins and disconnected trips fail explicitly", () => {
  const router = fixture();
  assert.equal(router.routes([0, 0], [0, 0], 480).candidates[0].duration, 0);
  assert.throws(
    () => router.routes([1000, 1000], [0, 0], 480),
    /connected mapped path/,
  );
  assert.throws(() => router.sunlight(2000), /available solar times/);
  router.adjacency[0] = [];
  assert.throws(() => router.shortestPath(0, 1, 480, 0), /No connected/);
});
test("exposure advances arrival time into the next solar bin", () => {
  const router = new OfflineRouter({
    points: [
      [0, 0],
      [500, 0],
      [1000, 0],
    ],
    edges: [
      [0, 1, 500],
      [1, 2, 500],
    ],
    first_minute: 480,
    bin_minutes: 5,
    max_walk_seconds: 7200,
    sunlight: Array.from({ length: 6 }, (_, i) =>
      Buffer.from(i === 0 ? [255, 255] : [0, 0]).toString("base64"),
    ),
  });
  const result = router.score({ nodes: [0, 1, 2], edges: [0, 1] }, 480);
  assert.equal(result.sunny, 0);
  assert.ok(result.duration > 700);
});
test("view constraints withstand extreme drags and zooms", () => {
  const bounds = [-2000, -1500, 1000, 2000];
  for (const aspect of [0.5, 1, 2])
    for (const x of [-1e6, -1000, 1e6])
      for (const width of [1, 500, 1e6]) {
        const view = constrainView(
          [x, x, width, width / aspect],
          bounds,
          aspect,
        );
        assert.ok(view[0] >= bounds[0] - 1e-8);
        assert.ok(view[1] >= -bounds[3] - 1e-8);
        assert.ok(view[0] + view[2] <= bounds[2] + 1e-8);
        assert.ok(view[1] + view[3] <= -bounds[1] + 1e-8);
      }
});
const payloadPath = path.resolve(__dirname, "../.cache/campus-payload.json");
test(
  "real exported field supports new near-campus and off-campus pins",
  { skip: !fs.existsSync(payloadPath) },
  () => {
    const campus = JSON.parse(fs.readFileSync(payloadPath, "utf8"));
    const router = new OfflineRouter(campus.network);
    assert.equal(campus.network.sunlight.length, 133);
    for (const frame of campus.network.sunlight)
      assert.equal(
        Buffer.from(frame, "base64").length,
        campus.network.edges.length,
      );
    for (const scenario of campus.scenarios) {
      const [start, finish] = scenario.nodes.map(
        (node) => campus.network.points[node],
      );
      const result = router.routes(
        [start[0] + 5, start[1] + 3],
        [finish[0] + 7, finish[1]],
        840,
      );
      assert.ok(result.candidates.length >= 1);
      assert.ok(
        result.candidates.every(
          (route) =>
            Number.isFinite(route.sunny) && route.sunny <= route.duration,
        ),
      );
      assert.ok(
        result.candidates.every(
          (route) =>
            route.distance <= result.candidates[0].distance * 1.35 + 0.001,
        ),
      );
    }
  },
);

test(
  "confirmed Creativity Commons path is connected and receives cover credit",
  { skip: !fs.existsSync(payloadPath) },
  () => {
    const campus = JSON.parse(fs.readFileSync(payloadPath, "utf8"));
    const walkway = campus.covered_walkways.find(
      (path) => path.id === "creativity-commons-west-colonnade",
    );
    assert.equal(walkway.routing_enabled, true);
    assert.equal(walkway.both_ends_connected, true);
    const router = new OfflineRouter(campus.network);
    const result = router.routes(walkway.points[0], walkway.points[1], 840);
    assert.ok(result.candidates[0].distance > 60);
    assert.ok(result.candidates[0].distance < 90);
    assert.equal(result.candidates[0].sunny, 0);
    assert.ok(result.offsets.every((distance) => distance < 0.02));
  },
);

test("indoor schedule uses arrival and exit time with outdoor fallback", () => {
  const router = fixture();
  router.network.weekday = 6;
  const schedule = Array.from({ length: 7 }, () => [600, 610]);
  for (const edge of [1, 2]) {
    router.network.edges[edge].push(10, schedule, "test-lobby");
  }
  const morning = router.routes([0, 0], [100, 0], 599);
  assert.ok(morning.candidates.every((route) => !route.passages.length));
  const open = router.routes([0, 0], [100, 0], 600);
  const indoor = open.candidates.find((route) => route.passages.length);
  assert.ok(indoor);
  assert.equal(indoor.distance, 120);
  assert.ok(Math.abs(indoor.duration - (120 / 1.4 + 20)) < 1e-8);
  const closing = router.routes([0, 0], [100, 0], 609.5);
  assert.ok(closing.candidates.every((route) => !route.passages.length));
});

test("search evaluates sunlight at predicted edge arrival time", () => {
  const router = new OfflineRouter({
    points: [
      [0, 0],
      [420, 0],
      [840, 0],
      [420, 100],
    ],
    edges: [
      [0, 1, 420],
      [1, 2, 420],
      [0, 3, 430],
      [3, 2, 430],
    ],
    first_minute: 480,
    bin_minutes: 5,
    max_walk_seconds: 7200,
    weekday: 1,
    sunlight: Array.from({ length: 10 }, (_, index) =>
      Buffer.from(index < 1 ? [0, 0, 255, 255] : [255, 255, 0, 0]).toString(
        "base64",
      ),
    ),
  });
  const shaded = router.shortestPath(0, 2, 480, 8);
  assert.deepEqual(shaded.nodes, [0, 3, 2]);
});

test("time-expanded search keeps distinct arrival windows at a node", () => {
  const router = new OfflineRouter({
    points: [
      [0, 0],
      [280, 0],
      [0, 1],
      [560, 0],
    ],
    edges: [
      [0, 1, 280],
      [0, 2, 1],
      [2, 1, 699],
      [1, 3, 280],
    ],
    first_minute: 480,
    bin_minutes: 5,
    routing_bin_seconds: 30,
    max_walk_seconds: 7200,
    weekday: 1,
    sunlight: Array.from({ length: 10 }, (_, index) =>
      Buffer.from(index <= 1 ? [0, 0, 0, 255] : [0, 0, 0, 0]).toString(
        "base64",
      ),
    ),
  });
  const path = router.shortestPath(0, 3, 480, 8);
  assert.deepEqual(path.nodes, [0, 2, 1, 3]);
});

test("live session replans after delays and expiring edge conditions", () => {
  const router = fixture();
  const session = new LiveRouteSession(router);
  session.begin([0, 0], [100, 0], 480);
  assert.equal(session.plan.calculatedAt, 480);
  session.addDelay(120, "stopped to talk");
  assert.equal(session.observedMinute, 482);
  assert.equal(session.plan.reason, "stopped to talk");
  session.reportCondition({
    edge: 0,
    kind: "blocked",
    reason: "crossing closed",
    expiresAt: 490,
  });
  assert.deepEqual(session.plan.candidates[0].nodes, [0, 2, 1]);
  session.updatePosition([0, 0], 491);
  assert.deepEqual(session.plan.candidates[0].nodes, [0, 1]);
});

test("live discomfort changes preference without changing travel time", () => {
  const router = fixture();
  const normal = router.routes([0, 0], [100, 0], 480);
  assert.deepEqual(normal.candidates[0].nodes, [0, 1]);
  const changed = router.routes([0, 0], [100, 0], 480, [
    { edge: 0, kind: "discomfort", penaltySeconds: 100 },
  ]);
  assert.deepEqual(changed.candidates[0].nodes, [0, 2, 1]);
  assert.equal(changed.candidates[0].duration, 120 / 1.4);
});

test(
  "exported MU and Hayden corridors route indoors with door delays",
  {
    skip: !fs.existsSync(payloadPath),
  },
  () => {
    const campus = JSON.parse(fs.readFileSync(payloadPath, "utf8"));
    const router = new OfflineRouter(campus.network);
    for (const id of ["mu-main-public-corridor", "hayden-level-one"]) {
      const passage = campus.indoor_passages.find((p) => p.id === id);
      assert.ok(passage);
      const points = [passage.lines[0][0], passage.lines.at(-1)[1]];
      const result = router.routes(...points, 840);
      assert.ok(result.candidates.some((route) => route.passages.includes(id)));
      const edges = campus.network.edges.filter((edge) => edge[5] === id);
      const corridor = edges.filter((edge) => !edge[3]);
      assert.ok(corridor.length >= 2);
      assert.ok(edges.filter((edge) => edge[3]).length >= 2);
      for (const edge of corridor) {
        const index = campus.network.edges.indexOf(edge);
        assert.equal(router.sunlight(840)[index], 0);
      }
    }
  },
);
