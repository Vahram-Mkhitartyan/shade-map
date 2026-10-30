"""Build an offline ASU/Tempe map from a cached, attributed OSM extract."""

import base64
import json
from collections import Counter
from datetime import datetime
from math import dist
from pathlib import Path
from zoneinfo import ZoneInfo

import networkx as nx
import numpy as np
from shapely.geometry import LineString, Point, box
from shapely.geometry.base import BaseGeometry

from shadeapp.asu_heights import apply_asu_heights, apply_height_overrides
from shadeapp.covered_walkways import connect_walkways, covered_segments
from shadeapp.geodata import load_buildings, to_local, walking_graph
from shadeapp.indoor_passages import connect_passages, register_trace
from shadeapp.routing import (
    candidate_paths,
    edge_samples,
    edge_sunlight,
    score_route,
)
from shadeapp.shadow_field import ShadowField

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


def render_payload(payload: dict) -> None:
    """Package a cached model with the current offline interface sources."""
    payload["network"]["routing_bin_seconds"] = 30
    annotations = json.loads(
        (ROOT / "data/covered_walkways.geojson").read_text()
    )
    payload["covered_walkways"] = [
        {
            "id": feature["id"],
            "points": [
                list(to_local(*point))
                for point in feature["geometry"]["coordinates"]
            ],
            **feature["properties"],
        }
        for feature in annotations["features"]
    ]
    template = (ROOT / "demo/campus-template.html").read_text()
    destination = ROOT / "demo/campus.html"
    # Escape markup-significant characters in untrusted OSM labels.
    embedded = json.dumps(payload, separators=(",", ":")).replace(
        "<", "\\u003c"
    )
    template = template.replace(
        "__ROUTING_SCRIPT__", (ROOT / "demo/offline-routing.js").read_text()
    ).replace(
        "__VIEWPORT_SCRIPT__", (ROOT / "demo/map-viewport.js").read_text()
    )
    (ROOT / ".cache/campus-payload.json").write_text(embedded)
    destination.write_text(template.replace("__CAMPUS_DATA__", embedded))
    print(f"Rendered {destination}: {destination.stat().st_size:,} bytes")


def build() -> None:
    """Build a reproducible map with route candidates and shade frames."""
    source = json.loads((ROOT / ".cache/campus-osm.json").read_text())
    buildings, skipped = load_buildings(source["elements"])
    asu_source = json.loads((ROOT / ".cache/asu-facilities.json").read_text())
    buildings, asu_matches = apply_asu_heights(
        buildings, asu_source["features"]
    )
    height_overrides = json.loads(
        (ROOT / "data/height_overrides.json").read_text()
    )
    buildings, override_matches = apply_height_overrides(
        buildings, height_overrides
    )
    print(
        f"Matched {asu_matches} ASU heights and {override_matches} "
        "explicit overrides",
        flush=True,
    )
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
    annotations = json.loads(
        (ROOT / "data/covered_walkways.geojson").read_text()
    )
    graph = connect_walkways(graph, annotations["features"])
    passages = [
        register_trace(item)
        for item in json.loads(
            (ROOT / "data/indoor_passages.json").read_text()
        )
    ]
    for passage in passages:
        mu = next(
            item for item in buildings if item.name == passage["building"]
        )
        passage["footprint"] = mu.model.footprint
        for key in passage["doors"]:
            point = Point(passage["points"][key])
            boundary = mu.model.footprint.boundary
            anchor = boundary.interpolate(boundary.project(point))
            if point.distance(anchor) > 12:
                raise ValueError("Indoor door registration exceeds 12 m")
            passage["points"][key] = (anchor.x, anchor.y)
    graph = connect_passages(graph, passages)
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

    field = ShadowField(
        buildings, DAY, VIEW, covered_paths=covered_segments(graph)
    )
    edges = list(graph.edges(data=True))
    samples, owners = edge_samples(graph, edges)
    frames = []
    # Half-hour departures for the fixed study date.
    for minute in range(480, 1021, 30):
        state = field.state(minute)
        sun = state.sun
        indices, shadows = state.building_indices, state.polygons
        sun_fractions = edge_sunlight(
            field, minute, samples, owners, len(edges)
        )
        for (_, _, attributes), fraction in zip(edges, sun_fractions):
            attributes["sunny_length"] = fraction * attributes["length"]
        route_sets = []
        for scenario in scenarios:
            candidates = candidate_paths(graph, *scenario["endpoints"])
            routes = []
            for index, candidate in enumerate(candidates):
                metrics = score_route(graph, candidate, minute, field)
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
    node_ids = list(graph)
    node_indices = {node: index for index, node in enumerate(node_ids)}
    edge_table = [
        [
            node_indices[first],
            node_indices[second],
            round(attributes["length"], 3),
            attributes.get("delay", 0),
            attributes.get("schedule"),
            attributes.get("passage"),
            attributes.get("access_after"),
            attributes.get("required_access"),
        ]
        for first, second, attributes in edges
    ]
    sunlight_table = []
    for minute in range(480, 1141, 5):
        fractions = edge_sunlight(field, minute, samples, owners, len(edges))
        sunlight_table.append(
            base64.b64encode(
                np.rint(fractions * 255).astype(np.uint8).tobytes()
            ).decode("ascii")
        )
        if minute % 30 == 0:
            print(
                f"Custom endpoint field: {minute // 60:02}:{minute % 60:02}",
                flush=True,
            )
    payload = {
        "bounds": [WEST, SOUTH, EAST, NORTH],
        "network": {
            "weekday": DAY.weekday(),
            "points": [
                [round(value, 2) for value in graph.nodes[node]["point"]]
                for node in node_ids
            ],
            "indoor_nodes": [
                node_indices[node]
                for node in node_ids
                if graph.nodes[node].get("indoor")
            ],
            "edges": edge_table,
            "sunlight": sunlight_table,
            "first_minute": 480,
            "bin_minutes": 5,
            "routing_bin_seconds": 30,
            "max_walk_seconds": 7200,
        },
        "indoor_passages": [
            {
                "id": item["id"],
                "name": item["name"],
                "source": item["source"],
                "geometry_note": item["geometry_note"],
                "access_note": item.get("access_note", ""),
                "step_free": item.get("step_free"),
                "lines": [
                    [item["points"][a], item["points"][b]]
                    for a, b in item["links"]
                ],
            }
            for item in passages
        ],
        "buildings": [
            {
                "path": svg_path(item.model.footprint.simplify(0.4)),
                "name": item.name or "Unnamed building",
                "height": round(item.model.height_m, 1),
                "source": item.height_source,
                "osm_id": item.osm_id,
                "height_reference": item.height_reference,
                "is_part": item.is_part,
                "parent_id": item.parent_id,
                "ownership": item.ownership,
            }
            for item in visible
        ],
        "roads": road_paths,
        "scenarios": [
            {
                "nodes": [
                    node_indices[node] for node in scenario["endpoints"]
                ],
                **{
                    key: value
                    for key, value in scenario.items()
                    if key in {"from", "to", "offsets"}
                },
            }
            for scenario in scenarios
        ],
        "frames": frames,
        "coverage": dict(Counter(item.height_source for item in visible)),
        "skipped": skipped,
        "snapshot": source["osm3s"]["timestamp_osm_base"],
    }
    render_payload(payload)
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


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--render-only",
        action="store_true",
        help="Repackage cached fields without recalculation",
    )
    arguments = parser.parse_args()
    if arguments.render_only:
        render_payload(
            json.loads((ROOT / ".cache/campus-payload.json").read_text())
        )
    else:
        build()
