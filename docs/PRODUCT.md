# Product brief

## Purpose

Help pedestrians choose a reasonably direct walk with less predicted direct sunlight.
The initial pilot is ASU's Tempe campus, as specified in the original repository README.
Campus boundaries and the first demonstration origin/destination remain to be selected.

## Platforms

The eventual app targets both iPhone and Android. The first deliverable is an
offline browser prototype; the production app framework is not selected yet.

## First usable experience

Choose a destination, departure time, walking speed, and shade preference. Compare a
fast route with a shade-aware alternative, including distance, time, and predicted
sun exposure. During navigation, preserve the chosen route unless deviation or a
meaningful improvement justifies changing it.

## MVP scope

Buildings, solar position, pedestrian paths, flat-ground hard shadows, arrival-time
exposure, and a 2D map. Start with synthetic fixtures before connecting real data.
Explain missing geometry and estimated heights rather than claiming complete coverage.

## Deferred

Trees, soft shadows, weather, heat/UV models, detailed roofs, terrain, accessibility
routing, and production navigation. No continuous 3D rendering is needed.

## Acceptance targets to establish

- Shadow checks agree with analytical fixtures and later field observations.
- Baseline routes follow valid pedestrian connections.
- Exposure uses predicted traversal times and reports its units.
- Shade alternatives obey an explicit detour policy.
- Small timing/GPS changes do not cause route oscillation.
- Performance targets follow measurement on a selected campus corridor.

Numerical targets and the detour policy are open decisions, not promises.
