"""Read a cached OpenStreetMap extract into local metric geometry."""

import re
from dataclasses import dataclass
from math import hypot
from typing import Dict, List, Tuple

import networkx as nx
from pyproj import Transformer
from shapely.geometry import LineString, Polygon
from shapely.ops import polygonize, unary_union

from shadeapp.polygons import Building

ORIGIN_LAT = 33.4242
ORIGIN_LON = -111.9281
TRANSFORMER = Transformer.from_crs("EPSG:4326", "EPSG:32612", always_xy=True)
ORIGIN_EAST, ORIGIN_NORTH = TRANSFORMER.transform(ORIGIN_LON, ORIGIN_LAT)


def to_local(longitude: float, latitude: float) -> Tuple[float, float]:
    """Project WGS84 lon/lat to local UTM 12N metres near ASU Tempe."""
    east, north = TRANSFORMER.transform(longitude, latitude)
    return east - ORIGIN_EAST, north - ORIGIN_NORTH


def solar_direction_to_grid(
    direction: Tuple[float, float, float],
) -> Tuple[float, float, float]:
    """Rotate true East/North solar components into the local UTM grid axes.

    Grid north and true north differ slightly at Tempe. Use the projected
    geographic meridian at the origin to preserve the directional convention.
    """
    north_east, north_north = to_local(ORIGIN_LON, ORIGIN_LAT + 0.001)
    length = hypot(north_east, north_north)
    north_east /= length
    north_north /= length
    east, north, up = direction
    return (
        east * north_north + north * north_east,
        -east * north_east + north * north_north,
        up,
    )


def parse_length(value: str) -> float:
    """Read metres, explicit feet, or feet/inches; reject ambiguous values."""
    text = str(value).strip()
    metric = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(?:m)?", text)
    feet = re.fullmatch(
        r"(\d+(?:\.\d+)?)\s*(?:ft|\')(?:(\d+(?:\.\d+)?)\")?", text
    )
    if metric:
        return float(metric.group(1))
    if feet:
        return (
            float(feet.group(1)) * 0.3048 + float(feet.group(2) or 0) * 0.0254
        )
    raise ValueError(f"Unsupported length: {value}")


def height_from_tags(tags: Dict[str, str]) -> Tuple[float, str]:
    """Prefer tagged height, then levels × 3 m, else explicit 9 m fallback."""
    if "height" in tags:
        try:
            height = parse_length(tags["height"])
            if height > 0:
                return height, "tagged"
        except ValueError:
            pass
    try:
        levels = float(tags.get("building:levels", "0"))
        if 0 < levels < 200:
            return levels * 3, "levels"
    except ValueError:
        pass
    return 9.0, "assumed"


@dataclass
class MapBuilding:
    """Projected geometry with source identity and height provenance."""

    model: Building
    osm_id: str
    name: str
    height_source: str


def _coordinates(geometry: List[dict]) -> List[Tuple[float, float]]:
    return [to_local(point["lon"], point["lat"]) for point in geometry]


def load_buildings(elements: List[dict]) -> Tuple[List[MapBuilding], int]:
    """Load polygon ways and multipolygon relations, preserving inner rings.

    Building parts replace parent outlines where available. The remaining
    parent footprint stays in the model with its explicitly sourced height.
    """
    results = []
    skipped = 0
    member_ids = {
        member["ref"]
        for element in elements
        if element["type"] == "relation"
        and "building" in element.get("tags", {})
        for member in element.get("members", [])
        if member["type"] == "way"
    }
    parts = []
    for element in elements:
        tags = element.get("tags", {})
        if not ("building" in tags or "building:part" in tags):
            continue
        if element["type"] == "way" and element["id"] in member_ids:
            continue
        try:
            if element["type"] == "relation":
                outer_lines, inner_lines = [], []
                for member in element.get("members", []):
                    if member.get("type") != "way" or not member.get(
                        "geometry"
                    ):
                        continue
                    line = LineString(_coordinates(member["geometry"]))
                    (
                        inner_lines
                        if member.get("role") == "inner"
                        else outer_lines
                    ).append(line)
                outer = unary_union(list(polygonize(outer_lines)))
                inner = unary_union(list(polygonize(inner_lines)))
                geometry = outer.difference(inner)
            else:
                coordinates = _coordinates(element["geometry"])
                if len(coordinates) < 4 or coordinates[0] != coordinates[-1]:
                    skipped += 1
                    continue
                geometry = Polygon(coordinates)
            if geometry.is_empty or not geometry.is_valid:
                skipped += 1
                continue
            height, source = height_from_tags(tags)
            minimum = parse_length(tags.get("min_height", "0"))
            polygons = (
                [geometry]
                if geometry.geom_type == "Polygon"
                else list(geometry.geoms)
            )
            for polygon in polygons:
                if polygon.geom_type != "Polygon" or polygon.area < 1:
                    continue
                item = MapBuilding(
                    Building(polygon, height, minimum),
                    f"{element['type']}/{element['id']}",
                    tags.get("name", ""),
                    source,
                )
                if "building:part" in tags:
                    parts.append(item)
                else:
                    results.append(item)
        except (KeyError, ValueError, TypeError):
            skipped += 1
    # Remove parent volume underneath detailed parts to avoid double blocking.
    if parts:
        part_union = unary_union([item.model.footprint for item in parts])
        clipped = []
        for item in results:
            remainder = item.model.footprint.difference(part_union)
            polygons = (
                [remainder]
                if remainder.geom_type == "Polygon"
                else list(getattr(remainder, "geoms", []))
            )
            for polygon in polygons:
                if polygon.geom_type == "Polygon" and polygon.area >= 1:
                    clipped.append(
                        MapBuilding(
                            Building(
                                polygon,
                                item.model.height_m,
                                item.model.min_height_m,
                            ),
                            item.osm_id,
                            item.name,
                            item.height_source,
                        )
                    )
        results = clipped
    return results + parts, skipped


def walking_graph(elements: List[dict]) -> nx.Graph:
    """Connect publicly accessible outdoor pedestrian ways by shared OSM nodes.

    Motor roads are drawn separately but not used as inferred sidewalks.
    Gates, temporary closures, stairs and accessibility need later validation.
    """
    graph = nx.Graph()
    allowed = {
        "footway",
        "path",
        "pedestrian",
        "steps",
        "living_street",
        "cycleway",
        "residential",
        "service",
        "track",
        "unclassified",
    }
    for element in elements:
        tags = element.get("tags", {})
        if element["type"] != "way" or tags.get("highway") not in allowed:
            continue
        if (
            tags.get("foot") in {"no", "private"}
            or tags.get("access") in {"no", "private"}
            or tags.get("indoor") == "yes"
            or tags.get("area") == "yes"
            or tags.get("highway") == "cycleway"
            and tags.get("foot") not in {"yes", "designated", "permissive"}
            or tags.get("highway")
            in {"residential", "service", "unclassified"}
        ):
            continue
        coordinates = _coordinates(element.get("geometry", []))
        nodes = element.get("nodes", [])
        if len(nodes) != len(coordinates):
            continue
        for node, point in zip(nodes, coordinates):
            graph.add_node(node, point=point)
        for first, second, start, end in zip(
            nodes, nodes[1:], coordinates, coordinates[1:]
        ):
            length = LineString([start, end]).length
            if length > 0:
                graph.add_edge(
                    first,
                    second,
                    length=length,
                    name=tags.get("name", ""),
                    steps=tags.get("highway") == "steps",
                )
    return graph
