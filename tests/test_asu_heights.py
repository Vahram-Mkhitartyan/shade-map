"""Validate source matching and feet-to-metre conversion."""

import pytest
from shapely.geometry import Polygon

from shadeapp.asu_heights import apply_asu_heights
from shadeapp.geodata import MapBuilding, to_local
from shadeapp.polygons import Building

RING = [
    (-111.93, 33.42),
    (-111.93, 33.4201),
    (-111.9299, 33.4201),
    (-111.9299, 33.42),
    (-111.93, 33.42),
]


def fixture_building(base=0):
    footprint = Polygon([to_local(*point) for point in RING])
    return MapBuilding(
        Building(footprint, 9, base), "way/1", "Test", "assumed"
    )


def facility(height=50, identifier=1, ring=None):
    return {
        "attributes": {"OBJECTID": identifier, "BLDG_HEIGHT_FT": height},
        "geometry": {"rings": [ring or RING]},
    }


def test_matching_height_converts_feet_and_keeps_footprint():
    original = fixture_building()
    result, count = apply_asu_heights([original], [facility()])
    assert count == 1
    assert result[0].model.height_m == pytest.approx(15.24)
    assert result[0].model.footprint.equals(original.model.footprint)
    assert result[0].height_source == "asu"
    assert "OBJECTID 1" in result[0].height_reference


def test_ambiguous_overlapping_facilities_remain_unmatched():
    original = fixture_building()
    result, count = apply_asu_heights(
        [original], [facility(), facility(70, 2)]
    )
    assert count == 0
    assert result[0] is original


@pytest.mark.parametrize("height", [0, None, -5, float("nan"), float("inf")])
def test_missing_or_invalid_heights_never_replace_estimates(height):
    result, count = apply_asu_heights([fixture_building()], [facility(height)])
    assert count == 0
    assert result[0].height_source == "assumed"


def test_elevated_part_is_not_flattened_to_facility_height():
    original = fixture_building(base=4)
    result, count = apply_asu_heights([original], [facility()])
    assert count == 0
    assert result[0].model.min_height_m == 4


def test_nearby_nonoverlapping_building_is_not_assigned_height():
    ring = [(lon + 0.001, lat) for lon, lat in RING]
    result, count = apply_asu_heights(
        [fixture_building()], [facility(ring=ring)]
    )
    assert count == 0
    assert result[0].height_source == "assumed"


def test_ground_level_part_keeps_its_own_height():
    from dataclasses import replace

    original = replace(fixture_building(), is_part=True, parent_id="way/2")
    result, count = apply_asu_heights([original], [facility()])
    assert count == 0
    assert result[0] is original
