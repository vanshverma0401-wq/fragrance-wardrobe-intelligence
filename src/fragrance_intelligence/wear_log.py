"""Wear-log data contract and CSV validation."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import FrozenSet, List, Mapping, Optional, Set, Union


PathLike = Union[str, Path]
REQUIRED_COLUMNS = {
    "wear_id",
    "worn_on",
    "fragrance_id",
    "season",
    "occasion",
    "sprays",
    "performance_rating",
    "satisfaction_rating",
}


class WearLogValidationError(ValueError):
    """Raised when a wear-log row is incomplete or inconsistent."""


@dataclass(frozen=True)
class WearEntry:
    wear_id: str
    worn_on: date
    fragrance_id: str
    season: str
    occasion: str
    sprays: int
    performance_rating: float
    satisfaction_rating: float


def _required(row: Mapping[str, str], field: str, row_number: int) -> str:
    value = (row.get(field) or "").strip()
    if not value:
        raise WearLogValidationError(f"row {row_number}: {field} must not be empty")
    return value


def _rating(row: Mapping[str, str], field: str, row_number: int) -> float:
    raw = _required(row, field, row_number)
    try:
        value = float(raw)
    except ValueError as error:
        raise WearLogValidationError(f"row {row_number}: {field} must be numeric") from error
    if not 0 <= value <= 10:
        raise WearLogValidationError(
            f"row {row_number}: {field} must be between 0 and 10"
        )
    return value


def load_wear_log(
    path: PathLike, valid_fragrance_ids: Optional[Set[str]] = None
) -> List[WearEntry]:
    """Load a wear log and optionally enforce collection referential integrity."""

    source = Path(path)
    with source.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_COLUMNS - columns)
        if missing:
            raise WearLogValidationError(
                "wear log is missing required columns: " + ", ".join(missing)
            )

        entries: List[WearEntry] = []
        seen: Set[str] = set()
        for row_number, row in enumerate(reader, start=2):
            wear_id = _required(row, "wear_id", row_number).lower()
            if wear_id in seen:
                raise WearLogValidationError(
                    f"row {row_number}: duplicate wear_id {wear_id!r}"
                )
            seen.add(wear_id)

            fragrance_id = _required(row, "fragrance_id", row_number).lower()
            if valid_fragrance_ids is not None and fragrance_id not in valid_fragrance_ids:
                raise WearLogValidationError(
                    f"row {row_number}: unknown fragrance_id {fragrance_id!r}"
                )

            try:
                worn_on = date.fromisoformat(_required(row, "worn_on", row_number))
            except ValueError as error:
                raise WearLogValidationError(
                    f"row {row_number}: worn_on must use YYYY-MM-DD"
                ) from error

            sprays_raw = _required(row, "sprays", row_number)
            try:
                sprays = int(sprays_raw)
            except ValueError as error:
                raise WearLogValidationError(
                    f"row {row_number}: sprays must be a positive integer"
                ) from error
            if sprays <= 0:
                raise WearLogValidationError(
                    f"row {row_number}: sprays must be a positive integer"
                )

            entries.append(
                WearEntry(
                    wear_id=wear_id,
                    worn_on=worn_on,
                    fragrance_id=fragrance_id,
                    season=_required(row, "season", row_number).lower(),
                    occasion=_required(row, "occasion", row_number).lower(),
                    sprays=sprays,
                    performance_rating=_rating(
                        row, "performance_rating", row_number
                    ),
                    satisfaction_rating=_rating(
                        row, "satisfaction_rating", row_number
                    ),
                )
            )

    return entries
