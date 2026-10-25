"""Fetch a bounded OSM snapshot for ASU Tempe and neighboring streets."""

import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "https://overpass-api.de/api/interpreter"
# Extra building context beyond the smaller walking-network window.
QUERY = """[out:json][timeout:120];
(
  way["building"](33.398,-111.958,33.449,-111.898);
  relation["building"](33.398,-111.958,33.449,-111.898);
  relation["type"="building"](33.398,-111.958,33.449,-111.898);
  way["building:part"](33.398,-111.958,33.449,-111.898);
  way["highway"](33.404,-111.950,33.443,-111.905);
);
out body geom;"""


def main() -> None:
    """Download once, reject incomplete results, then cache outside Git."""
    request = Request(
        ENDPOINT,
        data=urlencode({"data": QUERY}).encode(),
        headers={"User-Agent": "ShadeAppPrototype/0.0.2 (local research)"},
    )
    with urlopen(request, timeout=180) as response:
        data = json.load(response)
    if data.get("remark") or not data.get("elements"):
        raise RuntimeError(data.get("remark", "Empty Overpass response"))
    cache = ROOT / ".cache"
    cache.mkdir(exist_ok=True)
    temporary = cache / "campus-osm.json.tmp"
    temporary.write_text(json.dumps(data))
    temporary.replace(cache / "campus-osm.json")
    print(f"Cached {len(data['elements'])} elements from {ENDPOINT}")
    print(data["osm3s"]["timestamp_osm_base"])


if __name__ == "__main__":
    main()
