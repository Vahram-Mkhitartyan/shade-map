"""Build a self-contained browser demo with precomputed Python geometry."""

import json
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import List, Tuple
from zoneinfo import ZoneInfo

from shadeapp.exposure import evaluate_route
from shadeapp.geometry import AABB
from shadeapp.solar import Sun

Point = Tuple[float, float]
ROOT = Path(__file__).resolve().parents[1]
BUILDINGS = [
    (55, 50, 100, 100, 22),
    (115, 50, 165, 100, 30),
    (180, 50, 225, 100, 18),
    (240, 50, 280, 100, 26),
    (55, 130, 100, 180, 28),
    (115, 130, 165, 180, 16),
    (180, 130, 225, 180, 32),
    (240, 130, 280, 180, 23),
]
ROUTES = [
    {"name": "Central walk", "points": [(25, 115), (310, 115)]},
    {
        "name": "North walk",
        "points": [
            (25, 115),
            (40, 115),
            (40, 182),
            (295, 182),
            (295, 115),
            (310, 115),
        ],
    },
    {
        "name": "South walk",
        "points": [
            (25, 115),
            (40, 115),
            (40, 48),
            (295, 48),
            (295, 115),
            (310, 115),
        ],
    },
]
DAY = datetime(2026, 6, 21, tzinfo=ZoneInfo("America/Phoenix"))


def convex_hull(points: List[Point]) -> List[Point]:
    """Return a convex hull for a box footprint and its projected roof."""
    ordered = sorted(set(points))

    def cross(origin: Point, first: Point, second: Point) -> float:
        return (first[0] - origin[0]) * (second[1] - origin[1]) - (
            first[1] - origin[1]
        ) * (second[0] - origin[0])

    lower: List[Point] = []
    upper: List[Point] = []
    for point in ordered:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    for point in reversed(ordered):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    return lower[:-1] + upper[:-1]


@lru_cache(maxsize=None)
def solar_at_minute(minute: int) -> Sun:
    """Cache solar state at one-minute intervals for this fixed demo day."""
    return Sun.at(33.4242, -111.9281, DAY + timedelta(minutes=minute))


def direction_at(timestamp: datetime) -> Tuple[float, float, float]:
    """Use nearest-minute solar direction; maximum timing error is 30 s."""
    minute = round((timestamp - DAY).total_seconds() / 60)
    return solar_at_minute(minute).direction


def build() -> None:
    """Embed departure-time frames into the offline HTML template."""
    boxes = [
        AABB((x1, y1, 0), (x2, y2, height))
        for x1, y1, x2, y2, height in BUILDINGS
    ]
    frames = []
    for minute in range(360, 1201, 15):
        sun = solar_at_minute(minute)
        shadows = []
        if sun.elevation_deg > 0:
            east, north, up = sun.direction
            for x1, y1, x2, y2, height in BUILDINGS:
                corners = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
                shifted = [
                    (x - height * east / up, y - height * north / up)
                    for x, y in corners
                ]
                shadows.append(convex_hull(corners + shifted))
        metrics = []
        for route in ROUTES:
            result = evaluate_route(
                route["points"],
                DAY + timedelta(minutes=minute),
                boxes,
                direction_at,
            )
            metrics.append(
                {
                    "distance": round(result.distance_m),
                    "duration": round(result.duration_s, 1),
                    "sunny": round(result.sunny_seconds, 1),
                    "shade": round(result.shade_fraction * 100),
                }
            )
        frames.append(
            {
                "minute": minute,
                "elevation": sun.elevation_deg,
                "shadows": shadows,
                "routes": metrics,
            }
        )
    payload = {"buildings": BUILDINGS, "routes": ROUTES, "frames": frames}
    template = (ROOT / "demo/template.html").read_text()
    destination = ROOT / "demo/index.html"
    destination.write_text(
        template.replace(
            "__DEMO_DATA__", json.dumps(payload, separators=(",", ":"))
        )
    )
    print(f"Built {destination} ({destination.stat().st_size:,} bytes)")


if __name__ == "__main__":
    build()
