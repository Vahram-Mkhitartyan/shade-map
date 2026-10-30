# Roadmap

Current scope: ASU Tempe **and surrounding neighborhoods**, with an offline
prototype on the path to an iPhone and Android app. Height enrichment is paused
at the owner's request; the current ASU/OSM sources remain in use.

| Stage                           | Status                    | Evidence / remaining work                                                                    |
| ------------------------------- | ------------------------- | -------------------------------------------------------------------------------------------- |
| Solar + box queries             | Implemented               | Unit vectors, aware time, analytical rays                                                    |
| Polygon prisms                  | Implemented               | Concavity, holes, elevated bases, low Sun                                                    |
| Real neighborhood geometry      | Implemented prototype     | Cached OSM, UTM projection, ASU height provenance                                            |
| Building-part ownership         | Implemented               | Parent-specific subtraction; ambiguous/orphan parts flagged; elevated lower volumes retained |
| Local shadow field              | Implemented               | Dedicated `shadow_field.py`, bounded scene cache, daytime/night behavior                     |
| Pedestrian graph                | Implemented prototype     | Shared-node links, conservative access filters; no field validation                          |
| Candidate routing               | Implemented prototype     | Dedicated `routing.py`; shortest baseline, <=35% detour alternatives                         |
| Arrival-time exposure           | Implemented approximation | 3 m samples / 5 min solar bins; custom routes use edge midpoint arrival                      |
| Custom endpoints                | Implemented prototype     | Tap-to-place and drag pins, explicit <=100 m snap, same-point/error handling                 |
| Bounded map interaction         | Implemented               | Pan/zoom clamped to loaded area; context geometry clipped                                    |
| Live time-expanded search       | Implemented core          | 30 s arrival states; edge shade evaluated at traversal time                                  |
| Observed delay/condition events | Implemented core          | Stops, delays, blocks, discomfort, expiry and replanning API                                 |
| Deterministic walk simulator    | Implemented prototype     | Visible walker/clock, smooth route trail, continuous shadow display, pause and four events   |
| Timing uncertainty              | Planned                   | Speed distributions and early/late robust preference                                         |
| Route commitment                | Implemented threshold     | Keep valid path below 20 s weighted gain; GPS confidence and decision points planned         |
| Live app service                | Planned                   | Arbitrary dates, location, server API, app framework                                         |
| Phone field prototype           | Planned                   | iPhone/Android packaging and observed campus walks                                           |

## Indoor shortcuts: research added October 21, 2026

Public floor plans and accessible-entrance records are available for an initial
Hayden/Memorial Union pilot. Hayden Level One has a Cady Mall / Orange Mall
candidate; the concourse remains a separate level. No indoor passage is enabled.
Next: validate corridor continuity, doors, floor registration and schedules, then
connect verified corridors to the outdoor graph and compare actual travel times.
See INDOOR_SHORTCUTS.md. Noble and SDFC are excluded from accessible through-shortcut candidates per
owner reports. Prioritize engineering-building plans and identify the owner’s
shaded outdoor path near Palm Walk/SDFC as a separate lead.

## Next priorities

1. Review custom-pin behavior in a real browser/phone and validate graph entrances,
   barriers and crossings on selected walks.
2. Add a service boundary so fresh dates and locations do not require rebuilding
   an offline file. Keep the current file as a reproducible study artifact.
3. Add variable-speed scenario replay and timing uncertainty, then extend route
   commitment with GPS confidence and decision points.
4. Select the shared iPhone/Android application framework and deployment approach.

Do not describe candidate search as globally optimal time-dependent routing.
Height quality and additional sources are outside the current work order.
Direct owner-observed corrections may still be applied to an exact footprint;
The Crêpe Club currently has a low-confidence 3 m correction.

The Engineering Center's internal passage from the Annex/A-Wing gap to north of
F-Wing is enabled as owner-reported roof cover. Field-check its exact centerline,
the unroofed gap connection, width, low-angle side sun and supports.

## Indoor passage progress — October 21, 2026

MU and Hayden owner-confirmed traces are connected, with reported hours,
doorway-delay assumptions, indoor cover and outdoor fallback. Next: field-check
registration/distances, measure transition delays, add holiday exceptions and
identify engineering-building public corridors. See STATUS.md for limits.

Durham Hall's owner-confirmed east-west trace is also connected. Its public
18:00 cutoff and later ASU-ID requirement are enforced by the offline router.
Field-check its final closing time, east-door step-free status and corridor time.
