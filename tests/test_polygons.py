"""Physical fixtures for concave prisms, holes, and elevated structures."""

import pytest
from shapely.geometry import Point, Polygon, box

from shadeapp.polygons import Building


def test_rectangle_shadow_matches_analytical_length():
    shadow = Building(box(0, 0, 2, 2), 10).shadow((1, 0, 1))
    assert shadow.bounds == pytest.approx((-10, 0, 2, 2))
    assert shadow.covers(Point(-10, 1))
    assert not shadow.covers(Point(-10.01, 1))


def test_concavity_is_preserved_under_vertical_sun():
    footprint = Polygon([(0, 0), (4, 0), (4, 1), (1, 1), (1, 4), (0, 4)])
    shadow = Building(footprint, 10).shadow((0, 0, 1))
    assert shadow.equals(footprint)
    assert not shadow.covers(Point(2, 2))


def test_courtyard_stays_open_until_wall_shadow_reaches_it():
    footprint = Polygon(
        box(0, 0, 10, 10).exterior.coords, [box(2, 2, 8, 8).exterior.coords]
    )
    vertical = Building(footprint, 2).shadow((0, 0, 1))
    slanted = Building(footprint, 2).shadow((1, 0, 1))
    assert not vertical.covers(Point(7, 5))
    assert slanted.covers(Point(7, 5))
    assert not slanted.covers(Point(4, 5))


def test_elevated_prism_does_not_fill_unprojected_footprint():
    shadow = Building(box(0, 0, 2, 2), 10, 5).shadow((1, 0, 1))
    assert shadow.bounds == pytest.approx((-10, 0, -3, 2))
    assert not shadow.covers(Point(1, 1))


def test_low_sun_shadow_is_long_and_night_has_no_cast_polygon():
    building = Building(box(0, 0, 2, 2), 10)
    assert building.shadow((1, 0, 0.01)).bounds[0] == pytest.approx(-1000)
    assert building.shadow((0, 0, -1)).is_empty


@pytest.mark.parametrize(
    "height,base", [(0, 0), (5, 5), (5, -1), (float("inf"), 0)]
)
def test_invalid_heights_rejected(height, base):
    with pytest.raises(ValueError):
        Building(box(0, 0, 2, 2), height, base)
