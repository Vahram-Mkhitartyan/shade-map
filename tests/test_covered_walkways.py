"""Confirmed cover must connect properly and affect only its own centerline."""

from datetime import datetime, timezone

import networkx as nx
from shapely import points
from shapely.geometry import LineString, box

from shadeapp.covered_walkways import connect_walkways, covered_segments
from shadeapp.geodata import to_local
from shadeapp.shadow_field import ShadowField


def test_both_ends_split_same_palm_walk_edge_without_disconnect():
    graph = nx.Graph()
    first = to_local(-111.9327, 33.41735)
    last = to_local(-111.9327, 33.41822)
    graph.add_node(1, point=first)
    graph.add_node(2, point=last)
    graph.add_edge(
        1, 2, name="Palm Walk", length=LineString([first, last]).length
    )
    feature = {
        "properties": {
            "routing_enabled": True,
            "both_ends_connected": True,
            "name": "Covered path",
            "source": "owner",
            "connection_path_name": "Palm Walk",
        },
        "geometry": {
            "coordinates": [
                [-111.932648, 33.4181708],
                [-111.9326374, 33.4175093],
            ]
        },
    }
    result = connect_walkways(graph, [feature])
    assert len(graph) == 2
    assert len(result) == 6
    assert nx.is_connected(result)
    assert len(covered_segments(result)) == 1
    assert (
        sum(bool(data.get("covered")) for *_, data in result.edges(data=True))
        == 1
    )
    assert nx.has_path(result, 1, 2)
    assert all(data["length"] > 0 for *_, data in result.edges(data=True))


def test_roof_proxy_does_not_cover_adjacent_path_or_connector():
    field = ShadowField(
        [],
        datetime(2026, 10, 21, tzinfo=timezone.utc),
        box(-50, -50, 50, 50),
        covered_paths=[LineString([(0, 0), (0, 20)])],
    )
    result = field.blocked(points([[0, 10], [2, 10], [0, 25]]), 1140)
    assert result.tolist() == [True, False, False]


def test_internal_passage_uses_separate_rules_for_each_endpoint():
    graph = nx.Graph()
    coordinates = [
        (-111.932104996, 33.4198207525),
        (-111.9320933555, 33.4187314213),
    ]
    north = to_local(*coordinates[0])
    south = to_local(*coordinates[1])
    graph.add_node(0, point=(north[0] - 20, north[1]))
    graph.add_node(1, point=(north[0] + 20, north[1]))
    graph.add_node(2, point=(south[0] - 20, south[1] - 20))
    graph.add_node(3, point=(south[0] - 20, south[1] + 20))
    graph.add_edge(0, 1, name="North cross path", length=40)
    graph.add_edge(2, 3, name="Palm Walk", length=40)
    feature = {
        "properties": {
            "routing_enabled": True,
            "both_ends_connected": True,
            "name": "Internal covered passage",
            "source": "owner",
            "connection_path_names": [None, "Palm Walk"],
            "connection_max_distances_m": [1, 25],
        },
        "geometry": {"coordinates": coordinates},
    }

    result = connect_walkways(graph, [feature])

    assert result.number_of_nodes() == 7
    assert result.number_of_edges() == 6
    assert nx.is_connected(result)
    covered = [
        data for *_, data in result.edges(data=True) if data.get("covered")
    ]
    assert len(covered) == 1
    assert 118 < covered[0]["length"] < 125
    assert all(data["length"] > 0 for *_, data in result.edges(data=True))
