"""Deterministic collection and wear-log analytics."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date
from typing import Dict, Iterable, List, Optional, Union

from .inventory import CollectionItem
from .wear_log import WearEntry


Metric = Union[int, float]


@dataclass(frozen=True)
class NeglectStatus:
    fragrance_id: str
    last_worn: Optional[date]
    days_since_worn: Optional[int]
    reason: str


def wear_counts(entries: Iterable[WearEntry]) -> Dict[str, int]:
    """Count logged wears by fragrance identifier."""

    return dict(sorted(Counter(entry.fragrance_id for entry in entries).items()))


def cost_per_logged_wear(
    collection: Iterable[CollectionItem], entries: Iterable[WearEntry]
) -> Dict[str, Optional[float]]:
    """Return purchase price divided by logged wears, or None when unworn."""

    counts = wear_counts(entries)
    result: Dict[str, Optional[float]] = {}
    for item in sorted(collection, key=lambda entry: entry.fragrance_id):
        count = counts.get(item.fragrance_id, 0)
        result[item.fragrance_id] = round(item.price_usd / count, 2) if count else None
    return result


def collection_coverage(
    collection: Iterable[CollectionItem],
) -> Dict[str, Dict[str, int]]:
    """Count collection coverage across families, seasons, and occasions."""

    families: Counter[str] = Counter()
    seasons: Counter[str] = Counter()
    occasions: Counter[str] = Counter()
    for item in collection:
        families[item.family] += 1
        seasons.update(item.seasons)
        occasions.update(item.occasions)
    return {
        "families": dict(sorted(families.items())),
        "seasons": dict(sorted(seasons.items())),
        "occasions": dict(sorted(occasions.items())),
    }


def rotation_summary(
    collection: Iterable[CollectionItem], entries: Iterable[WearEntry]
) -> Dict[str, Metric]:
    """Summarize how much of the collection appears in the supplied wear log."""

    items = list(collection)
    collection_ids = {item.fragrance_id for item in items}
    worn_ids = {entry.fragrance_id for entry in entries} & collection_ids
    collection_size = len(collection_ids)
    return {
        "collection_size": collection_size,
        "worn_unique": len(worn_ids),
        "unworn_unique": collection_size - len(worn_ids),
        "rotation_rate": round(len(worn_ids) / collection_size, 4)
        if collection_size
        else 0.0,
    }


def neglected_fragrances(
    collection: Iterable[CollectionItem],
    entries: Iterable[WearEntry],
    *,
    as_of: date,
    threshold_days: int = 30,
) -> List[NeglectStatus]:
    """Find unworn items and items not worn within a configurable threshold."""

    if threshold_days < 0:
        raise ValueError("threshold_days must be at least 0")

    last_worn: Dict[str, date] = {}
    for entry in entries:
        previous = last_worn.get(entry.fragrance_id)
        if previous is None or entry.worn_on > previous:
            last_worn[entry.fragrance_id] = entry.worn_on

    result: List[NeglectStatus] = []
    for item in collection:
        last_date = last_worn.get(item.fragrance_id)
        if last_date is None:
            result.append(
                NeglectStatus(
                    fragrance_id=item.fragrance_id,
                    last_worn=None,
                    days_since_worn=None,
                    reason="no logged wears",
                )
            )
            continue

        days = (as_of - last_date).days
        if days >= threshold_days:
            result.append(
                NeglectStatus(
                    fragrance_id=item.fragrance_id,
                    last_worn=last_date,
                    days_since_worn=days,
                    reason=f"not worn in {days} days",
                )
            )

    return sorted(
        result,
        key=lambda entry: (
            entry.last_worn is not None,
            -(entry.days_since_worn or 0),
            entry.fragrance_id,
        ),
    )
