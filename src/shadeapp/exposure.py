"""Sample direct sunlight along a local metric walking path."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from math import ceil, dist, isfinite
from typing import Callable, Iterable, Sequence, Tuple

from shadeapp.geometry import AABB, is_shaded

Point = Tuple[float, float]
Direction = Tuple[float, float, float]


@dataclass(frozen=True)
class RouteExposure:
    """Walking distance and direct sunlight duration, in metres and seconds."""

    distance_m: float
    duration_s: float
    sunny_seconds: float

    @property
    def shade_fraction(self) -> float:
        """Return the fraction of traversal time without direct sunlight."""
        if self.duration_s == 0:
            return 0.0
        return 1 - self.sunny_seconds / self.duration_s


def evaluate_route(
    points: Sequence[Point],
    departure: datetime,
    obstacles: Iterable[AABB],
    sun_direction_at: Callable[[datetime], Direction],
    walking_speed: float = 1.4,
    sample_spacing: float = 2.0,
) -> RouteExposure:
    """Sample each segment at midpoint arrival times, without waiting.

    Points use East/North metres on flat ground. Each sample represents an
    equal-distance part of its segment, so short segments retain proper weight.
    """
    if departure.tzinfo is None or departure.utcoffset() is None:
        raise ValueError("Departure must be timezone-aware")
    if not all(
        isfinite(value) and value > 0
        for value in (walking_speed, sample_spacing)
    ):
        raise ValueError("Walking speed and sample spacing must be positive")
    if len(points) < 2:
        raise ValueError("A route needs at least two points")
    if any(
        len(point) != 2 or not all(isfinite(v) for v in point)
        for point in points
    ):
        raise ValueError("Route points must contain two finite coordinates")

    buildings = tuple(obstacles)
    distance_m = 0.0
    sunny_seconds = 0.0
    for start, end in zip(points, points[1:]):
        segment_length = dist(start, end)
        sample_count = max(1, ceil(segment_length / sample_spacing))
        sample_length = segment_length / sample_count
        for index in range(sample_count):
            fraction = (index + 0.5) / sample_count
            point = (
                start[0] + fraction * (end[0] - start[0]),
                start[1] + fraction * (end[1] - start[1]),
                0.0,
            )
            arrival = departure + timedelta(
                seconds=(distance_m + fraction * segment_length)
                / walking_speed
            )
            if not is_shaded(point, sun_direction_at(arrival), buildings):
                sunny_seconds += sample_length / walking_speed
        distance_m += segment_length
    return RouteExposure(distance_m, distance_m / walking_speed, sunny_seconds)
