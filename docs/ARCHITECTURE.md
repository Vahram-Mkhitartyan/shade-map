# Architecture

## Pipeline

Location + destination + aware departure timestamp → local pedestrian graph and
building geometry → solar state → shade queries → traversal exposure → candidate
routes → stability policy → GeoJSON and metrics for a 2D map.

## Boundaries

| Module     | Responsibility                                                      | Current state                                 |
| ---------- | ------------------------------------------------------------------- | --------------------------------------------- |
| `solar`    | Aware time and geographic position to solar angles/direction        | Implemented                                   |
| `geometry` | Local metric obstacles and ray intersection                         | Box fixtures and polygon-prism ground shadows |
| data       | Geographic queries, projection, provenance, caching                 | Cached OSM prototype                          |
| exposure   | Sample paths at their traversal timestamps                          | Implemented; campus solar bins 5 min          |
| routing    | Baseline and shade-aware candidates                                 | Bounded candidate prototype                   |
| navigation | Observed clock, events, replanning, route commitment and simulation | Interactive prototype                         |
| API/UI     | Deliver geometry and metrics to a lightweight map                   | Offline file; API planned                     |

## Physical contract

Local axes: x east, y north, z up; all distances/heights in metres. Solar azimuth is
clockwise from north; elevation is above the geometric horizon. For azimuth A and
elevation a, the observer-to-Sun unit vector is `(cos(a) sin(A), cos(a) cos(A), sin(a))`.
Ray queries use `P + t S`, t > 0. A positive intersection means blocked sunlight.
Elevation <= 0 means no direct Sun; it does not assert a building is providing shade.
The first API returns a boolean for absence of direct sunlight; richer reasons come later.

Use pvlib's geometric elevation consistently. Refraction and atmospheric intensity
are outside this first milestone. Geographic projection and its valid region must
be explicit when real building data is added.

## Exposure and routing contract (planned)

At distance s on an edge, evaluate time `entry_time + s / walking_speed`.
Store sunny distance (metres), sunny duration (seconds), and exposure fraction as
different quantities. For a time-based score, use travel seconds plus a dimensionless
preference times sunny seconds; do not add an unlabeled fraction directly to seconds.

Arrival time affects future exposure. A single least-cost label per node can discard
a later arrival with a better continuation. Choose and validate a bounded multi-label,
time-expanded, or candidate-route approach before claiming optimal time-dependent A*.
Document discretization error or candidate coverage. Waiting is disallowed unless
explicitly introduced. Nighttime routes have zero direct sunlight exposure.

## Geometry and stability

Cache static building geometry separately from solar state. Polygon prisms precede
real building ingestion. Test concavity, holes, boundaries, and low-elevation rays.
Near-horizon shadows may reach far beyond a route corridor: any data clipping or
shadow range limit must report the resulting uncertainty.

Future navigation compares the current remaining route and alternatives from the
same observed position/time, with switching penalties and natural decision points.
Timing uncertainty and geometry quality remain explicit; predicted precision is not
equivalent to field accuracy.

## Live routing contract

Live routing maintains separate predicted, observed and condition clocks. Search
uses a bounded time-expanded state `(node, arrival bucket)` rather than one label
per node. Each edge is priced at its predicted midpoint time, including static
door delays, reported opening intervals and active live conditions. The current
prototype uses 30-second arrival buckets and five-minute solar fields.

`LiveRouteSession` owns the observed position and time. It replans when the snapped
node changes, at least 30 observed seconds pass, or a delay/condition event arrives.
An unplanned stop advances the observed clock before replanning. Conditions are
edge-scoped and time-bounded: `delay` changes traversal time, `blocked` removes an
edge, and `discomfort` adds a seconds-equivalent preference cost without falsifying
travel time. Outdoor fallback remains available when graph connectivity permits.

`LiveWalkSimulator` advances a virtual position and clock and injects the same event
vocabulary through the live session. The session retains a valid current route when
a new alternative improves weighted cost by less than 20 seconds; invalid current
routes switch immediately. This is a first stability threshold, not GPS-aware
decision-point logic.

The offline renderer caches the two neighboring Python-generated shadow polygon
frames and blends their opacity from the observed minute. This removes half-hour
visual snapping while retaining backend-generated geometry. Intermediate blends
are a display transition, not freshly computed exact shadow boundaries. This layer
does not change routing costs: the exported edge sunlight field remains five-minute,
1/255-quantized data. During simulation, one stable route path uses traveled and
remaining stroke intervals so progress can move continuously without dropping
whole graph segments.

This is the navigation core, not live sensing. The offline artifact has no GPS,
traffic-signal feed, crowdsourcing backend or uncertainty distribution. It also
cannot route beyond the exported date/time solar window.
See `docs/LIVE_ROUTING.md` for the event model and staged path to the phone app.

## Real-area projection

The campus adapter uses origin-shifted UTM 12N metres rather than exact local ENU.
It rotates true East/North solar directions into the grid axes before projecting
shadows. Latitude/longitude never enter the polygon engine. See CAMPUS_DATA.md
for the bounds, source attribution, scale approximation, and data-edge limits.

## Offline custom routing boundary

`shadow_field.py` owns indexed Sun/shadow states. `routing.py` owns trajectory
sampling, detour-bounded candidate generation, and exposure evaluation. The
builder only assembles and serializes those results. Static geometry and source
metadata never become graph-search responsibilities.

To retain a double-clickable file, export the connected graph and five-minute
edge sunlight fractions (3 m spatial samples, 1/255 storage resolution). Browser
Dijkstra creates custom candidates; edge midpoint arrival times select sunlight
bins for scoring. Presets retain per-sample arrival scoring. Neither search
claims global time-dependent optimality. This is a prototype transport format,
not a decision to ship a large precomputed region as the final phone architecture.

`map-viewport.js` clamps all views to loaded bounds. Context geometry is clipped;
custom pins retain their requested positions and expose bounded graph snapping.
The offline file does not infer access paths from a pin to the graph.

## MU and Hayden indoor routing enabled — October 21, 2026

Owner-marked black corridor traces are now enabled: MU Main Level, including
its marked entrance branches; Hayden Level One, Cady Mall west entrance to
Orange Mall south entrance. Owner confirms step-free, bidirectional passage and
all marked doors usable throughout reported hours. Hayden is confirmed daily
07:00–midnight; MU Mon–Fri 06:30–22:00, Sat 08:00–22:00, Sun 10:00–22:00.
This supersedes earlier statements that both candidates remain disabled.
Noble, SDFC and Hayden concourse shortcuts remain excluded.

`data/indoor_passages.json` preserves pixel traces, controls, access evidence and
weekly schedules. `indoor_passages.py` registers coordinates in local metres and
splits nearby exterior edges for each confirmed door; ties crossing the building
interior are rejected. MU uses ASU entrance records 249/248/247 as three controls;
the unmarked southwest doorway is only a registration control, not another added
route. Hayden uses entrance records 222/224 and an approximate OSM northwest
facade control. Doors snap to the mapped facade within a 12 m registration limit;
exterior ties are bounded at 25 m. Geometry and distances are approximate, not
surveyed; floor plans and simplified OSM footprints differ.

Indoor centerlines receive zero direct-sun exposure. Exterior ties are evaluated
separately. Each door crossing adds an explicitly assumed 10 seconds; actual door,
queue and crowd delays are unknown. Route cards label trips via MU or Hayden;
brown lines show available corridor geometry. Full edge traversal must fit within
reported opening hours; custom search checks predicted arrival and exit times,
retaining outdoor alternatives. It still uses bounded candidates with one label
per node, not a globally optimal time-dependent solver. Python presets are for
the existing Tuesday 08:00–17:00 study, entirely within both opening schedules;
no arbitrary-day preset service is claimed. The offline solar date/time window
is unchanged. Holiday/event closures and live door status are unavailable.

Durham adds credential-aware access metadata to the same edge model. Each edge
can carry an `access_after` minute and `required_access` identifier. The offline
router accepts user access eligibility separately from the graph and rejects a
traversal ending after the cutoff when eligibility is absent. This supports a
route becoming unavailable after a live delay without mixing identity state into
static campus geometry.

Covered-walkway observations become explicit centerlines whose endpoints split
the nearest eligible pedestrian edges. A feature can restrict those connections
to named paths either globally or per endpoint. The Creativity Commons trace
uses Palm Walk at both ends; the Engineering Center trace uses the north cross
path and a separate south tie through the Annex/A-Wing gap. Endpoint ties are
bounded and remain unroofed; only the observed centerline receives the roof
proxy.
