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
