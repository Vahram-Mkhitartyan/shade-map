# Roadmap

Each milestone needs a reproducible demo, behavioral tests, and an updated status.

| Milestone | Deliverable | Exit evidence |
| --- | --- | --- |
| 0.0.1 | Solar model + rectangular obstacle queries | Unit directions, analytical ray fixtures, aware-time validation |
| 0.0.2 | Arbitrary footprint + height | Convex/concave polygons, holes, boundary and height tests |
| 0.0.3 | Real nearby buildings + projection/cache | Small campus fixture, source/license/provenance, coordinate checks |
| 0.0.4 | Local shadow field | GeoJSON and analytical/visual comparisons |
| 0.0.5 | Pedestrian network | Valid connected walking routes and baseline distance |
| 0.0.6 | Shade-aware route comparison | Explicit exposure units and detour constraint |
| 0.0.7 | Arrival-time exposure | Cases where departure-only evaluation gives a different result |
| 0.0.8 | Timing uncertainty | Early/late scenarios and robust route comparisons |
| 0.0.9 | Route commitment | GPS noise, delay, deviation, threshold and switching tests |
| 0.1 | Phone prototype | End-to-end campus walk with documented data limitations |

Next: validate 0.0.1, then design polygon-prism queries before adding real data.
