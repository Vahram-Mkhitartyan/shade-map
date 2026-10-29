# Live routing model

## Goal

Keep the route aligned with where the walker actually is and when they actually
reach each place. A twenty-minute trip is a moving solar problem: shade, building
access and street conditions can change after the first calculation.

## Three clocks

1. **Predicted time** travels through candidate edges during search.
2. **Observed time** comes from the navigation session and moves forward when GPS
   updates arrive or the walker reports a stop.
3. **Condition time** defines when an observation applies and when it expires.

Every edge uses its predicted midpoint time to select a solar field. Indoor opening
hours must cover the complete predicted traversal. A new observed position or delay
starts another search over the remaining trip.

## Search state

The browser router keeps a best label for each `(node, arrival bucket)`, using
30-second buckets. This preserves futures that reach the same intersection at
meaningfully different times. The priority cost is:

`travel seconds + shade preference × sunny seconds + discomfort penalty`

Delay changes both arrival and duration. Discomfort is seconds-equivalent only for
comparison and never appears as fake walking time. Temporary closures remove an
edge while active. The search is bounded by the two-hour offline trip limit and the
available solar frames.

The map's shadow picture follows the observed clock continuously by blending the
neighboring Python-generated polygon frames. The blend removes abrupt half-hour
swaps but does not claim an exact intermediate shadow boundary. Route exposure
still uses the five-minute edge field, so smoother display is not presented as
finer scoring. The active route also keeps a muted traveled trace and smoothly
retracts the green remainder instead of removing completed graph segments at
replans.

## Event vocabulary

| Event                 | Routing effect                         | Example         |
| --------------------- | -------------------------------------- | --------------- |
| `delay` at the walker | Advance observed clock, then replan    | Stopped to talk |
| edge `delay`          | Add traversal seconds while active     | Red light cycle |
| `blocked`             | Exclude an edge while active           | Closed sidewalk |
| `discomfort`          | Add preference cost, preserve duration | Sewer smell     |

Edge observations carry a start, optional expiry, reason and eventually provenance,
confidence and audience. A phone client should convert raw sensor/community reports
into this small vocabulary before routing.

## Simulator and route stability

`LiveWalkSimulator` advances a visible virtual walker and the observed clock in
deterministic ten-second steps. The offline UI runs those steps at 20× wall-clock
speed and can inject all four event types above. It uses the same
`LiveRouteSession` and time-expanded search intended for later phone observations.

The session compares a newly preferred route with the valid remainder of the
current route from the same snapped node and observed time. In shade mode the
comparison cost is travel seconds plus three times sunny seconds. It keeps the
current route unless the alternative improves this cost by at least 20 seconds.
A blocked, closed or otherwise invalid current remainder switches immediately.
The decision and estimated gain are exposed to the UI. This is an initial
commitment rule; GPS confidence and natural turning points remain future work.

## Next layers

1. Add variable walking speed and recorded/replayable scenario fixtures to the
   deterministic simulator.
2. Extend route commitment with location confidence and useful decision points.
3. Model uncertainty with speed ranges and probable signal waits. Compare routes
   across early/on-time/late arrival scenarios rather than one exact future.
4. Connect real phone location and clock, then add feeds or community observations.
5. Store privacy-safe observations with confidence decay and expiry. Smell and other
   subjective conditions should be personalizable and easy to ignore.

The live-session API is deliberately independent of GPS, databases and UI so those
layers can change without replacing pathfinding again.
