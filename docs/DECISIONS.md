# Decision log

## Accepted foundation — 2026-10-20

- Call the product **shade app**, per the owner's correction.
- Build from scratch; the pasted prior proof of concept is background, not inherited code.
- Use Python for the computational core and pvlib for solar position.
- Start with synthetic axis-aligned building boxes and a pure ray-intersection function.
- Keep a lightweight 2D frontend; compute shadows on the backend.
- Use metric East/North/Up geometry and timezone-aware timestamps.
- Begin with ASU Tempe as the pilot specified by the repository; select a corridor later.
- Validate each milestone before adding the next source of complexity.

## Open

- Campus corridor and pedestrian/building data sources, licenses, and height coverage.
- Polygon geometry library and geographic projection.
- UI platform, mapping library, hosting, and API design.
- Arrival-time routing strategy, detour policy, timing uncertainty, reroute thresholds.

Record rationale and consequences when resolving these. Avoid turning placeholders
into implied requirements or reporting candidate-only routing as globally optimal.

## First interactive demo — 2026-10-20

- Eventual app targets both iPhone and Android, per the owner. Framework selection
  remains open; this offline browser file is the first interaction prototype.
- Generate a self-contained HTML file using Python-computed solar/shadow data.
  The frontend renders precomputed polygons and route scores.
- Fixed demo: June 21, 2026, ASU Tempe solar coordinates, synthetic buildings/paths,
  flat ground, 1.4 m/s walking, 2 m midpoint samples, 15-minute departures.
- Solar state is rounded to the nearest minute (at most 30 seconds of timing error).
- Compare only three fixed paths. More shade minimizes sunny seconds with a 60%
  distance allowance, chosen to demonstrate the tradeoff, not a final product policy.
- No API keys, network access, or personal location are needed for this artifact.

## Real neighborhood prototype — 2026-10-20

- Use a geographic neighborhood window plus outer building context, not a campus
  administrative boundary, per the owner's request to include nearby buildings.
- Start with cached OpenStreetMap footprints/parts and pedestrian links, with ODbL
  attribution. Enrich heights later; unknowns remain explicit estimates.
- Use origin-shifted UTM 12N geometry and rotate true-north solar vectors into
  grid axes. Polygon-prism tests precede real polygon shadow calculations.
- Ship three selectable example walks in an offline file. These use actual graph
  edges and sampled arrival-time scores; they are not unrestricted navigation.
- A 35% detour allowance and five-minute solar bins are prototype parameters,
  not final product settings. Document their error and search limitations.
