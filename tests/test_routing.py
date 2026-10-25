"""Meaningful behavior checks for the separated routing and field modules."""

from datetime import datetime, timezone

import networkx as nx
import numpy as np
import pytest
from shapely.geometry import box

from shadeapp.routing import candidate_paths, sample_route, score_route
from shadeapp.shadow_field import ShadowField


def graph_fixture():
    graph = nx.Graph()
    for node, point in [(0, (0, 0)), (1, (10, 0)), (2, (10, 10))]:
        graph.add_node(node, point=point)
    graph.add_edge(0, 1, length=10, sunny_length=10)
    graph.add_edge(1, 2, length=10, sunny_length=10)
    return graph


def test_sample_spacing_and_weights_are_metric():
    samples, distances, seconds = sample_route(graph_fixture(), [0, 1, 2])
    assert len(samples) == 8
    assert distances[0] == 1.25
    assert distances[-1] == 18.75
    assert seconds.sum() == pytest.approx(20 / 1.4)


def test_arrival_times_advance_and_zero_length_route_is_safe():
    class Field:
        def __init__(self):
            self.times = []

        def blocked(self, points, minute):
            self.times.append(minute)
            return np.full(len(points), minute >= 5)

    graph = nx.Graph()
    graph.add_node(0, point=(0, 0))
    graph.add_node(1, point=(840, 0))
    graph.add_edge(0, 1, length=840)
    field = Field()
    result = score_route(graph, [0, 1], 0, field)
    assert len(set(field.times)) > 1
    assert 0 < result["sunny"] < result["duration"]
    assert score_route(graph, [0], 0, field)["duration"] == 0


def test_candidates_respect_detour_limit():
    graph = nx.Graph()
    graph.add_edge(0, 1, length=100, sunny_length=100)
    graph.add_edge(0, 2, length=70, sunny_length=0)
    graph.add_edge(2, 1, length=70, sunny_length=0)
    assert candidate_paths(graph, 0, 1) == [[0, 1]]
    graph[0][2]["length"] = 60
    graph[2][1]["length"] = 60
    assert [0, 2, 1] in candidate_paths(graph, 0, 1)


def test_empty_field_night_and_scene_caches_are_separate():
    from shapely import points

    field = ShadowField(
        [],
        datetime(2026, 10, 20, tzinfo=timezone.utc),
        box(-100, -100, 100, 100),
    )
    assert field.blocked(points([[0, 0]]), 420).tolist() == [True]
    assert field.state(420) is field.state(420)
    other = ShadowField([], field.day, field.view)
    assert field.state(420) is not other.state(420)
