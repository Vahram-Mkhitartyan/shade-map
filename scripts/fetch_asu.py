"""Cache public roofline and height records from ASU's campus map layer."""

import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

from shadeapp.asu_heights import SOURCE_URL

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Fetch a bounded query; reject errors or truncated results."""
    parameters = {
        "where": "1=1",
        "geometry": "-111.958,33.398,-111.898,33.449",
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "*",
        "outSR": "4326",
        "f": "json",
    }
    with urlopen(
        SOURCE_URL + "/query?" + urlencode(parameters), timeout=60
    ) as response:
        data = json.load(response)
    if data.get("error") or data.get("exceededTransferLimit"):
        raise RuntimeError("ASU query failed or exceeded its transfer limit")
    if not data.get("features"):
        raise RuntimeError("ASU query returned no facilities")
    cache = ROOT / ".cache"
    cache.mkdir(exist_ok=True)
    temporary = cache / "asu-facilities.json.tmp"
    temporary.write_text(json.dumps(data))
    temporary.replace(cache / "asu-facilities.json")
    print(f"Cached {len(data['features'])} ASU facility records")


if __name__ == "__main__":
    main()
