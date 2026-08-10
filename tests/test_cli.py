from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from fragrance_intelligence.cli import main


COLLECTION = """fragrance_id,house,name,family,notes,seasons,occasions,price_usd,bottle_ml,personal_rating,longevity_hours,projection
fresh-01,Demo House,Fresh One,fresh aromatic,"bergamot;cedar","spring;summer","daily;office",120,100,8.5,7,3
amber-02,Demo House,Amber Two,amber,"amber;vanilla","fall;winter","evening;special occasion",90,75,8,9,4
"""

WEARS = """wear_id,worn_on,fragrance_id,season,occasion,sprays,performance_rating,satisfaction_rating
wear-001,2026-08-01,fresh-01,summer,office,4,8,9
wear-002,2026-08-05,fresh-01,summer,daily,3,7.5,8.5
"""


class CommandLineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.collection_path = root / "collection.csv"
        self.wear_path = root / "wears.csv"
        self.collection_path.write_text(COLLECTION, encoding="utf-8")
        self.wear_path.write_text(WEARS, encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_summary_emits_deterministic_json(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = main(
                [
                    "summary",
                    "--collection",
                    str(self.collection_path),
                    "--wear-log",
                    str(self.wear_path),
                    "--as-of",
                    "2026-08-10",
                    "--neglect-days",
                    "30",
                ]
            )

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["collection_size"], 2)
        self.assertEqual(payload["wear_log_entries"], 2)
        self.assertEqual(payload["rotation"]["rotation_rate"], 0.5)
        self.assertEqual(payload["cost_per_logged_wear"]["fresh-01"], 60.0)
        self.assertIsNone(payload["cost_per_logged_wear"]["amber-02"])
        self.assertEqual(payload["neglected"][0]["fragrance_id"], "amber-02")

    def test_similar_emits_explanations(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = main(
                [
                    "similar",
                    "--collection",
                    str(self.collection_path),
                    "--target",
                    "fresh-01",
                ]
            )

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["target"], "fresh-01")
        self.assertEqual(payload["recommendations"][0]["fragrance_id"], "amber-02")
        self.assertTrue(payload["recommendations"][0]["reasons"])


if __name__ == "__main__":
    unittest.main()
