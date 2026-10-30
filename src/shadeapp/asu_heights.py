"""Match public ASU heights to OSM footprints using spatial overlap."""

from dataclasses import replace
from math import isfinite
from typing import List, Tuple

from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

from shadeapp.geodata import MapBuilding, to_local
from shadeapp.polygons import Building

SOURCE_URL = (
    "https://gisprodportal.asu.edu/server/rest/services/"
    "University_Facilities/FeatureServer/1"
)


def apply_asu_heights(
    buildings: List[MapBuilding], features: List[dict]
) -> Tuple[List[MapBuilding], int]:
    """Use ASU heights only for strong, unambiguous footprint matches.

    Require >=60% OSM coverage and intersection-over-union >=20%. Reject a
    runner-up with more than 80% of the best overlap. Keep elevated OSM
    parts unchanged: facility-wide heights cannot describe their vertical
    structure reliably. Feet convert to metres.
    """
    polygons, records = [], []
    for feature in features:
        attributes = feature.get("attributes", {})
        try:
            feet = float(attributes.get("BLDG_HEIGHT_FT") or 0)
        except (TypeError, ValueError):
            continue
        if not isfinite(feet) or not 0 < feet < 2000:
            continue
        outer, inner = [], []
        for ring in feature.get("geometry", {}).get("rings", []):
            polygon = Polygon([to_local(lon, lat) for lon, lat, *rest in ring])
            if polygon.is_empty or not polygon.is_valid:
                continue
            (inner if polygon.exterior.is_ccw else outer).append(polygon)
        if not outer:
            continue
        geometry = unary_union(outer).difference(unary_union(inner))
        if geometry.is_empty or not geometry.is_valid:
            continue
        polygons.append(geometry)
        records.append((feet * 0.3048, attributes))
    tree = STRtree(polygons)
    enriched, matches = [], 0
    for item in buildings:
        footprint = item.model.footprint
        if item.is_part or item.model.min_height_m > 0:
            enriched.append(item)
            continue
        candidates = []
        for index in tree.query(footprint, predicate="intersects"):
            overlap = footprint.intersection(polygons[index]).area
            coverage = overlap / footprint.area
            union_area = footprint.area + polygons[index].area - overlap
            if coverage >= 0.6 and overlap / union_area >= 0.2:
                candidates.append((coverage, int(index)))
        candidates.sort(reverse=True)
        if not candidates or (
            len(candidates) > 1 and candidates[1][0] >= candidates[0][0] * 0.8
        ):
            enriched.append(item)
            continue
        height, attributes = records[candidates[0][1]]
        reference = f"{SOURCE_URL} · OBJECTID {attributes.get('OBJECTID')}"
        enriched.append(
            replace(
                item,
                model=Building(footprint, height),
                height_source="asu",
                height_reference=reference,
            )
        )
        matches += 1
    return enriched, matches


def apply_height_overrides(
    buildings: List[MapBuilding], overrides: List[dict]
) -> Tuple[List[MapBuilding], int]:
    """Apply explicit, narrowly scoped height observations by OSM ID."""
    overrides_by_id = {item["osm_id"]: item for item in overrides}
    updated = []
    matches = 0
    for item in buildings:
        override = overrides_by_id.get(item.osm_id)
        if override is None:
            updated.append(item)
            continue
        height = float(override["height_m"])
        if not isfinite(height) or height <= item.model.min_height_m:
            raise ValueError(f"Invalid height override for {item.osm_id}")
        updated.append(
            replace(
                item,
                model=Building(
                    item.model.footprint,
                    height,
                    item.model.min_height_m,
                ),
                height_source=override["source"],
                height_reference=override["reference"],
            )
        )
        matches += 1
    return updated, matches
