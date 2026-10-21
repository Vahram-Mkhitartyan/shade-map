# ASU Tempe and surrounding neighborhood data

## Source and attribution

OpenStreetMap via the public Overpass API:

- https://overpass-api.de/api/interpreter
- https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_API_by_Example
- https://www.openstreetmap.org/copyright
- https://opendatacommons.org/licenses/odbl/1-0/
- https://wiki.openstreetmap.org/wiki/Key:height

Map data: © OpenStreetMap contributors, available under ODbL. Attribution and
license links appear in the standalone map. Imported names are treated as text;
embedded JSON escapes markup-sensitive characters. Raw and derived downloaded
map files are ignored by Git, following AGENTS.md.

## Geography and coverage

Bounds are south, west, north, east:

| Purpose | Bounds |
| --- | --- |
| Building context | 33.398, -111.958, 33.449, -111.898 |
| Walking-network download | 33.404, -111.950, 33.443, -111.905 |
| Visible neighborhood | 33.409, -111.945, 33.439, -111.914 |

No ASU administrative polygon clips the data. The visible neighborhood includes
campus, downtown/Mill Avenue, and adjacent blocks. Outer buildings can contribute
shadows even when their footprints are off-screen. Extreme low-angle shadows from
beyond the downloaded band can still be missing; the UI states this limitation.

Projection: WGS84 longitude/latitude → EPSG:32612 (UTM zone 12N), subtracting the
projected origin at 33.4242 N, -111.9281 E. Local metric axes follow UTM grid east
and north. True-north solar vectors are rotated using the projected meridian at
the origin. This is a small-area, flat-ground approximation; no terrain model is
present and grid convergence/scale vary slightly across the extract.

## Heights and geometry

- Prefer a positive `height` tag; parse metres or explicit feet/inches.
- Otherwise estimate `building:levels × 3 m`.
- Otherwise use an explicitly marked 9 m assumption, including unknown heights.
- `min_height` creates an elevated base; underground levels are not added.
- Relation inner rings remain courtyards; building parts replace overlapping
  parent volume, with uncovered parent area retained.
- Tagged height does not imply measured or field-verified height.
- The map inspector exposes OSM identity, name, height and provenance.
- Hiding estimated shadows affects display only; scores still use the full model.

## Walking network and candidates

Use connected outdoor pedestrian ways and shared OSM node IDs; geometry crossings
without a shared node are not joined. Private/no-access and indoor ways are
excluded. Motor-road centerlines are drawn for context, not converted to invented
sidewalks. Stairs may appear. This conservative graph can omit legitimate links;
barriers, traffic controls and time-dependent access need future validation.

Example endpoints snap to nearby mapped nodes rather than verified entrances.
The UI reports distances from building centers; those connectors are not included
in the route metrics. Reject an endpoint more than 150 m from the chosen node.

For each departure, generate a shortest path and departure-time shade-weighted
alternatives. Reject alternatives over 35% longer. Evaluate retained candidates
at arrival time along the walk, then choose least sunny seconds (or shortest time).
Candidates are not exhaustive; do not claim global time-dependent optimality.

Study date: October 20, 2026 in America/Phoenix. Walking speed: 1.4 m/s. Final route
samples: at most 3 m. Solar states: nearest 5-minute bin (up to 2.5 minutes of error).
Departure choices: every 30 minutes from 08:00 to 17:00. Display shadows correspond
to departure, while route scores advance along the predicted walk.

## Refresh and rebuild

From the repository, after installing `.[dev]`:

```sh
.venv/bin/python scripts/fetch_campus.py
.venv/bin/python scripts/build_campus.py
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
```

The fetch requires internet access; avoid repeated requests when the cache is
sufficient. The build uses `.cache/campus-osm.json` and creates `demo/campus.html`.
Build runtime and file size increase with footprint complexity. Only the finished
HTML is needed to view the map, and it makes no network requests.
