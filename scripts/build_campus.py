"""Build an offline ASU/Tempe map from a cached, attributed OSM extract."""

import json
from collections import Counter
from datetime import datetime, timedelta
from functools import lru_cache
from math import ceil, dist
from pathlib import Path
from typing import Dict, List, Tuple
from zoneinfo import ZoneInfo

import networkx as nx
import numpy as np
from shapely import points as make_points
from shapely.geometry import LineString, Point, box
from shapely.geometry.base import BaseGeometry
from shapely.strtree import STRtree

from shadeapp.geodata import (
    load_buildings,
    solar_direction_to_grid,
    to_local,
    walking_graph,
)
from shadeapp.solar import Sun

ROOT = Path(__file__).resolve().parents[1]
DAY = datetime(2026, 10, 20, tzinfo=ZoneInfo("America/Phoenix"))
SPEED = 1.4
# A neighborhood window, not an ASU administrative boundary.
WEST, SOUTH = to_local(-111.945, 33.409)
EAST, NORTH = to_local(-111.914, 33.439)
VIEW = box(WEST, SOUTH, EAST, NORTH)


def svg_path(geometry: BaseGeometry) -> str:
    """Serialize metric polygon rings into SVG, preserving holes."""
    polygons = (
        [geometry]
        if geometry.geom_type == "Polygon"
        else getattr(geometry, "geoms", [])
    )
    paths = []
    for polygon in polygons:
        if polygon.geom_type != "Polygon":
            continue
        for ring in [polygon.exterior, *polygon.interiors]:
            coordinates = list(ring.coords)
            paths.append(
                "M"
                + "L".join(f"{x:.1f},{y:.1f}" for x, y in coordinates)
                + "Z"
            )
    return "".join(paths)


def sample_route(
    graph: nx.Graph, nodes: List[int]
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return evenly weighted midpoint samples, up to 3 m apart."""
    samples, distances, weights = [], [], []
    distance_so_far = 0.0
    for first, second in zip(nodes, nodes[1:]):
        start = graph.nodes[first]["point"]
        end = graph.nodes[second]["point"]
        length = dist(start, end)
        count = max(1, ceil(length / 3))
        for index in range(count):
            fraction = (index + 0.5) / count
            samples.append(
                (
                    start[0] + (end[0] - start[0]) * fraction,
                    start[1] + (end[1] - start[1]) * fraction,
                )
            )
            distances.append(distance_so_far + length * fraction)
            weights.append(length / count / SPEED)
        distance_so_far += length
    return np.array(samples), np.array(distances), np.array(weights)


def build() -> None:
    """Build a reproducible map with route candidates and shade frames."""
    source = json.loads((ROOT / ".cache/campus-osm.json").read_text())
    buildings, skipped = load_buildings(source["elements"])
    graph = walking_graph(source["elements"])
    largest = max(nx.connected_components(graph), key=len)
    graph = graph.subgraph(largest).copy()
    graph.remove_nodes_from(
        [
            node
            for node in graph
            if not VIEW.covers(Point(graph.nodes[node]["point"]))
        ]
    )
    graph = graph.subgraph(max(nx.connected_components(graph), key=len)).copy()
    print(
        f"Using {len(buildings)} buildings and {len(graph)} connected nodes",
        flush=True,
    )
    # Candidate paths use only real shared-node pedestrian links.
    scenarios = []
    for origin_name, destination_name in [
        ("Memorial Union", "Noble Science and Engineering Library"),
        ("Memorial Union", "Brickyard Engineering"),
        ("Grady Gammage Memorial Auditorium", "Hayden Library"),
    ]:
        endpoints, offsets = [], []
        for name in (origin_name, destination_name):
            footprint = next(
                item.model.footprint for item in buildings if item.name == name
            )
            center = footprint.centroid
            node = min(
                graph,
                key=lambda item: dist(
                    graph.nodes[item]["point"], (center.x, center.y)
                ),
            )
            offset = center.distance(Point(graph.nodes[node]["point"]))
            if offset > 150:
                raise ValueError(
                    f"Endpoint {name} is too far from mapped paths"
                )
            endpoints.append(node)
            offsets.append(round(offset))
        shortest = nx.shortest_path(graph, *endpoints, weight="length")
        shortest_length = nx.path_weight(graph, shortest, "length")
        scenarios.append(
            {
                "from": origin_name,
                "to": destination_name,
                "endpoints": endpoints,
                "offsets": offsets,
                "shortest": shortest,
                "shortest_length": shortest_length,
            }
        )

    bounds = np.array([item.model.footprint.bounds for item in buildings])
    heights = np.array([item.model.height_m for item in buildings])
    edges = list(graph.edges(data=True))
    midpoints = make_points(
        [
            (
                (graph.nodes[a]["point"][0] + graph.nodes[b]["point"][0]) / 2,
                (graph.nodes[a]["point"][1] + graph.nodes[b]["point"][1]) / 2,
            )
            for a, b, _ in edges
        ]
    )

    @lru_cache(maxsize=6)
    def shadow_state(
        minute: int,
    ) -> Tuple[Sun, List[int], List[BaseGeometry], STRtree]:
        """Calculate prism shadows from the available building extract."""
        sun = Sun.at(33.4242, -111.9281, DAY + timedelta(minutes=minute))
        if sun.elevation_deg <= 0:
            return sun, [], [], STRtree([])
        grid_direction = solar_direction_to_grid(sun.direction)
        east, north, up = grid_direction
        dx, dy = -heights * east / up, -heights * north / up
        relevant = np.flatnonzero(
            (np.minimum(bounds[:, 0], bounds[:, 0] + dx) <= EAST)
            & (np.maximum(bounds[:, 2], bounds[:, 2] + dx) >= WEST)
            & (np.minimum(bounds[:, 1], bounds[:, 1] + dy) <= NORTH)
            & (np.maximum(bounds[:, 3], bounds[:, 3] + dy) >= SOUTH)
        )
        indices, shadows = [], []
        for index in relevant:
            geometry = buildings[index].model.shadow(grid_direction)
            if geometry.intersects(VIEW):
                indices.append(int(index))
                shadows.append(geometry)
        return sun, indices, shadows, STRtree(shadows)

    def blocked(samples: np.ndarray, minute: int) -> np.ndarray:
        sun, _, _, tree = shadow_state(minute)
        result = np.zeros(len(samples), dtype=bool)
        if sun.elevation_deg <= 0:
            result[:] = True
        elif len(samples):
            pairs = tree.query(samples, predicate="intersects")
            if pairs.size:
                result[pairs[0]] = True
        return result

    def score(nodes: List[int], departure_minute: int) -> Dict[str, object]:
        samples, distances, seconds = sample_route(graph, nodes)
        # Advance arrival time along the walk using five-minute solar bins.
        arrival_bins = (
            np.rint((departure_minute + distances / SPEED / 60) / 5) * 5
        ).astype(int)
        shaded = np.zeros(len(samples), dtype=bool)
        for minute in np.unique(arrival_bins):
            indices = np.flatnonzero(arrival_bins == minute)
            shaded[indices] = blocked(
                make_points(samples[indices]), int(minute)
            )
        duration = float(seconds.sum())
        sunny = float(seconds[~shaded].sum())
        return {
            "duration": round(duration, 1),
            "sunny": round(sunny, 1),
            "distance": round(duration * SPEED),
            "shade": round(100 * (1 - sunny / duration)),
        }

    frames = []
    # Half-hour departures for the fixed study date.
    for minute in range(480, 1021, 30):
        sun, indices, shadows, _ = shadow_state(minute)
        shade_at_edges = blocked(midpoints, minute)
        for (_, _, attributes), shade in zip(edges, shade_at_edges):
            attributes["sunny_length"] = 0 if shade else attributes["length"]
        route_sets = []
        for scenario in scenarios:
            candidates = [scenario["shortest"]]
            for preference in (1, 3, 8):
                candidate = nx.shortest_path(
                    graph,
                    *scenario["endpoints"],
                    weight=lambda a, b, attributes: (
                        attributes["length"]
                        + preference * attributes["sunny_length"]
                    ),
                )
                if (
                    candidate not in candidates
                    and nx.path_weight(graph, candidate, "length")
                    <= scenario["shortest_length"] * 1.35
                ):
                    candidates.append(candidate)
            routes = []
            for index, candidate in enumerate(candidates):
                metrics = score(candidate, minute)
                coordinates = [
                    graph.nodes[node]["point"] for node in candidate
                ]
                metrics["points"] = [
                    [round(x, 1), round(y, 1)] for x, y in coordinates
                ]
                metrics["name"] = (
                    "Shortest walk"
                    if index == 0
                    else f"Shade candidate {index}"
                )
                routes.append(metrics)
            route_sets.append(routes)
        frames.append(
            {
                "minute": minute,
                "elevation": round(sun.elevation_deg, 2),
                "shadows": [
                    [
                        svg_path(shape.intersection(VIEW).simplify(0.6)),
                        buildings[index].height_source,
                    ]
                    for index, shape in zip(indices, shadows)
                ],
                "routes": route_sets,
            }
        )
        print(
            f"Built {minute // 60:02}:{minute % 60:02}: "
            f"{len(shadows)} shadow polygons",
            flush=True,
        )
    visible = [
        item for item in buildings if item.model.footprint.intersects(VIEW)
    ]
    road_paths = []
    for element in source["elements"]:
        if element["type"] != "way" or "highway" not in element.get(
            "tags", {}
        ):
            continue
        geometry = element.get("geometry", [])
        if len(geometry) < 2:
            continue
        line = LineString([to_local(p["lon"], p["lat"]) for p in geometry])
        if not line.intersects(VIEW):
            continue
        road_paths.append(
            {
                "points": [[round(x, 1), round(y, 1)] for x, y in line.coords],
                "type": element["tags"]["highway"],
                "name": element["tags"].get("name", ""),
            }
        )
    payload = {
        "bounds": [WEST, SOUTH, EAST, NORTH],
        "buildings": [
            {
                "path": svg_path(item.model.footprint.simplify(0.4)),
                "name": item.name or "Unnamed building",
                "height": round(item.model.height_m, 1),
                "source": item.height_source,
                "osm_id": item.osm_id,
            }
            for item in visible
        ],
        "roads": road_paths,
        "scenarios": [
            {
                key: value
                for key, value in scenario.items()
                if key in {"from", "to", "offsets"}
            }
            for scenario in scenarios
        ],
        "frames": frames,
        "coverage": dict(Counter(item.height_source for item in visible)),
        "skipped": skipped,
        "snapshot": source["osm3s"]["timestamp_osm_base"],
    }
    template = (ROOT / "demo/campus-template.html").read_text()
    destination = ROOT / "demo/campus.html"
    # Escape markup-significant characters in untrusted OSM labels.
    embedded = json.dumps(payload, separators=(",", ":")).replace(
        "<", "\\u003c"
    )
    destination.write_text(template.replace("__CAMPUS_DATA__", embedded))
    (ROOT / ".cache/campus-summary.json").write_text(
        json.dumps(
            {
                "buildings": len(visible),
                "coverage": payload["coverage"],
                "nodes": len(graph),
                "edges": graph.number_of_edges(),
                "snapshot": payload["snapshot"],
                "skipped": skipped,
            },
            indent=2,
        )
    )
    print(f"Built {destination}: {destination.stat().st_size:,} bytes")


if __name__ == "__main__":
    build()
