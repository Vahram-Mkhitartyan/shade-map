"""Pedestrian candidate search and time-dependent exposure evaluation."""

from math import ceil, dist, isfinite
from typing import Dict, List, Tuple

import networkx as nx
import numpy as np
from shapely import points as make_points

from shadeapp.indoor_passages import is_open
from shadeapp.shadow_field import ShadowField

WALKING_SPEED = 1.4
SOLAR_BIN_MINUTES = 5
MAX_DETOUR = 1.35


def sample_route(
    graph: nx.Graph,
    nodes: List[int],
    walking_speed: float = WALKING_SPEED,
    spacing: float = 3.0,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return weighted midpoint positions, cumulative metres and seconds."""
    if not all(
        isfinite(value) and value > 0 for value in (walking_speed, spacing)
    ):
        raise ValueError("Speed and sample spacing must be positive")
    samples, distances, weights = [], [], []
    travelled = 0.0
    for first, second in zip(nodes, nodes[1:]):
        start, end = graph.nodes[first]["point"], graph.nodes[second]["point"]
        length = dist(start, end)
        count = max(1, ceil(length / spacing))
        for index in range(count):
            fraction = (index + 0.5) / count
            samples.append(
                (
                    start[0] + (end[0] - start[0]) * fraction,
                    start[1] + (end[1] - start[1]) * fraction,
                )
            )
            distances.append(travelled + length * fraction)
            weights.append(length / count / walking_speed)
        travelled += length
    return (
        np.array(samples).reshape((-1, 2)),
        np.array(distances),
        np.array(weights),
    )


def score_route(
    graph: nx.Graph,
    nodes: List[int],
    departure: int,
    field: ShadowField,
) -> Dict[str, object]:
    """Advance time through each sample; score direct-sun walking seconds."""
    duration, sunny, distance = 0.0, 0.0, 0.0
    passages = set()
    for first, second in zip(nodes, nodes[1:]):
        data = graph[first][second]
        samples, distances, seconds = sample_route(graph, [first, second])
        delay = data.get("delay", 0)
        entry = departure + duration / 60
        traversal = float(seconds.sum()) + delay
        if data.get("schedule") and not is_open(
            data["schedule"],
            field.day.weekday(),
            entry,
            entry + traversal / 60,
        ):
            raise ValueError("Indoor passage closes during traversal")
        arrival_bins = (
            np.rint(
                (entry + (distances / WALKING_SPEED + delay / 2) / 60)
                / SOLAR_BIN_MINUTES
            )
            * SOLAR_BIN_MINUTES
        ).astype(int)
        shaded = np.zeros(len(samples), dtype=bool)
        for minute in np.unique(arrival_bins):
            indices = np.flatnonzero(arrival_bins == minute)
            shaded[indices] = field.blocked(
                make_points(samples[indices]), int(minute)
            )
        sunny += float(seconds[~shaded].sum())
        if len(shaded):
            sunny += delay * float((~shaded).mean())
        duration += traversal
        distance += data["length"]
        if data.get("passage"):
            passages.add(data["passage"])
    return {
        "duration": round(duration, 1),
        "sunny": round(sunny, 1),
        "distance": round(distance),
        "shade": round(100 * (1 - sunny / duration)) if duration else 0,
        "passages": sorted(passages),
    }


def candidate_paths(
    graph: nx.Graph,
    start: int,
    finish: int,
) -> List[List[int]]:
    """Generate bounded alternatives using preassigned sunny-length costs.

    Departure-time costs generate candidates; score_route evaluates arrival
    times afterwards. This is not globally optimal time-dependent routing.
    """

    def walking_cost(a: int, b: int, data: dict) -> float:
        return data["length"] + WALKING_SPEED * data.get("delay", 0)

    shortest = nx.shortest_path(graph, start, finish, weight=walking_cost)
    baseline = nx.path_weight(graph, shortest, "length")
    candidates = [shortest]
    for preference in (1, 3, 8):
        candidate = nx.shortest_path(
            graph,
            start,
            finish,
            weight=lambda a, b, data: (
                walking_cost(a, b, data) + preference * data["sunny_length"]
            ),
        )
        if (
            candidate not in candidates
            and nx.path_weight(graph, candidate, "length")
            <= baseline * MAX_DETOUR
        ):
            candidates.append(candidate)
    return candidates


def edge_samples(
    graph: nx.Graph, edges: list
) -> Tuple[np.ndarray, np.ndarray]:
    """Flatten 3 m spatial samples and return their owning edge indices."""
    points, owners = [], []
    for index, (first, second, _) in enumerate(edges):
        samples, _, _ = sample_route(graph, [first, second])
        points.extend(samples)
        owners.extend([index] * len(samples))
    return make_points(np.array(points)), np.array(owners)


def edge_sunlight(
    field: ShadowField,
    minute: int,
    samples: np.ndarray,
    owners: np.ndarray,
    edge_count: int,
) -> np.ndarray:
    """Return direct-sun fractions per edge at a specified solar state."""
    sunny = ~field.blocked(samples, minute)
    totals = np.bincount(owners, minlength=edge_count)
    sunny_counts = np.bincount(owners, weights=sunny, minlength=edge_count)
    return np.divide(
        sunny_counts, totals, out=np.zeros(edge_count), where=totals > 0
    )
