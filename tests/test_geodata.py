"""Check projections, height estimates, and walking access rules."""

from math import hypot

import pytest

from shadeapp.geodata import (
    height_from_tags,
    parse_length,
    to_local,
    walking_graph,
)


@pytest.mark.parametrize(
    "text,metres",
    [("12", 12), ("12 m", 12), ("10 ft", 3.048), ("10'6\"", 3.2004)],
)
def test_length_units(text, metres):
    assert parse_length(text) == pytest.approx(metres)


def test_unknown_height_is_explicitly_assumed():
    assert height_from_tags({}) == (9, "assumed")
    assert height_from_tags({"building:levels": "4"}) == (12, "levels")
    assert height_from_tags({"height": "15"}) == (15, "tagged")
    assert height_from_tags({"height": "unknown"}) == (9, "assumed")


def test_local_origin_and_metric_scale():
    origin = to_local(-111.9281, 33.4242)
    east = to_local(-111.9271, 33.4242)
    assert origin == pytest.approx((0, 0))
    assert 90 < hypot(*east) < 95
    assert east[0] > 0


def test_graph_does_not_invent_sidewalks_or_allow_private_indoor_links():
    def way(identifier, tags):
        return {
            "type": "way",
            "id": identifier,
            "tags": tags,
            "nodes": [identifier * 2, identifier * 2 + 1],
            "geometry": [
                {"lon": -111.9281, "lat": 33.4242},
                {"lon": -111.928, "lat": 33.4242},
            ],
        }

    graph = walking_graph(
        [
            way(1, {"highway": "footway"}),
            way(2, {"highway": "footway", "access": "private"}),
            way(3, {"highway": "residential"}),
            way(4, {"highway": "footway", "indoor": "yes"}),
            way(5, {"highway": "cycleway", "foot": "no"}),
        ]
    )
    assert set(graph.edges()) == {(2, 3)}


def test_solar_direction_rotates_into_grid_north_without_changing_length():
    from shadeapp.geodata import solar_direction_to_grid

    projected_north = to_local(-111.9281, 33.4252)
    length = hypot(*projected_north)
    rotated = solar_direction_to_grid((0, 1, 0))
    assert rotated == pytest.approx(
        (projected_north[0] / length, projected_north[1] / length, 0)
    )
    assert hypot(rotated[0], rotated[1]) == pytest.approx(1)
    assert solar_direction_to_grid((0, 0, 1)) == (0, 0, 1)
