"""Register confirmed corridor traces and attach doors to outdoor paths.

Coordinates are local grid metres. Floor-plan pixels are registered against
ASU entrances and OSM facade controls; geometry is an approximate prototype.
"""

from copy import deepcopy
from math import dist
from typing import List

import networkx as nx
import numpy as np
from shapely.geometry import LineString, Point

from shadeapp.geodata import to_local


def register_trace(passage: dict) -> dict:
    """Project a geographic trace or fit an affine floor-plan registration."""
    if "coordinates" in passage:
        points = {
            key: to_local(*coordinates)
            for key, coordinates in passage["coordinates"].items()
        }
        return {**passage, "points": points}

    controls = passage["controls"]
    pixels = np.array([row["pixel"] + [1] for row in controls])
    targets = np.array(
        [
            row["local"] if "local" in row else to_local(*row["coordinates"])
            for row in controls
        ]
    )
    if np.linalg.matrix_rank(pixels) < 3:
        raise ValueError("Registration controls must be non-collinear")
    transform = np.linalg.lstsq(pixels, targets, rcond=None)[0]
    points = {
        key: tuple(np.array(pixel + [1]) @ transform)
        for key, pixel in passage["pixels"].items()
    }
    return {**passage, "points": points}


def connect_passages(graph: nx.Graph, passages: List[dict]) -> nx.Graph:
    """Add traced public corridors, splitting bounded exterior path ties.

    Ties must not cross the building interior. Failed registration or a missing
    exterior connection aborts the build instead of silently adding a jump.
    Door edges carry a provisional ten-second delay in either direction.
    """
    result = deepcopy(graph)
    next_node = min(0, min(result.nodes, default=0)) - 1
    for passage in passages:
        if not passage.get("routing_enabled"):
            continue
        nodes = {}
        for key, point in passage["points"].items():
            nodes[key], next_node = next_node, next_node - 1
            result.add_node(nodes[key], point=point, indoor=True)
        common = {
            "indoor": True,
            "covered": True,
            "passage": passage["id"],
            "schedule": passage["schedule"],
            "name": passage["name"],
            "access_after": passage.get("access_after"),
            "required_access": passage.get("required_access"),
        }
        for first, second in passage["links"]:
            result.add_edge(
                nodes[first],
                nodes[second],
                length=dist(
                    passage["points"][first], passage["points"][second]
                ),
                **common,
            )
        for key in passage["doors"]:
            point = Point(passage["points"][key])
            choices = []
            for first, second, data in result.edges(data=True):
                if data.get("indoor"):
                    continue
                line = LineString(
                    [
                        result.nodes[first]["point"],
                        result.nodes[second]["point"],
                    ]
                )
                if line.length < 0.01:
                    continue
                anchor = line.interpolate(line.project(point))
                tie = LineString([point, anchor])
                # Allow a small registration tolerance at the doorway only.
                if tie.intersection(passage["footprint"].buffer(-2)).length:
                    continue
                choices.append((point.distance(anchor), first, second, anchor))
            if not choices or min(row[0] for row in choices) > 25:
                raise ValueError(
                    "No exterior path within 25 m of passage door " + key
                )
            length, first, second, anchor = min(choices, key=lambda r: r[0])
            junction = next_node
            next_node -= 1
            attrs = dict(result[first][second])
            result.remove_edge(first, second)
            result.add_node(junction, point=(anchor.x, anchor.y))
            for neighbor in (first, second):
                result.add_edge(
                    junction,
                    neighbor,
                    **{
                        **attrs,
                        "length": anchor.distance(
                            Point(result.nodes[neighbor]["point"])
                        ),
                    },
                )
            result.add_edge(
                junction,
                nodes[key],
                length=length,
                **{
                    **common,
                    "covered": False,
                    "delay": 10,
                    "name": passage["name"] + " doorway",
                },
            )
    return result


def is_open(schedule: list, weekday: int, start: float, end: float) -> bool:
    """Check a full traversal against reported local weekly opening hours."""
    opening, closing = schedule[weekday]
    return opening <= start and end <= closing
