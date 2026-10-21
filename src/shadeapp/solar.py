"""Solar angles and observer-to-Sun vectors in East/North/Up coordinates."""

from dataclasses import dataclass
from datetime import datetime
from math import cos, isfinite, radians, sin
from typing import Tuple

import pandas as pd
from pvlib.solarposition import get_solarposition

Vector = Tuple[float, float, float]


def direction_from_angles(azimuth_deg: float, elevation_deg: float) -> Vector:
    """Return a unit vector from angles in degrees, azimuth north-clockwise."""
    if not all(isfinite(angle) for angle in (azimuth_deg, elevation_deg)):
        raise ValueError("Solar angles must be finite")
    if not -90 <= elevation_deg <= 90:
        raise ValueError("Elevation must lie between -90 and 90 degrees")
    azimuth, elevation = radians(azimuth_deg), radians(elevation_deg)
    return (
        cos(elevation) * sin(azimuth),
        cos(elevation) * cos(azimuth),
        sin(elevation),
    )


@dataclass(frozen=True)
class Sun:
    """Solar state at a geographic location and a timezone-aware instant."""

    latitude: float
    longitude: float
    timestamp: datetime
    azimuth_deg: float
    elevation_deg: float
    direction: Vector

    @classmethod
    def at(
        cls, latitude: float, longitude: float, timestamp: datetime
    ) -> "Sun":
        """Calculate geometric solar position at a geographic location."""
        if not isfinite(latitude) or not -90 <= latitude <= 90:
            raise ValueError("Latitude must lie between -90 and 90 degrees")
        if not isfinite(longitude) or not -180 <= longitude <= 180:
            raise ValueError("Longitude must lie between -180 and 180 degrees")
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("Timestamp must be timezone-aware")
        position = get_solarposition(
            pd.DatetimeIndex([timestamp]), latitude, longitude
        )
        azimuth = float(position.iloc[0]["azimuth"])
        elevation = float(position.iloc[0]["elevation"])
        return cls(
            latitude=latitude,
            longitude=longitude,
            timestamp=timestamp,
            azimuth_deg=azimuth,
            elevation_deg=elevation,
            direction=direction_from_angles(azimuth, elevation),
        )
