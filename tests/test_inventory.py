from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fragrance_intelligence.inventory import CollectionValidationError, load_collection


HEADER = (
    "fragrance_id,house,name,family,notes,seasons,occasions,price_usd,"
    "bottle_ml,personal_rating,longevity_hours,projection\n"
)


def write_csv(body: str) -> Path:
    handle = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
    handle.write(HEADER)
    handle.write(body)
    handle.close()
    return Path(handle.name)


class CollectionInventoryTests(unittest.TestCase):
    def tearDown(self) -> None:
        for path in getattr(self, "temporary_paths", []):
            path.unlink(missing_ok=True)

    def temporary_csv(self, body: str) -> Path:
        path = write_csv(body)
        self.temporary_paths = getattr(self, "temporary_paths", []) + [path]
        return path

    def test_loads_and_normalizes_a_valid_collection(self) -> None:
        path = self.temporary_csv(
            "demo-01,Northstar Atelier,Glacier Current,Fresh Aromatic,"
            '"Bergamot; Juniper; Musk","Spring; SUMMER",'
            '"Daily; Office",120,100,8.5,7.0,3\n'
        )

        items = load_collection(path)

        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item.fragrance_id, "demo-01")
        self.assertEqual(item.family, "fresh aromatic")
        self.assertEqual(item.notes, frozenset({"bergamot", "juniper", "musk"}))
        self.assertEqual(item.seasons, frozenset({"spring", "summer"}))
        self.assertEqual(item.occasions, frozenset({"daily", "office"}))
        self.assertEqual(item.price_usd, 120.0)
        self.assertEqual(item.projection, 3)

    def test_rejects_duplicate_identifiers(self) -> None:
        row = (
            "demo-01,Northstar Atelier,Glacier Current,Fresh Aromatic,"
            '"Bergamot;Juniper","Spring;Summer","Daily;Office",'
            "120,100,8.5,7.0,3\n"
        )
        path = self.temporary_csv(row + row)

        with self.assertRaisesRegex(CollectionValidationError, "duplicate fragrance_id"):
            load_collection(path)

    def test_rejects_nonpositive_price_or_bottle_size(self) -> None:
        path = self.temporary_csv(
            "demo-01,Northstar Atelier,Glacier Current,Fresh Aromatic,"
            '"Bergamot;Juniper","Spring;Summer","Daily;Office",'
            "0,100,8.5,7.0,3\n"
        )

        with self.assertRaisesRegex(CollectionValidationError, "price_usd must be greater than 0"):
            load_collection(path)

    def test_rejects_rating_or_projection_outside_bounds(self) -> None:
        path = self.temporary_csv(
            "demo-01,Northstar Atelier,Glacier Current,Fresh Aromatic,"
            '"Bergamot;Juniper","Spring;Summer","Daily;Office",'
            "120,100,10.5,7.0,6\n"
        )

        with self.assertRaisesRegex(CollectionValidationError, "personal_rating must be between 0 and 10"):
            load_collection(path)

    def test_requires_at_least_one_note_season_and_occasion(self) -> None:
        path = self.temporary_csv(
            "demo-01,Northstar Atelier,Glacier Current,Fresh Aromatic,"
            ',"Spring;Summer","Daily;Office",120,100,8.5,7.0,3\n'
        )

        with self.assertRaisesRegex(CollectionValidationError, "notes must not be empty"):
            load_collection(path)


if __name__ == "__main__":
    unittest.main()
