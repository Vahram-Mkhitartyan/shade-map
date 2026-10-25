# Decision log

These are current decisions. Historical prototype settings below are explicitly
superseded rather than remaining in the open-decision list.

## Product and scope

- Product: **shade app**; repository `shade-map`, Python package `shadeapp`.
- Built from scratch, with ASU Tempe and adjacent neighborhoods as the pilot.
- No campus administrative polygon clips buildings or routes. An outer building
  band supplies potential off-map shadow casters; finite coverage is disclosed.
- Eventual platforms: **both iPhone and Android**. Native/shared framework, hosting,
  and app distribution remain open.
- No Unity or continuously rendered 3D city. Use vertical geometric prisms with
  a lightweight 2D frontend.

## Data and coordinate contracts

- Cached OSM footprints/parts and mapped pedestrian links, with ODbL attribution.
- ASU facility heights use feet-to-metres conversion and conservative spatial
  matching; provenance stays attached. Public ASU availability is not assumed to
  grant ODbL redistribution rights; see CAMPUS_DATA.md.
- Unknown heights retain their disclosed assumptions. **Further height enrichment
  is paused by the owner**; no new source is applied in this refactor.
- WGS84 lon/lat is projected to origin-shifted UTM 12N metres. Rotate true-north
  solar directions into grid axes. The scene uses flat ground.
- Require aware times. Use pvlib's geometric elevation and observer-to-Sun vectors.

## Ownership correction

A scene-wide union of all parts previously cut every overlapping building. That
behavior is removed. Explicit OSM building-relation membership identifies an owner
when available; otherwise require one parent covering >=99% of a part. Ambiguous
and orphan parts do not cut outlines. Subtract a ground-level part only from its
owner. Preserve the parent's lower volume under elevated parts. Facility-wide
height enrichment must not overwrite part-level vertical structure.

## Module boundaries

- `geodata.py`: projection, OSM ingestion, ownership and walking graph.
- `asu_heights.py`: ASU matching and source references.
- `shadow_field.py`: cached solar states, projected shadows, point queries.
- `routing.py`: sampling, candidate search, arrival-time scoring, edge fields.
- `build_campus.py`: assemble data, invoke modules, package the offline artifact.
- `demo/offline-routing.js`: offline graph search over Python-computed fields.
- `demo/map-viewport.js`: pure viewport constraints, independently tested.

Static geometry and dynamic Sun remain separate. No polygon shadow engine runs
in the frontend. The browser does perform graph search for arbitrary offline pins.

## Current offline routing approximation

- Study date: October 20, 2026, America/Phoenix; departures 08:00–17:00 every 30 min.
- Speed: 1.4 m/s. Candidate alternatives must be <=35% longer than shortest.
- Candidate generation uses departure-time exposure costs; arrival-time scoring
  compares those candidates. This is **not** globally optimal time-dependent A*.
- Preset scores use 3 m trajectory samples with five-minute solar bins.
- Custom routes use edge sunlight fractions from 3 m spatial samples, evaluated
  at edge midpoint arrival, with five-minute bins. Fractions use 8-bit storage
  (nearest 1/255). Fields extend to 19:00; custom walks are capped at two hours.
- Pins may be placed throughout the loaded area. Route to the nearest connected
  node within 100 m; show the offset and an unverified dotted connector. Connector
  distance/exposure is excluded. Reject unsupported pins rather than invent links.
- Same-node routes return zero travel duration safely.
- Clamp viewport pan/zoom and pin placement to the loaded building-area rectangle;
  clip context geometry outside it. Whole-area fit can have neutral letterboxing.

## Superseded prototype settings

The synthetic demo (`demo/index.html`) used June 21, fixed paths, 2 m samples,
15-minute departures, and a 60% detour allowance. These apply only to that retained
synthetic artifact. The real-neighborhood artifact uses the settings above.

Shapely, UTM 12N, actual data sources, and the pilot bounds are chosen; they are no
longer open architectural questions.

## Still open

App framework, live service/API, mapping platform for production, deployment,
arbitrary-date performance, field accuracy, uncertainty model, and reroute policy.

## Indoor shortcuts — October 21, 2026

Investigate publicly traversable corridors as additional time-dependent graph
edges, beginning with Hayden Level One and Memorial Union. Plans and entrance
points are evidence to investigate, not an automatic routing permission. Require
floor registration, traced corridors, bidirectional door checks, user access and
schedules before enabling a passage; retain an outdoor fallback. Never connect
all exterior doors by straight lines or merge Hayden's concourse into Level One.
Time savings must include doorway and vertical-transition costs. Height enrichment
remains paused and is unrelated to this indoor-passage research.

## Creativity Commons connection enabled — October 21, 2026

The owner confirms both ends of the marked covered segment connect to Palm Walk.
Routing now splits the named Palm Walk edges at projected endpoint ties (maximum
15 m), retaining existing connectivity. The full-length marked segment is
routable; short exterior ties receive no roof-cover credit. Geometry is still
approximate, based on the owner screenshot and building facade.

The roof-covered centerline uses an explicit MVP shade proxy, not measured roof
geometry: it receives zero direct-sun cost under the cover assumption. Low-angle
sun entering the open sides, exact roof width/height, and column obstructions
are not modeled. This does not guarantee full shade or accessibility.

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

## Live routing state — October 24, 2026

Use a bounded time-expanded graph state `(node, 30-second arrival bucket)` for
custom route search. Price sunlight at the predicted midpoint of each edge. Keep
the live navigation session separate from search: observed position/time and
events cause recalculation but do not become global graph state.

Normalize near-term human and urban observations into three edge effects:
temporary delay, temporary block and seconds-equivalent discomfort. A stop such
as a conversation advances the walker's observed clock rather than modifying an
unrelated edge. Discomfort affects preference only; reported duration remains
physical traversal time. Conditions support expiry from the start so stale reports
do not become permanent map truth.

This is deliberately an event vocabulary rather than separate pathfinding code for
red lights, odors, crowds and future observations. GPS integration, confidence,
community aggregation, uncertainty and switching hysteresis remain separate layers.
