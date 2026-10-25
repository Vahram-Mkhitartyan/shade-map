# shade app

Shade-aware pedestrian routing, starting with ASU's Tempe campus.

Predict building shade at the time a walker reaches each part of a route, then
balance sunlight exposure against walking time and route stability. A lightweight
2D map will display the result; geometry calculations belong on the backend.

## Open the map prototype

Double-click **`demo/campus.html`** for the real ASU/Tempe neighborhood map.
The original synthetic study remains in `demo/index.html`. It works offline without a server.
Move the departure-time slider and compare Fastest and More shade. Choose
**Place me / Place finish** and tap the map, or drag either pin, to calculate a
custom walk. Pins snap to connected mapped paths within 100 m; displayed dotted
connectors are unverified and excluded from totals. Pan and zoom stay within the
loaded building area.
Owner-confirmed MU and Hayden indoor passages are included, with reported
opening hours and estimated doorway delays. Brown lines mark approximate corridors;
route cards identify indoor shortcuts.
The campus file uses OpenStreetMap footprints and paths, with height estimates
clearly marked, enriched with ASU facility height records. See [campus data notes](docs/CAMPUS_DATA.md) for coverage and refresh
steps. Rebuild with `.venv/bin/python scripts/build_campus.py`.

## Start here

- [Product brief](docs/PRODUCT.md): purpose, pilot, scope, and success criteria.
- [Architecture](docs/ARCHITECTURE.md): module boundaries and physical conventions.
- [Decisions](docs/DECISIONS.md): accepted choices and unresolved questions.
- [Roadmap](docs/ROADMAP.md): small, verifiable milestones.
- [Status](docs/STATUS.md): what works and what comes next.
- [Campus data](docs/CAMPUS_DATA.md): sources, bounds, assumptions, and rebuilding.
- [Live routing](docs/LIVE_ROUTING.md): observed time, events, replanning, and next layers.
- [Agent instructions](AGENTS.md): rules for changing this repository.

## Run the first milestone

Python 3.9 or newer:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m ruff format --check .
python -m ruff check .
python -m pytest
python demo.py
```

For JavaScript regression tests (Node 20+), install test dependencies with
`npm install`, then run `npm test`. Build the campus file first to include the
real-data and DOM integration checks; those checks skip without the artifact.

Current scope: real-area footprints and a pedestrian graph, flat-ground building
shadows, arrival-time scoring of a bounded set of route candidates, and an offline
map. Height data is mostly estimated. This is not live or verified navigation.
Predicted building shade is not a measurement of thermal comfort or UV exposure.
