from datetime import datetime, timezone
from math import sqrt
from zoneinfo import ZoneInfo

import pytest

from shadeapp.solar import Sun, direction_from_angles


@pytest.mark.parametrize(
    "azimuth,elevation,expected",
    [
        (0, 0, (0, 1, 0)),
        (90, 0, (1, 0, 0)),
        (180, 0, (0, -1, 0)),
        (270, 0, (-1, 0, 0)),
        (0, 90, (0, 0, 1)),
    ],
)
def test_axis_convention(azimuth, elevation, expected):
    assert direction_from_angles(azimuth, elevation) == pytest.approx(expected)


def test_sun_normalized_and_same_instant_invariant():
    local = datetime(2026, 6, 21, 12, tzinfo=ZoneInfo("America/Phoenix"))
    sun = Sun.at(33.4242, -111.9281, local)
    utc = Sun.at(33.4242, -111.9281, local.astimezone(timezone.utc))
    assert sqrt(sum(v * v for v in sun.direction)) == pytest.approx(1)
    assert sun.direction == pytest.approx(utc.direction)
    assert sun.elevation_deg > 70


def test_midnight_sun_below_horizon_in_tempe():
    sun = Sun.at(
        33.4242,
        -111.9281,
        datetime(2026, 6, 21, tzinfo=ZoneInfo("America/Phoenix")),
    )
    assert sun.elevation_deg < 0


def test_naive_time_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        Sun.at(33, -112, datetime(2026, 6, 21))


@pytest.mark.parametrize("lat,lon", [(91, 0), (0, -181), (float("nan"), 0)])
def test_invalid_location_rejected(lat, lon):
    with pytest.raises(ValueError):
        Sun.at(lat, lon, datetime(2026, 6, 21, tzinfo=timezone.utc))
