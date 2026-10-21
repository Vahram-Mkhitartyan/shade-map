"""Ground shadows cast by vertical polygon prisms in local metric space."""

from dataclasses import dataclass
from math import isfinite
from typing import Tuple

from shapely.affinity import translate
from shapely.geometry import GeometryCollection, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union


@dataclass(frozen=True)
class Building:
    """A vertical solid with a footprint, height and optional elevated base."""

    footprint: Polygon
    height_m: float
    min_height_m: float = 0.0

    def __post_init__(self) -> None:
        if self.footprint.is_empty or not self.footprint.is_valid:
            raise ValueError("Footprint must be a nonempty valid polygon")
        if (
            not all(
                isfinite(value) for value in (self.height_m, self.min_height_m)
            )
            or not 0 <= self.min_height_m < self.height_m
        ):
            raise ValueError("Require 0 <= base height < total height")

    def shadow(self, direction: Tuple[float, float, float]) -> BaseGeometry:
        """Project the solid along parallel sunlight rays onto z=0.

        Sweeping each boundary preserves concave outlines and courtyard holes.
        At night no cast polygon is returned; direct Sun is absent globally.
        """
        if len(direction) != 3 or not all(isfinite(v) for v in direction):
            raise ValueError("Sun direction needs three finite components")
        east, north, up = direction
        if not any(direction):
            raise ValueError("Sun direction must be nonzero")
        if up <= 0:
            return GeometryCollection()
        bottom_shift = (
            -self.min_height_m * east / up,
            -self.min_height_m * north / up,
        )
        top_shift = (-self.height_m * east / up, -self.height_m * north / up)
        pieces = [
            translate(
                self.footprint, xoff=bottom_shift[0], yoff=bottom_shift[1]
            ),
            translate(self.footprint, xoff=top_shift[0], yoff=top_shift[1]),
        ]
        for ring in [self.footprint.exterior, *self.footprint.interiors]:
            coordinates = list(ring.coords)
            for first, second in zip(coordinates, coordinates[1:]):
                swept = Polygon(
                    [
                        (
                            first[0] + bottom_shift[0],
                            first[1] + bottom_shift[1],
                        ),
                        (
                            second[0] + bottom_shift[0],
                            second[1] + bottom_shift[1],
                        ),
                        (second[0] + top_shift[0], second[1] + top_shift[1]),
                        (first[0] + top_shift[0], first[1] + top_shift[1]),
                    ]
                )
                if swept.area > 0:
                    pieces.append(swept)
        return unary_union(pieces)
