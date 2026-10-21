"""Run a synthetic building query at an illustrative ASU Tempe location."""

from datetime import datetime
from zoneinfo import ZoneInfo

from shadeapp.geometry import AABB, is_shaded
from shadeapp.solar import Sun


def main() -> None:
    """Print solar position and shade checks for a synthetic building."""
    departure_time = datetime(
        2026, 6, 21, 16, tzinfo=ZoneInfo("America/Phoenix")
    )
    sun = Sun.at(
        latitude=33.4242, longitude=-111.9281, timestamp=departure_time
    )
    building = AABB((-10, -10, 0), (10, 10, 20))
    print("shade app | synthetic geometry, not actual campus shade")
    print(f"Time: {sun.timestamp.isoformat()}")
    print(
        f"Sun: azimuth={sun.azimuth_deg:.2f}°, "
        f"elevation={sun.elevation_deg:.2f}°"
    )
    for point in [(20, 0, 0), (-20, 0, 0), (0, 30, 0)]:
        shaded = is_shaded(point, sun.direction, [building])
        print(f"Point {point} m ENU: shaded={shaded}")


if __name__ == "__main__":
    main()
