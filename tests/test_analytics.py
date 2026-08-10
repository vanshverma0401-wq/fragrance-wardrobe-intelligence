from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from fragrance_intelligence.analytics import (
    collection_coverage,
    cost_per_logged_wear,
    neglected_fragrances,
    rotation_summary,
    wear_counts,
)
from fragrance_intelligence.inventory import CollectionItem
from fragrance_intelligence.wear_log import WearLogValidationError, load_wear_log


WEAR_HEADER = (
    "wear_id,worn_on,fragrance_id,season,occasion,sprays,"
    "performance_rating,satisfaction_rating\n"
)


def item(
    fragrance_id: str,
    family: str,
    price: float,
    seasons: frozenset[str],
    occasions: frozenset[str],
) -> CollectionItem:
    return CollectionItem(
        fragrance_id=fragrance_id,
        house="Demo House",
        name=fragrance_id.title(),
        family=family,
        notes=frozenset({"cedar", "musk"}),
        seasons=seasons,
        occasions=occasions,
        price_usd=price,
        bottle_ml=100.0,
        personal_rating=8.0,
        longevity_hours=7.0,
        projection=3,
    )


class WardrobeAnalyticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.collection = [
            item(
                "fresh-01",
                "fresh aromatic",
                120.0,
                frozenset({"spring", "summer"}),
                frozenset({"daily", "office"}),
            ),
            item(
                "amber-02",
                "amber",
                90.0,
                frozenset({"fall", "winter"}),
                frozenset({"evening", "special occasion"}),
            ),
        ]
        self.temporary_paths: list[Path] = []

    def tearDown(self) -> None:
        for path in self.temporary_paths:
            path.unlink(missing_ok=True)

    def wear_csv(self, body: str) -> Path:
        handle = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
        handle.write(WEAR_HEADER)
        handle.write(body)
        handle.close()
        path = Path(handle.name)
        self.temporary_paths.append(path)
        return path

    def test_loads_wears_and_rejects_unknown_fragrance(self) -> None:
        valid = self.wear_csv(
            "wear-001,2026-08-01,fresh-01,summer,office,4,8.0,9.0\n"
        )
        wears = load_wear_log(valid, {item.fragrance_id for item in self.collection})
        self.assertEqual(wears[0].worn_on, date(2026, 8, 1))
        self.assertEqual(wears[0].occasion, "office")

        invalid = self.wear_csv(
            "wear-002,2026-08-02,missing-99,summer,office,4,8.0,9.0\n"
        )
        with self.assertRaisesRegex(WearLogValidationError, "unknown fragrance_id"):
            load_wear_log(invalid, {item.fragrance_id for item in self.collection})

    def test_wear_counts_and_cost_per_logged_wear(self) -> None:
        path = self.wear_csv(
            "wear-001,2026-08-01,fresh-01,summer,office,4,8.0,9.0\n"
            "wear-002,2026-08-05,fresh-01,summer,daily,3,7.5,8.5\n"
        )
        wears = load_wear_log(path, {item.fragrance_id for item in self.collection})

        self.assertEqual(wear_counts(wears), {"fresh-01": 2})
        self.assertEqual(
            cost_per_logged_wear(self.collection, wears),
            {"fresh-01": 60.0, "amber-02": None},
        )

    def test_collection_coverage_and_rotation(self) -> None:
        path = self.wear_csv(
            "wear-001,2026-08-01,fresh-01,summer,office,4,8.0,9.0\n"
        )
        wears = load_wear_log(path, {item.fragrance_id for item in self.collection})

        coverage = collection_coverage(self.collection)
        self.assertEqual(coverage["families"], {"amber": 1, "fresh aromatic": 1})
        self.assertEqual(
            coverage["seasons"],
            {"fall": 1, "spring": 1, "summer": 1, "winter": 1},
        )
        self.assertEqual(rotation_summary(self.collection, wears)["rotation_rate"], 0.5)

    def test_neglected_items_include_unworn_bottles(self) -> None:
        path = self.wear_csv(
            "wear-001,2026-08-01,fresh-01,summer,office,4,8.0,9.0\n"
        )
        wears = load_wear_log(path, {item.fragrance_id for item in self.collection})

        neglected = neglected_fragrances(
            self.collection,
            wears,
            as_of=date(2026, 8, 10),
            threshold_days=30,
        )

        self.assertEqual([entry.fragrance_id for entry in neglected], ["amber-02"])
        self.assertIsNone(neglected[0].last_worn)
        self.assertIsNone(neglected[0].days_since_worn)


if __name__ == "__main__":
    unittest.main()
