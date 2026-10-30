"""Connect owner-confirmed covered paths to a mapped pedestrian graph."""

from copy import deepcopy
from typing import List

import networkx as nx
from shapely.geometry import LineString, Point

from shadeapp.geodata import to_local


def connect_walkways(graph: nx.Graph, features: List[dict]) -> nx.Graph:
    """Return a graph with confirmed covered paths.

    Centerlines split the nearest eligible pedestrian edge at each endpoint
    projection. Short ties between observed endpoints and mapped paths remain
    unroofed. Work on a copy so rejection is atomic.
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
        path_names = properties.get("connection_path_names")
        max_distances = properties.get("connection_max_distances_m")
        for index, point in enumerate((points[0], points[-1])):
            choices = []
            path_name = (
                path_names[index]
                if path_names is not None
                else properties.get("connection_path_name")
            )
            max_distance = (
                max_distances[index]
                if max_distances is not None
                else properties.get("connection_max_distance_m", 15)
            )
            for first, second, data in result.edges(data=True):
                if path_name and data.get("name") != path_name:
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
            if (
                not choices
                or min(choice[0] for choice in choices) > max_distance
            ):
                raise ValueError("Covered endpoint is too far from a path")
            distance, first, second, projection = min(
                choices, key=lambda row: row[0]
            )
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
            endpoint = junction
            if distance >= 0.01:
                endpoint, next_node = next_node, next_node - 1
                result.add_node(endpoint, point=point)
                result.add_edge(
                    junction,
                    endpoint,
                    length=distance,
                    name=properties["name"] + " connection",
                    covered=False,
                    source=properties.get(
                        "connection_source", "owner-confirmed connection"
                    ),
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
