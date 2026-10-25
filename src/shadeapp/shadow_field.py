"""Time-indexed building shadows, independent of graph search and rendering."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache
from typing import List, Optional

import numpy as np
from shapely.geometry import LineString
from shapely.geometry.base import BaseGeometry
from shapely.strtree import STRtree

from shadeapp.geodata import MapBuilding, solar_direction_to_grid
from shadeapp.solar import Sun


@dataclass
class ShadowState:
    """Solar state and indexed ground polygons at one model timestamp."""

    sun: Sun
    building_indices: List[int]
    polygons: List[BaseGeometry]
    tree: STRtree


class ShadowField:
    """Cache a fixed building scene separately from dynamic solar state."""

    def __init__(
        self,
        buildings: List[MapBuilding],
        day: datetime,
        view: BaseGeometry,
        latitude: float = 33.4242,
        longitude: float = -111.9281,
        covered_paths: Optional[List[LineString]] = None,
    ) -> None:
        if day.tzinfo is None or day.utcoffset() is None:
            raise ValueError("Shadow field requires a timezone-aware day")
        # Narrow centerline tolerance marks routing samples, not roof width.
        self.covered_tree = STRtree(
            [line.buffer(0.1) for line in (covered_paths or [])]
        )
        self.buildings = buildings
        self.day = day
        self.view = view
        self.latitude = latitude
        self.longitude = longitude
        self.bounds = np.array(
            [item.model.footprint.bounds for item in buildings]
        )
        self.heights = np.array([item.model.height_m for item in buildings])
        # Keep cached solar states local to this scene.
        self.state = lru_cache(maxsize=8)(self._state)

    def _state(self, minute: int) -> ShadowState:
        sun = Sun.at(
            self.latitude, self.longitude, self.day + timedelta(minutes=minute)
        )
        if sun.elevation_deg <= 0 or not self.buildings:
            return ShadowState(sun, [], [], STRtree([]))
        east, north, up = solar_direction_to_grid(sun.direction)
        dx, dy = -self.heights * east / up, -self.heights * north / up
        west, south, east_bound, north_bound = self.view.bounds
        relevant = np.flatnonzero(
            (
                np.minimum(self.bounds[:, 0], self.bounds[:, 0] + dx)
                <= east_bound
            )
            & (np.maximum(self.bounds[:, 2], self.bounds[:, 2] + dx) >= west)
            & (
                np.minimum(self.bounds[:, 1], self.bounds[:, 1] + dy)
                <= north_bound
            )
            & (np.maximum(self.bounds[:, 3], self.bounds[:, 3] + dy) >= south)
        )
        indices, polygons = [], []
        direction = solar_direction_to_grid(sun.direction)
        for index in relevant:
            polygon = self.buildings[index].model.shadow(direction)
            if polygon.intersects(self.view):
                indices.append(int(index))
                polygons.append(polygon)
        return ShadowState(sun, indices, polygons, STRtree(polygons))

    def blocked(self, samples: np.ndarray, minute: int) -> np.ndarray:
        """Return absence of direct Sun for an array of Shapely points."""
        state = self.state(minute)
        result = np.zeros(len(samples), dtype=bool)
        if state.sun.elevation_deg <= 0:
            result[:] = True
        elif len(samples):
            pairs = state.tree.query(samples, predicate="intersects")
            if pairs.size:
                result[pairs[0]] = True
        # MVP proxy: reported roof cover removes direct-sun cost along this
        # centerline. Side-entry sunlight needs roof dimensions to model.
        if len(samples):
            covered = self.covered_tree.query(samples, predicate="intersects")
            if covered.size:
                result[covered[0]] = True
        return result
