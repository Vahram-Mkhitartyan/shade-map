"""Connect owner-confirmed covered paths to a mapped pedestrian graph."""

from copy import deepcopy
from typing import List

import networkx as nx
from shapely.geometry import LineString, Point

from shadeapp.geodata import to_local


def connect_walkways(graph: nx.Graph, features: List[dict]) -> nx.Graph:
    """Return a graph with confirmed paths and bounded Palm Walk ties.

    Split the nearest named Palm Walk edge at each endpoint projection. This
    preserves connectivity even when both connections share one original edge.
    Short exterior ties are unroofed. Work on a copy so rejection is atomic.
    """
    result = deepcopy(graph)
    next_node = min(0, min(result.nodes, default=0)) - 1
    for feature in features:
        properties = feature["properties"]
        if not properties.get("routing_enabled"):
            continue
        if not properties.get("both_ends_connected"):
            raise ValueError("Both endpoint connections must be confirmed")
        points = [
            to_local(*point) for point in feature["geometry"]["coordinates"]
        ]
        if len(points) != 2:
            raise ValueError(
                "This connector requires a straight two-point path"
            )
        endpoints = []
        for point in (points[0], points[-1]):
            choices = []
            for first, second, data in result.edges(data=True):
                if data.get("name") != "Palm Walk":
                    continue
                line = LineString(
                    [
                        result.nodes[first]["point"],
                        result.nodes[second]["point"],
                    ]
                )
                projection = line.interpolate(line.project(Point(point)))
                choices.append(
                    (
                        projection.distance(Point(point)),
                        first,
                        second,
                        projection,
                    )
                )
            if not choices or min(choice[0] for choice in choices) > 15:
                raise ValueError("Covered path is too far from Palm Walk")
            _, first, second, projection = min(choices, key=lambda row: row[0])
            anchor = (projection.x, projection.y)
            junction = None
            for node in (first, second):
                if (
                    Point(result.nodes[node]["point"]).distance(projection)
                    < 0.01
                ):
                    junction = node
            if junction is None:
                junction, next_node = next_node, next_node - 1
                attributes = dict(result[first][second])
                result.remove_edge(first, second)
                result.add_node(junction, point=anchor)
                for neighbor in (first, second):
                    length = Point(result.nodes[neighbor]["point"]).distance(
                        projection
                    )
                    result.add_edge(
                        neighbor, junction, **{**attributes, "length": length}
                    )
            endpoint, next_node = next_node, next_node - 1
            result.add_node(endpoint, point=point)
            result.add_edge(
                junction,
                endpoint,
                length=Point(point).distance(projection),
                name=properties["name"] + " connection",
                covered=False,
                source="owner-confirmed connection",
            )
            endpoints.append(endpoint)
        line = LineString(points)
        result.add_edge(
            *endpoints,
            length=line.length,
            name=properties["name"],
            covered=True,
            source=properties["source"],
        )
    return result


def covered_segments(graph: nx.Graph) -> List[LineString]:
    """Return only roof-covered centerlines, excluding exterior connectors."""
    return [
        LineString([graph.nodes[a]["point"], graph.nodes[b]["point"]])
        for a, b, data in graph.edges(data=True)
        if data.get("covered")
    ]
