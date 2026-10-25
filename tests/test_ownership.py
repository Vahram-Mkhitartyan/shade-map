"""Ensure parts modify only their own parent building."""

from shapely.geometry import box

from shadeapp.geodata import MapBuilding, resolve_part_ownership
from shadeapp.polygons import Building


def item(identifier, footprint, base=0):
    return MapBuilding(
        Building(footprint, 20, base),
        identifier,
        identifier,
        "tagged",
        "test source",
    )


def test_ground_part_does_not_cut_neighboring_building():
    owner = item("way/1", box(0, 0, 10, 10))
    neighbor = item("way/2", box(8, 0, 18, 10))
    part = item("way/3", box(2, 2, 9, 8))
    result = resolve_part_ownership([owner, neighbor], [part], {})
    assert next(
        value for value in result if value.osm_id == "way/2"
    ).model.footprint.equals(neighbor.model.footprint)
    modified = next(value for value in result if value.osm_id == "way/1")
    assert modified.model.footprint.area == 58
    assert modified.height_reference == "test source"
    assert result[-1].parent_id == "way/1"
    assert result[-1].is_part


def test_elevated_part_keeps_lower_parent_volume():
    owner = item("way/1", box(0, 0, 10, 10))
    result = resolve_part_ownership(
        [owner], [item("way/2", box(2, 2, 8, 8), 5)], {}
    )
    assert result[0].model.footprint.equals(owner.model.footprint)
    assert result[-1].parent_id == "way/1"


def test_ambiguous_and_orphan_parts_never_cut_outlines():
    first = item("way/1", box(0, 0, 10, 10))
    second = item("way/2", box(0, 0, 10, 10))
    result = resolve_part_ownership(
        [first, second],
        [item("way/3", box(2, 2, 8, 8)), item("way/4", box(20, 20, 25, 25))],
        {},
    )
    assert result[0].model.footprint.area == 100
    assert result[1].model.footprint.area == 100
    assert result[-2].ownership == "ambiguous"
    assert result[-1].ownership == "orphan"


def test_explicit_relation_resolves_geometric_ambiguity():
    first = item("way/1", box(0, 0, 10, 10))
    second = item("way/2", box(0, 0, 10, 10))
    part = item("way/3", box(2, 2, 8, 8))
    result = resolve_part_ownership(
        [first, second], [part], {"way/3": {"way/1"}}
    )
    assert result[0].model.footprint.area == 64
    assert result[1].model.footprint.area == 100
    assert result[-1].ownership == "relation"
