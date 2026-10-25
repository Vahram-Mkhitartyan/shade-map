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

## Event vocabulary

| Event | Routing effect | Example |
| --- | --- | --- |
| `delay` at the walker | Advance observed clock, then replan | Stopped to talk |
| edge `delay` | Add traversal seconds while active | Red light cycle |
| `blocked` | Exclude an edge while active | Closed sidewalk |
| `discomfort` | Add preference cost, preserve duration | Sewer smell |

Edge observations carry a start, optional expiry, reason and eventually provenance,
confidence and audience. A phone client should convert raw sensor/community reports
into this small vocabulary before routing.

## Next layers

1. Add a deterministic walk simulator that emits position updates, variable speed,
   stops and condition events against recorded scenarios.
2. Add route commitment: change routes only at useful decision points and when the
   benefit clears a threshold. This prevents GPS noise and tiny shade differences
   from producing constant turns.
3. Model uncertainty with speed ranges and probable signal waits. Compare routes
   across early/on-time/late arrival scenarios rather than one exact future.
4. Connect real phone location and clock, then add feeds or community observations.
5. Store privacy-safe observations with confidence decay and expiry. Smell and other
   subjective conditions should be personalizable and easy to ignore.

The live-session API is deliberately independent of GPS, databases and UI so those
layers can change without replacing pathfinding again.
