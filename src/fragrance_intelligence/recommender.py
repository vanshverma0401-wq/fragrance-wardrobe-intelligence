"""Explainable similarity recommendations within an owned wardrobe."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, Iterable, List, Tuple

from .inventory import CollectionItem


WEIGHTS = {
    "notes": 0.30,
    "family": 0.20,
    "season": 0.15,
    "occasion": 0.15,
    "longevity": 0.10,
    "projection": 0.10,
}


@dataclass(frozen=True)
class Recommendation:
    fragrance_id: str
    score: float
    reasons: Tuple[str, ...]
    components: Dict[str, float]


def _jaccard(left: FrozenSet[str], right: FrozenSet[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def _similarity(target: CollectionItem, candidate: CollectionItem) -> Recommendation:
    shared_notes = sorted(target.notes & candidate.notes)
    shared_seasons = sorted(target.seasons & candidate.seasons)
    shared_occasions = sorted(target.occasions & candidate.occasions)
    components = {
        "notes": _jaccard(target.notes, candidate.notes),
        "family": 1.0 if target.family == candidate.family else 0.0,
        "season": _jaccard(target.seasons, candidate.seasons),
        "occasion": _jaccard(target.occasions, candidate.occasions),
        "longevity": max(
            0.0, 1.0 - abs(target.longevity_hours - candidate.longevity_hours) / 12.0
        ),
        "projection": max(0.0, 1.0 - abs(target.projection - candidate.projection) / 4.0),
    }
    score = round(sum(components[name] * weight for name, weight in WEIGHTS.items()), 4)

    reasons: List[str] = []
    if shared_notes:
        reasons.append("shares notes: " + ", ".join(shared_notes))
    if components["family"] == 1.0:
        reasons.append(f"same {target.family} family")
    if shared_seasons:
        reasons.append("overlapping seasons: " + ", ".join(shared_seasons))
    if shared_occasions:
        reasons.append("overlapping occasions: " + ", ".join(shared_occasions))
    if components["longevity"] >= 0.75 and components["projection"] >= 0.75:
        reasons.append("similar longevity and projection profile")
    if not reasons:
        reasons.append("closest available profile under the documented heuristic")

    return Recommendation(
        fragrance_id=candidate.fragrance_id,
        score=score,
        reasons=tuple(reasons),
        components={name: round(value, 4) for name, value in sorted(components.items())},
    )


def similar_fragrances(
    target_id: str, collection: Iterable[CollectionItem], limit: int = 3
) -> List[Recommendation]:
    """Rank wardrobe alternatives by a documented, inspectable heuristic."""

    if limit <= 0:
        raise ValueError("limit must be greater than 0")

    items = list(collection)
    by_id = {item.fragrance_id: item for item in items}
    target = by_id.get(target_id)
    if target is None:
        raise ValueError(f"unknown target fragrance_id: {target_id}")

    ranked = [
        _similarity(target, candidate)
        for candidate in items
        if candidate.fragrance_id != target.fragrance_id
    ]
    return sorted(ranked, key=lambda entry: (-entry.score, entry.fragrance_id))[:limit]
