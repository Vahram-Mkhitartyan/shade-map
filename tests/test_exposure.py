"""Behavioral checks for traversal-time exposure sampling."""

from datetime import datetime, timedelta, timezone

import pytest

from shadeapp.exposure import evaluate_route
from shadeapp.geometry import AABB

DEPARTURE = datetime(2026, 6, 21, tzinfo=timezone.utc)


def test_empty_scene_is_sunny_and_night_has_no_direct_sun():
    sunny = evaluate_route(
        [(0, 0), (10, 0)],
        DEPARTURE,
        [],
        lambda timestamp: (0, 0, 1),
        walking_speed=1,
    )
    night = evaluate_route(
        [(0, 0), (10, 0)],
        DEPARTURE,
        [],
        lambda timestamp: (0, 0, -1),
        walking_speed=1,
    )
    assert sunny.sunny_seconds == pytest.approx(10)
    assert sunny.shade_fraction == 0
    assert night.sunny_seconds == 0
    assert night.shade_fraction == 1


def test_arrival_time_changes_exposure():
    observations = []

    def changing_sun(timestamp):
        observations.append(timestamp)
        return (
            (0, 0, 1)
            if timestamp < DEPARTURE + timedelta(seconds=5)
            else (0, 0, -1)
        )

    result = evaluate_route(
        [(0, 0), (10, 0)],
        DEPARTURE,
        [],
        changing_sun,
        walking_speed=1,
        sample_spacing=1,
    )
    assert result.sunny_seconds == pytest.approx(5)
    assert observations[0] == DEPARTURE + timedelta(seconds=0.5)
    assert observations[-1] == DEPARTURE + timedelta(seconds=9.5)


def test_building_shades_route_and_segment_lengths_are_weighted():
    building = AABB((0, 1, 0), (20, 5, 30))
    result = evaluate_route(
        [(0, 0), (1, 0), (10, 0)],
        DEPARTURE,
        [building],
        lambda timestamp: (0, 1, 1),
        walking_speed=1,
    )
    assert result.distance_m == 10
    assert result.sunny_seconds == 0


@pytest.mark.parametrize("speed", [0, -1, float("nan")])
def test_invalid_speed_rejected(speed):
    with pytest.raises(ValueError):
        evaluate_route(
            [(0, 0), (10, 0)],
            DEPARTURE,
            [],
            lambda timestamp: (0, 0, 1),
            walking_speed=speed,
        )
