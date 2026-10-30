"""Validate indoor access intervals and graph connection invariants."""

import networkx as nx
import pytest
from shapely.geometry import box

from shadeapp.indoor_passages import connect_passages, is_open, register_trace


def test_full_traversal_must_fit_open_interval():
    schedule = [[390, 1320]] * 5 + [[480, 1320], [600, 1320]]
    assert is_open(schedule, 1, 390, 400)
    assert not is_open(schedule, 6, 599, 601)
    assert is_open(schedule, 6, 600, 1320)
    assert not is_open(schedule, 1, 1319, 1320.01)


def test_registration_rejects_collinear_controls():
    with pytest.raises(ValueError, match="non-collinear"):
        register_trace(
            {
                "controls": [
                    {"pixel": [x, 0], "local": [x, 0]} for x in range(3)
                ]
            }
        )


def test_geographic_trace_projects_each_named_point():
    passage = register_trace(
        {
            "coordinates": {
                "west": [-111.93470884303507, 33.420828346019086],
                "east": [-111.93445726804312, 33.420968026322036],
            }
        }
    )
    assert passage["points"]["west"] != passage["points"]["east"]
    assert passage["points"]["west"][0] < passage["points"]["east"][0]


def test_door_ties_preserve_exterior_graph_without_crossing_building():
    graph = nx.Graph()
    for key, point in enumerate([(-5, -5), (15, -5), (15, 15), (-5, 15)]):
        graph.add_node(key, point=point)
    for a, b in [(0, 1), (1, 2), (2, 3), (3, 0)]:
        graph.add_edge(a, b, length=20)
    passage = {
        "id": "lobby",
        "name": "Lobby",
        "routing_enabled": True,
        "points": {"west": (0, 5), "turn": (5, 5), "south": (5, 0)},
        "links": [("west", "turn"), ("turn", "south")],
        "doors": ["west", "south"],
        "footprint": box(0, 0, 10, 10),
        "schedule": [[420, 1440]] * 7,
    }
    result = connect_passages(graph, [passage])
    assert nx.is_connected(result)
    assert graph.number_of_edges() == 4
    doors = [d for _, _, d in result.edges(data=True) if d.get("delay")]
    assert len(doors) == 2
    assert all(d["length"] == 5 and not d["covered"] for d in doors)
    assert (
        sum(d.get("covered", False) for _, _, d in result.edges(data=True))
        == 2
    )
