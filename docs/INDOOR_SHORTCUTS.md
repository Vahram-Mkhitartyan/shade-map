# ASU indoor-shortcut source survey

Reviewed October 28, 2026. Public sources only. This packet identifies potential
passages; it does not enable any indoor route in shade app or claim time savings.

## Best starting candidates

| Priority | Building / level           | Evidence                                                                                                           | What remains                                                                                                           |
| -------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| 1        | Hayden Library, Level One  | Official plan labels entrances at Cady Mall and Orange Mall. Public GIS has west- and south-side entrance records. | Trace a lobby route avoiding collection/office rooms; verify both doors and common opening times.                      |
| 2        | Memorial Union, Main Level | Public 2025 four-floor map; GIS identifies north, southwest and southeast accessible entrances.                    | Trace north-to-southwest and north-to-southeast public corridors; check ramp/stair alternatives and door availability. |
| Excluded | Noble Library, Level One   | Owner reports no accessible second entrance.                                                                       | Exclude accessible through-building shortcuts; not a claim that no other doors exist.                                  |
| Hold     | Student Pavilion           | Public hours and one accessible entrance record.                                                                   | No suitable floor plan or second public entrance established in this survey.                                           |

These priorities are research judgments, not ASU endorsements. Multiple doorway
symbols or entrance points do not prove permission or a continuous public passage.
An exit-only door cannot automatically be used as a bidirectional entrance.

## Source files

- [Memorial Union map](https://eoss.asu.edu/sites/g/files/litvpz141/files/2025-08/MU-Map-24x36-071425.pdf), page 1 = Main Level;
  four pages total. The filename identifies July 14, 2025; that is not proof of
  current door operation. [Official PDF](https://eoss.asu.edu/sites/g/files/litvpz141/files/2025-08/MU-Map-24x36-071425.pdf).
- [Hayden Level One](https://lib.asu.edu/sites/g/files/litvpz3326/files/docs/hayden_floorplan_level1.pdf), one page, revision 08/05/26.
  [Official PDF](https://lib.asu.edu/sites/g/files/litvpz3326/files/docs/hayden_floorplan_level1.pdf).
- [Hayden Concourse](https://lib.asu.edu/sites/g/files/litvpz3326/files/docs/hayden_floorplan_concourse.pdf), one page, revision 08/05/26.
  [Official PDF](https://lib.asu.edu/sites/g/files/litvpz3326/files/docs/hayden_floorplan_concourse.pdf).
- [Noble Level One](https://lib.asu.edu/sites/g/files/litvpz3326/files/docs/noble_floorplan_1st.pdf), one page, revision 08/14/25.
  [Official PDF](https://lib.asu.edu/sites/g/files/litvpz3326/files/docs/noble_floorplan_1st.pdf).

All four relevant first pages were rendered and visually inspected. Plans are
published wayfinding diagrams, not guaranteed metric/as-built surveys. Downloaded
files are unmodified; inventory.json records source URLs and SHA-256 hashes.
Source attribution: Arizona State University / ASU Library / ASU Educational
Outreach and Student Services. Public access is not a blanket redistribution
license; establish applicable reuse terms before embedding plan artwork in a
published app. A graph derived from verified public corridors need not distribute
full building-plan artwork.

## Entrance geometry

[Accessible-entrance GeoJSON](https://gisprodportal.asu.edu/server/rest/services/CampusLayers/Accessible_Entrances/FeatureServer/0) contains 216 public
ASU entrance records inside the current map window. Coordinates are WGS84
longitude/latitude, not local metres. Endpoint:

https://gisprodportal.asu.edu/server/rest/services/CampusLayers/Accessible_Entrances/FeatureServer/0

| Building                | Record IDs    | Source descriptions                                                  |
| ----------------------- | ------------- | -------------------------------------------------------------------- |
| Hayden (LIB)            | 222, 224      | West side; south side (Level One candidates)                         |
| Hayden (LIB)            | 223           | West-side elevator access to concourse; keep separate from Level One |
| Memorial Union (MU)     | 247, 248, 249 | Southeast corner; southwest corner; north side                       |
| Noble (NOBLE)           | 275           | Main entrance; ramp noted west of stairs                             |
| Student Pavilion (STPV) | 345           | Southwest corner                                                     |

The layer contains accessibility-related attributes such as button, width32,
mainentrance and accessibleentrance. These describe source records, not a fresh
accessibility inspection or guarantee that the door is open. It is an accessible
entrance inventory, not a complete inventory of all doors or emergency exits.

The inventory also lists 53 other building codes with multiple mapped accessible
entrances. Wexler (5), Nelson Fine Arts Center (4), Armstrong (4), Student Services
(4), and Business Administration (3) are follow-up leads. More doors do not imply
a better shortcut.

## Campus-wide public plan sweep — October 28, 2026

ASURITE authentication succeeded for the ASU Virtual Print Vault, but the account
does not have the separate facilities permission required to open drawings. The
vault returned `NoPermission`. Do not bypass that boundary. ASU's official campus
and building information page says students and non-consultants should use the
plans-request form with a sponsoring faculty or staff member; vault accessibility
permission is handled separately by University Facilities Records Management.

The public-source sweep produced three new results:

| Building               | Public evidence                                                                                                                                         | Routing decision                                                                                                 |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Music Building         | The official School of Music FAQ links a public MappedIn interactive building map. Owner inspected it on October 28 and found only one usable entrance. | Exclude from through-building routing. Two GIS entrance records do not establish two usable public doors.        |
| Desert Financial Arena | An official 2022 facility map shows the circular concourse and north, east, south and west exits.                                                       | Treat as a partial venue plan. Keep disabled because event access and ongoing renovation can change circulation. |
| Payne Hall             | A current official 12-page emergency plan references floor plans but does not include them. Visual review found only an exterior assembly-area map.     | The document cannot support an indoor corridor trace. Request the ground-floor sheet or collect an owner trace.  |

Sources:

- [ASU campus and building information](https://cfo.asu.edu/campus-bldg-information)
- [Official Music Building map link](https://musicdancetheatre.asu.edu/admission/frequently-asked-questions)
- [Desert Financial Arena facility map](https://graduation.asu.edu/sites/g/files/litvpz3431/files/2022_desert_financial_arena_map_updated_04.19.221.pdf)
- [Payne Hall emergency and evacuation plan](https://employee.cisa.asu.edu/sites/g/files/litvpz1091/files/2025-10/Payne_Hall_Emergency_and_Evacuation_Plan_2024%20-%20Updated.pdf)

Official ASU searches also surfaced site, parking, gate, virtual-tour and building
history pages. These locate buildings but do not expose traceable indoor corridors.
The remaining candidates therefore stay disabled and retain
`not_established_in_this_research` until a public plan, approved vault/requested
drawing, or an owner-verified trace supplies the missing geometry.

## Hours and permission evidence

- [Memorial Union](https://eoss.asu.edu/mu) publishes academic-semester hours and
  holiday exceptions. These are building-level hours, not individual-door schedules.
- [Hayden hours](https://lib.asu.edu/hours/hayden) and
  [Noble hours](https://lib.asu.edu/hours/noble) are official schedule entry points.
  Their dynamic schedule tables were not available in the retrieved page text;
  no current weekly times or public-versus-cardholder schedule was extracted.
- [Library visitors](https://lib.asu.edu/services/visitors) directs visitors to
  current library hours; it does not prove every room or exit is publicly usable.
- [Student Pavilion](https://eoss.asu.edu/student-pavilion) publishes building
  hours and holiday/event exceptions; office or reservation hours are distinct.

No source establishes all candidate doors as unlocked for all users. Plans,
public-door access, floor elevation, opening schedules and temporary closures
must remain separate evidence fields. No emails or messages were sent.

## Proposed routing representation

An indoor shortcut should be a small verified graph, not a line joining every
pair of exterior doors:

`outdoor path -> entrance -> public corridor junctions -> exit -> outdoor path`

For each passage, store:

- Building ID, floor ID/elevation, surveyed entrance coordinates and graph ties.
- Corridor polyline and measured distance, source URL, revision and verification.
- Allowed direction, access category (public/cardholder/etc.), open intervals,
  exceptions, and door/transition delays where known.
- Stairs, ramps and elevators as explicit transitions; accessibility verification.
- Covered/indoor status separate from outdoor building shadow and thermal comfort.

Require the passage to remain usable over the predicted traversal interval, not
just at initial departure. Unknown schedules/access keep the passage disabled.
Keep an outdoor fallback. Candidate time gains must subtract doorway, queue and
vertical-transition time; a covered route is not automatically the fastest.

Wayfinding diagrams need registration against real building geometry. Use at
least three non-collinear control points where possible, then validate another
location and the traced corridor length. Do not infer accurate metres from PDF
page size. Hayden's concourse and courtyard/elevator approach cannot be merged
into Level One simply because both have west-side entrance records.

## First validation walk

1. Hayden: Cady Mall entrance -> Level One public lobby -> Orange Mall entrance,
   then reverse. Note access, hours/signage, doors, travel time and any barriers.
2. MU: north entrance -> public circulation -> southwest entrance, then southeast
   entrance as a separate candidate. Verify ramps/stairs and bidirectional doors.
3. Only after those checks, trace/register the corridor polylines, connect them to
   the outdoor graph and compare against the outdoor baseline for actual trips.

A door-status or corridor observation from the owner can complete this missing
field evidence. No need to collect every campus plan manually.

Local source packet and inventory: `.cache/indoor-shortcuts/` (ignored by Git).

## Current owner-reported hours — October 21, 2026

America/Phoenix local time:

- Hayden: 07:00–midnight, ending the service day; applicable days unspecified.
- MU Monday–Friday: 06:30–22:00.
- MU Saturday: 08:00–22:00.
- MU Sunday: 10:00–22:00.

MU's 22:00 closing supersedes the earlier owner-reported 21:30. The inventory
retains source provenance. Do not infer Hayden's weekly applicability or holiday
exceptions. Individual door schedules and corridor continuity remain unverified;
no indoor passage is enabled by this schedule update.

## Owner campus observations — October 21, 2026

Noble and SDFC are excluded from accessible through-building shortcut candidates
per owner reports of no accessible second entrance. Existing outdoor paths and
building approaches are unaffected. Engineering buildings are high-priority
leads, with specific wings/doors/hours still to be identified.

The owner also reports an outdoor shaded path beside Palm Walk beyond the field
in front of SDFC. Treat it as an outdoor lead, not an indoor corridor. The owner confirms the building is Creativity Commons. Exact path geometry
and shade mechanism remain unverified; do not assign all-day shade or a routing
override before identifying the segment.

## Creativity Commons trace confirmed — October 21, 2026

The owner marked only a straight black segment and confirmed it spans the full
Palm Walk-facing (west) side of Creativity Commons. Roof cover and columns along
the path are owner-reported. `data/covered_walkways.geojson` stores an approximate
facade-aligned line; the blue overlay excludes the drawn arrow and green routes.
No unmarked connectors are invented. Existing graph connections and roof dimensions
remain to be verified, so routing and solar scores do not yet use this annotation.

Armstrong Hall is also an owner-reported multi-entry indoor-shortcut candidate;
location may limit its usefulness. No corridor is enabled from this observation.

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

## Durham Hall enabled — October 29, 2026

The owner-marked route connects the mapped east entrance (ASU record 203) to the
west accessible entrance (record 226). Both are reported as public through 18:00;
ASU ID is required afterward. The app exposes that eligibility as an explicit
checkbox and excludes the corridor after the cutoff when it is not selected.

The centerline follows the marked east-to-west bend and is geographically
registered from the two entrance records. It is approximate, bidirectional and
receives indoor cover credit. The current route schedule is limited to the
prototype's 08:00–19:00 solar-data window. Final building closing time and
step-free access at the east door remain unconfirmed.
