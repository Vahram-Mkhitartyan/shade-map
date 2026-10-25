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
- Relation inner rings remain courtyards. Ground-level parts replace only their
  unambiguous parent volume. Elevated parts preserve lower parent volume; orphan
  and ambiguous parts never cut unrelated buildings.
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

## ASU facility-height enrichment

The owner supplied https://www.asu.edu/about/map. Its embedded Experience Builder
map references the public University Facility polygon layer:

https://gisprodportal.asu.edu/server/rest/services/University_Facilities/FeatureServer/1

Source credit: ASU University Facility Records Management Group (UFRM). This is
separate from the ODbL-licensed OSM layer. The public ArcGIS item provides no
explicit reuse-license text; public availability is not treated as an ODbL grant
for ASU data. The current use is a local research prototype; resolve reuse terms
before distributing ASU-derived data with a published product.

The layer identifies rooflines and exposes `BLDG_HEIGHT_FT`. In the queried
context there are 254 facilities, 210 with positive heights. Their ExtractDateTime
is October 19, 2026 at 22:28 UTC; that is a database export timestamp, not proof
that every height was recently measured.

Match heights to existing OSM polygons using >=60% OSM footprint overlap and
intersection-over-union >=20%. Reject ambiguous candidates when the runner-up
has at least 80% of the best coverage. Preserve all OSM building-part heights unchanged.
Do not relocate footprints or assign height by nearest name/centroid alone.
The importer matched 199 polygons in the context extract, 198 in the visible
window. One facility can
correspond to multiple OSM polygons, so these are not unique facility counts.
ASU matches receive separate provenance and per-record source references.

Use `.venv/bin/python scripts/fetch_asu.py` before building from a fresh cache.
`build_campus.py` requires both the OSM and ASU caches. The map inspector exposes
source and units, and the legend groups ASU and OSM tagged heights as recorded
heights. Neither is claimed to be independently field-verified.

## Custom endpoints and offline field export

The graph is exported with 133 five-minute sunlight states from 08:00 through
19:00. Each edge fraction aggregates <=3 m spatial samples in Python and is stored
as an unsigned byte (nearest 1/255). Browser graph search uses these precomputed
fields; no polygon geometry engine or network request is needed. Custom exposure
uses each edge's midpoint arrival time with nearest five-minute solar state, so
it differs slightly from preset per-sample arrival scoring. Walks are capped at
two hours; departures remain 08:00–17:00.

Arbitrary pin positions snap to the nearest connected node within 100 m. Show
requested and snapped positions separately. Dotted connectors are not verified
walkable and are excluded from distance/time/exposure. Unsupported pins retain
their placement and show an error rather than an invented route. Same-node trips
return zero travel duration. Pan/zoom and pin dragging stop at the visible bounds;
outer-context buildings are clipped from display but still contribute shadows.

Height enrichment is paused by the owner. Current source estimates remain as
documented; this refactor does not introduce Overture or other new height data.

After an interface-only edit, run `python scripts/build_campus.py --render-only`
to repackage `.cache/campus-payload.json` without recalculating shadows. A full
build is required after geometry, ownership, routing-model or solar changes.
