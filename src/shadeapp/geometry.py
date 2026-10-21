"""Flat-world synthetic obstacles. Coordinates and heights are local metres."""

from dataclasses import dataclass
from math import isfinite
from typing import Iterable, Tuple

Vector = Tuple[float, float, float]


def _validate_vector(value: Vector) -> Vector:
    """Convert a vector to three finite floating-point coordinates."""
    result = tuple(float(coordinate) for coordinate in value)
    if len(result) != 3 or not all(
        isfinite(coordinate) for coordinate in result
    ):
        raise ValueError("Expected three finite coordinates")
    return result


@dataclass(frozen=True)
class AABB:
    """Axis-aligned bounding box representing a closed solid obstacle.

    Tangent rays count as blocked. Zero-volume boxes are invalid.
    """

    min_corner: Vector
    max_corner: Vector

    def __post_init__(self) -> None:
        lower, upper = (
            _validate_vector(self.min_corner),
            _validate_vector(self.max_corner),
        )
        if any(minimum >= maximum for minimum, maximum in zip(lower, upper)):
            raise ValueError(
                "Every minimum must be strictly below its maximum"
            )
        object.__setattr__(self, "min_corner", lower)
        object.__setattr__(self, "max_corner", upper)

    def intersects_ray(self, origin: Vector, direction: Vector) -> bool:
        """Test P + t * direction for t > 0 using axis-aligned slabs.

        The direction need not be normalized.
        """
        origin, direction = (
            _validate_vector(origin),
            _validate_vector(direction),
        )
        if not any(direction):
            raise ValueError("Ray direction must be nonzero")
        nearest_distance = float("-inf")
        farthest_distance = float("inf")
        for position, component, minimum, maximum in zip(
            origin, direction, self.min_corner, self.max_corner
        ):
            if component == 0:
                if position < minimum or position > maximum:
                    return False
                continue
            # Intersect the ray intervals from each of the three axis slabs.
            entry_distance, exit_distance = sorted(
                (
                    (minimum - position) / component,
                    (maximum - position) / component,
                )
            )
            nearest_distance = max(nearest_distance, entry_distance)
            farthest_distance = min(farthest_distance, exit_distance)
            if nearest_distance > farthest_distance:
                return False
        return farthest_distance > 0 and farthest_distance >= max(
            nearest_distance, 0
        )


def is_shaded(
    point: Vector, sun_direction: Vector, obstacles: Iterable[AABB]
) -> bool:
    """True when direct Sun is absent (blocked or at/below the horizon).

    Points inside solid obstacles are blocked. This is not a thermal/UV model.
    """
    point, direction = _validate_vector(point), _validate_vector(sun_direction)
    if not any(direction):
        raise ValueError("Sun direction must be nonzero")
    if direction[2] <= 0:
        return True
    return any(
        obstacle.intersects_ray(point, direction) for obstacle in obstacles
    )
