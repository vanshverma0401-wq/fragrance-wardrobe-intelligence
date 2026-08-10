"""Collection data contract and CSV validation."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, FrozenSet, Iterable, List, Mapping, Union


PathLike = Union[str, Path]
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED_COLUMNS = {
    "fragrance_id",
    "house",
    "name",
    "family",
    "notes",
    "seasons",
    "occasions",
    "price_usd",
    "bottle_ml",
    "personal_rating",
    "longevity_hours",
    "projection",
}


class CollectionValidationError(ValueError):
    """Raised when a collection row does not satisfy the public data contract."""


@dataclass(frozen=True)
class CollectionItem:
    fragrance_id: str
    house: str
    name: str
    family: str
    notes: FrozenSet[str]
    seasons: FrozenSet[str]
    occasions: FrozenSet[str]
    price_usd: float
    bottle_ml: float
    personal_rating: float
    longevity_hours: float
    projection: int


def _text(row: Mapping[str, str], field: str, row_number: int) -> str:
    value = (row.get(field) or "").strip()
    if not value:
        raise CollectionValidationError(f"row {row_number}: {field} must not be empty")
    return value


def _tags(row: Mapping[str, str], field: str, row_number: int) -> FrozenSet[str]:
    value = (row.get(field) or "").strip()
    tags = frozenset(part.strip().lower() for part in value.split(";") if part.strip())
    if not tags:
        raise CollectionValidationError(f"row {row_number}: {field} must not be empty")
    return tags


def _float(row: Mapping[str, str], field: str, row_number: int) -> float:
    raw = (row.get(field) or "").strip()
    try:
        return float(raw)
    except ValueError as error:
        raise CollectionValidationError(
            f"row {row_number}: {field} must be numeric"
        ) from error


def _parse_item(row: Mapping[str, str], row_number: int) -> CollectionItem:
    fragrance_id = _text(row, "fragrance_id", row_number).lower()
    if not ID_PATTERN.fullmatch(fragrance_id):
        raise CollectionValidationError(
            f"row {row_number}: fragrance_id must use lowercase letters, numbers, and hyphens"
        )

    price_usd = _float(row, "price_usd", row_number)
    bottle_ml = _float(row, "bottle_ml", row_number)
    personal_rating = _float(row, "personal_rating", row_number)
    longevity_hours = _float(row, "longevity_hours", row_number)
    projection_raw = _float(row, "projection", row_number)

    if price_usd <= 0:
        raise CollectionValidationError(
            f"row {row_number}: price_usd must be greater than 0"
        )
    if bottle_ml <= 0:
        raise CollectionValidationError(
            f"row {row_number}: bottle_ml must be greater than 0"
        )
    if not 0 <= personal_rating <= 10:
        raise CollectionValidationError(
            f"row {row_number}: personal_rating must be between 0 and 10"
        )
    if longevity_hours < 0:
        raise CollectionValidationError(
            f"row {row_number}: longevity_hours must be at least 0"
        )
    if not projection_raw.is_integer() or not 1 <= projection_raw <= 5:
        raise CollectionValidationError(
            f"row {row_number}: projection must be an integer between 1 and 5"
        )

    return CollectionItem(
        fragrance_id=fragrance_id,
        house=_text(row, "house", row_number),
        name=_text(row, "name", row_number),
        family=_text(row, "family", row_number).lower(),
        notes=_tags(row, "notes", row_number),
        seasons=_tags(row, "seasons", row_number),
        occasions=_tags(row, "occasions", row_number),
        price_usd=price_usd,
        bottle_ml=bottle_ml,
        personal_rating=personal_rating,
        longevity_hours=longevity_hours,
        projection=int(projection_raw),
    )


def load_collection(path: PathLike) -> List[CollectionItem]:
    """Load and validate a collection CSV in its source order."""

    source = Path(path)
    with source.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_COLUMNS - columns)
        if missing:
            raise CollectionValidationError(
                "collection is missing required columns: " + ", ".join(missing)
            )

        items: List[CollectionItem] = []
        seen: Dict[str, int] = {}
        for row_number, row in enumerate(reader, start=2):
            item = _parse_item(row, row_number)
            if item.fragrance_id in seen:
                raise CollectionValidationError(
                    f"row {row_number}: duplicate fragrance_id {item.fragrance_id!r}; "
                    f"first seen on row {seen[item.fragrance_id]}"
                )
            seen[item.fragrance_id] = row_number
            items.append(item)

    if not items:
        raise CollectionValidationError("collection must contain at least one item")
    return items
