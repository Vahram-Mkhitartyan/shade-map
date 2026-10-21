# Architecture

## Pipeline

Location + destination + aware departure timestamp → local pedestrian graph and
building geometry → solar state → shade queries → traversal exposure → candidate
routes → stability policy → GeoJSON and metrics for a 2D map.

## Boundaries

| Module | Responsibility | Current state |
| --- | --- | --- |
| `solar` | Aware time and geographic position to solar angles/direction | Implemented |
| `geometry` | Local metric obstacles and ray intersection | Box fixtures and polygon-prism ground shadows |
| data | Geographic queries, projection, provenance, caching | Cached OSM prototype |
| exposure | Sample paths at their traversal timestamps | Implemented; campus solar bins 5 min |
| routing | Baseline and shade-aware candidates | Bounded candidate prototype |
| navigation | Deviation, route commitment, reroute thresholds | Planned |
| API/UI | Deliver geometry and metrics to a lightweight map | Offline file; API planned |

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

## Real-area projection

The campus adapter uses origin-shifted UTM 12N metres rather than exact local ENU.
It rotates true East/North solar directions into the grid axes before projecting
shadows. Latitude/longitude never enter the polygon engine. See CAMPUS_DATA.md
for the bounds, source attribution, scale approximation, and data-edge limits.
