import pytest

from shadeapp.geometry import AABB, is_shaded


def test_tall_building_blocks_but_short_building_does_not():
    # A 45-degree eastward ray reaches x=10 at z=10.
    tall = AABB((10, -5, 0), (20, 5, 30))
    short = AABB((10, -5, 0), (20, 5, 5))
    assert is_shaded((0, 0, 0), (1, 0, 1), [tall])
    assert not is_shaded((0, 0, 0), (1, 0, 1), [short])


def test_building_behind_observer_does_not_block():
    box = AABB((-20, -5, 0), (-10, 5, 30))
    assert not is_shaded((0, 0, 0), (1, 0, 1), [box])


@pytest.mark.parametrize("direction", [(0, 0, -1), (1, 0, 0)])
def test_no_direct_sun_at_or_below_horizon(direction):
    assert is_shaded((0, 0, 0), direction, [])


def test_parallel_ray_outside_slab_and_empty_scene():
    box = AABB((10, 1, 0), (20, 5, 30))
    assert not box.intersects_ray((0, 0, 0), (1, 0, 1))
    assert not is_shaded((0, 0, 0), (0, 0, 1), [])


def test_analytical_shadow_boundary_for_ten_metre_box():
    box = AABB((0, -1, 0), (2, 1, 10))
    # At 45 degrees, western ground shadow extends exactly 10 m.
    assert is_shaded((-9.9, 0, 0), (1, 0, 1), [box])
    assert is_shaded((-10, 0, 0), (1, 0, 1), [box])
    assert not is_shaded((-10.1, 0, 0), (1, 0, 1), [box])


def test_boundary_outward_ray_and_inside_origin():
    box = AABB((0, 0, 0), (2, 2, 2))
    assert not box.intersects_ray((2, 1, 1), (1, 0, 0))
    assert box.intersects_ray((1, 1, 1), (1, 0, 0))


@pytest.mark.parametrize(
    "lo,hi",
    [
        ((0, 0, 0), (0, 1, 1)),
        ((2, 0, 0), (1, 1, 1)),
        ((0, 0, 0), (1, 1, float("inf"))),
    ],
)
def test_invalid_boxes_rejected(lo, hi):
    with pytest.raises(ValueError):
        AABB(lo, hi)


@pytest.mark.parametrize("direction", [(0, 0, 0), (float("nan"), 0, 1)])
def test_invalid_directions_rejected(direction):
    with pytest.raises(ValueError):
        is_shaded((0, 0, 0), direction, [])
