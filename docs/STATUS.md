# Project status

## Current deliverable

`demo/campus.html` is the offline real-area map for ASU Tempe and neighboring
blocks. It includes presets plus custom start/finish pins. `demo/index.html`
retains the earlier synthetic demo. Eventual platforms: iPhone and Android.

## Implemented in this pass

- Extracted cached shadow computation to `src/shadeapp/shadow_field.py` and
  candidate search/exposure evaluation to `src/shadeapp/routing.py`.
- Removed global building-part subtraction. Track parent ownership, retain
  elevated lower volumes, and flag ambiguous/orphan parts without cutting others.
- Preserve part heights when applying facility-level ASU records.
- Add **Place me / Place finish**, map taps and pin dragging. Custom graph routes
  work offline using Python-generated five-minute edge sunlight fields.
- Explicit 100 m snap bound, unverified connector offsets, same-point trips,
  unsupported/disconnected endpoint errors, and a two-hour walk limit.
- Clamp zoom and drag to the loaded map rectangle and clip outside geometry.
- Add a visible live-walk simulator with accelerated clock, pause/resume,
  conversation, red-light, temporary blockage and discomfort controls.
- Keep one stable route path during a walk, smoothly retract its green remainder,
  and preserve completed distance as a muted trail.
- Blend neighboring Python-generated shadow frames from the observed minute so the
  display no longer snaps every half hour. Intermediate blends are visual, while
  five-minute route exposure fields remain unchanged.
- Retain a valid current route unless a new alternative improves weighted cost by
  at least 20 seconds; switch immediately when the current remainder is invalid.
- Rewrote roadmap/decisions to separate current behavior, planned work, and old
  synthetic-demo settings.

## Existing sources and coverage

Broad height enrichment is **paused at the owner's request**. The only later
exception is a direct owner observation for The Crêpe Club: approximately 3 m,
recorded as a low-confidence visual estimate. Current ASU records, OSM tags,
levels and fallback assumptions otherwise remain.

- Visible neighborhood: lon -111.945 to -111.914, lat 33.409 to 33.439.
- Context: 12,479 polygons/parts; 2,582 polygons visible.
- Visible heights: 198 ASU records, one owner estimate, 37 OSM tags, 117 levels
  estimates and 2,229 fallbacks.
- Walking network: 10,511 connected nodes and 11,339 undirected links.
- Custom edge fields: 133 five-minute states, 08:00–19:00 on October 20, 2026.
- Visible parts: 3 with containment owners, 11 orphans retained without cuts.
- OSM snapshot: 2026-10-21 03:46:05 UTC (October 20 in Phoenix).

## Verification

- 72 Python tests pass, including ownership, elevated/ground part preservation,
  ambiguity, graph detours, sampling, arrival time, cache separation and prior
  solar/geometry/source checks. Ruff lint and formatting pass.
- Twenty-one Node tests pass (including the DOM integration test), including actual exported-network custom trips, distant and
  disconnected endpoints, zero trips, arrival-time fields and extreme viewport
  positions/zoom levels, route stability and simulated progress.
- A DOM-only integration check passes: initialization, custom start/finish taps,
  pin dragging, simulator start/pause/event controls, route recomputation, time
  changes, fastest selection, and pan/zoom limits, without script errors. This does
  not validate browser painting or touch.
- Final embedded JavaScript syntax and payload dimensions checked.

The browser URL policy blocks automatic access to this local file. No workaround
was attempted; browser visual/mobile revalidation of these new controls remains
for the owner. Earlier browser checks apply to the previous map UI only.

## Limits / next

Custom routes use aggregated edge sunlight at midpoint arrival (not exact continuous
integration). Candidate search is bounded, not globally optimal. Snapped connectors,
entrances, crossings, barriers, stairs, temporary access and accessibility are not
field-verified. No live GPS, timing uncertainty, GPS-aware decision-point policy,
arbitrary date service, terrain, trees, weather or native app package yet.

Python 3.9.6 emits an existing urllib3/LibreSSL warning on pvlib import; tests/builds
pass. Prefer a current OpenSSL-backed Python for future development.

See ROADMAP.md, DECISIONS.md and CAMPUS_DATA.md for current scope and source rules.

## Indoor passage research — October 21, 2026

Saved four official ASU wayfinding PDFs and 216 public accessible-entrance records
in the ignored research cache. Hayden Level One and Memorial Union are first
candidates; Noble has a plan but no second public through-entrance established.
The source inventory identifies 53 additional building codes with multiple
accessible entrance records, without claiming corridor plans or route permission.
All candidates remain disabled pending tracing, door access, schedules and floor
registration. No routing code or existing app output changed in this research
step. See INDOOR_SHORTCUTS.md for sources and the validation walk.

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

Final walkway verification: 66 Python tests and eight JavaScript/DOM tests pass,
including an actual exported-network route along the confirmed covered segment.

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

Current verification: 72 Python tests and 21 JavaScript/DOM tests pass,
including real exported indoor routes, indoor cover, schedule boundaries,
arrival-time closure exclusion, doorway delay, outdoor fallback and simulator
completion across scheduled replans. All three exported campus journeys finish
in both routing preferences without nearest-path oscillation. Ruff and formatting
checks pass. Browser painting remains unverified under the existing local-file
URL policy restriction.

## Live routing core — October 24, 2026

Custom route search now evaluates each edge at its predicted traversal time. A
bounded time-expanded search retains distinct 30-second arrival windows at the
same node instead of collapsing all futures into one label. `LiveRouteSession`
accepts observed position/time updates, unplanned stops and expiring edge events,
then recalculates the remaining route. Supported event effects are added delay,
temporary closure and discomfort cost. Route duration remains separate from
preference cost.

This replaces the custom router's departure-state edge pricing. Preset Python
routes still use the earlier bounded candidate generator followed by arrival-time
scoring. Live GPS, speed estimation, automatic red-light sensing, observation
storage/sharing and confidence decay are not implemented.

## Live simulator and route stability — October 29, 2026

The offline campus app now plays a virtual walk at 20× real time. The orange
walker advances along the selected route while observed time changes. Controls
inject a two-minute conversation, 45-second red-light edge delay, three-minute
temporary blockage or discomfort penalty. All events re-use `LiveRouteSession`;
there is no separate demonstration router.

The session compares the valid current remainder with the new preferred route.
It keeps the current route when weighted improvement is under 20 seconds and
switches immediately if the current path becomes invalid. Shade-mode comparison
uses duration plus three times sunny seconds; displayed duration remains physical
travel time. Twenty-one JavaScript/DOM tests pass. Browser paint, animation timing,
touch behavior and real GPS remain unverified.

## Durham Hall indoor routing — October 29, 2026

The owner-marked Durham Hall trace connects ASU entrance record 203 on the east
side to accessible entrance record 226 on the west side. It is enabled as a
bidirectional indoor corridor with the existing estimated ten-second doorway
delay. The route is geographically traced and approximate rather than registered
from a floor plan.

The owner reports that both entrances are public through 18:00 and require an
ASU ID afterward. The offline UI now has an explicit **I have an ASU ID** option;
the router excludes Durham after 18:00 unless it is selected. The prototype only
claims routing during its 08:00–19:00 solar-data window. Durham's final closing
time and the east entrance's step-free status remain unconfirmed.

## Engineering Center internal covered passage — October 30, 2026

The owner corrected the roof-covered north-south path after seeing the first map
placement, then supplied a closer screenshot for a second correction. The trace
now sits farther east in the narrow space beside Engineering Annex. Its covered
portion begins in the Annex/A-Wing gap, does not cross A-Wing, and ends on the
mapped cross path immediately north of F-Wing. The earlier Palm Walk coverage
has been removed.

OSM does not contain a pedestrian edge inside the south gap. The graph therefore
uses a 57 m unroofed registration tie west through the visible open gap to Palm
Walk. That tie makes the passage routable but receives no roof-cover credit and
still needs an on-site connectivity check.

The covered centerline receives the same zero-direct-sun roof proxy used by the
Creativity Commons colonnade. Roof width, height, support obstructions and
low-angle side sunlight remain unmodeled. The corrected straight trace is still
based on the owner-marked screenshot and needs a field check for metre-level
alignment.
