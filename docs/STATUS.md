# Project status

## Current deliverable

`demo/campus.html` is a self-contained real-area map for ASU Tempe, downtown and
neighboring blocks. It works offline. `demo/index.html` preserves the synthetic
first demo. The eventual app targets both iPhone and Android.

## Implemented

- Timezone-aware pvlib solar state and metric rectangular ray fixtures.
- Polygon-prism shadows with concave footprints, holes and elevated bases.
- WGS84-to-UTM 12N projection with an explicit local origin and solar-vector
  rotation from true north into map-grid north.
- Cached OpenStreetMap building ways/relations, building parts, height provenance,
  and a graph connected through shared pedestrian nodes.
- Three example walks, including Memorial Union to Brickyard/Mill Avenue.
- Shortest-distance baseline and shade-weighted candidates, followed by
  arrival-time exposure evaluation with a 35% distance allowance.
- Time controls, pan/zoom, whole-area view, building inspection, and a display
  toggle for estimated-height shadows.

## Data coverage

Map window: longitude -111.945 to -111.914; latitude 33.409 to 33.439.
This is a neighborhood window, not the university boundary. Building downloads
extend farther in all directions to include off-map shadow casters.

- 12,479 building polygons/parts in the computational extract after processing.
- 2,582 building polygons in the displayed window.
- Visible heights: 42 tagged, 181 estimated from levels, 2,359 assumed at 9 m.
- 10,480 connected pedestrian nodes and 11,300 links used by the prototype.
- OSM snapshot: 2026-10-21 03:46:05 UTC (October 20 in Phoenix).

These are dataset counts, not a claim of complete real-world coverage. Most
shadow predictions depend on unverified height assumptions.

## Validation

46 Python tests passed, including polygon concavity/courtyards, analytical shadow
length, elevated buildings, projection scale/grid rotation, height units/access
filters, and arrival-time exposure. Ruff lint/format checks passed.

Headless Chrome verified offline loading, real building footprints, changing
shadows, the off-campus walk, fastest selection, zoom, estimate-display controls,
and a 390 px mobile layout without overflow, JavaScript errors or network requests.
Desktop/mobile screenshots were visually inspected.

Environment note: Python 3.9.6 uses LibreSSL and pvlib import emits an urllib3
compatibility warning. Core tests and builds pass; prefer a modern OpenSSL-backed
Python for ongoing development.

## Limits and next work

- Heights need enrichment/validation; use Overture or local lidar/GIS next.
- No trees, terrain, weather, UV, or field-verified shadows.
- Paths are mapped links, not verified entrances or safe turn-by-turn directions.
  Crossing controls, barriers, accessibility and temporary access are not validated.
- Candidate search uses departure-time midpoint edge costs; final scoring uses
  3 m samples and arrival times with solar state rounded to 5 minutes (±2.5 min).
  It is not globally optimal time-dependent routing.
- Fixed study date October 20, 2026; half-hour departures from 08:00 through 17:00.
- No live GPS, API service, arbitrary destination search, route commitment or
  native app package yet. The standalone file is a prototype for the app.

See CAMPUS_DATA.md for sources, bounds, refresh steps and data conventions.
