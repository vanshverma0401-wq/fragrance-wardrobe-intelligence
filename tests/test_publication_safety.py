from __future__ import annotations

import re
import unittest
from pathlib import Path

from fragrance_intelligence.inventory import load_collection
from fragrance_intelligence.wear_log import load_wear_log


ROOT = Path(__file__).resolve().parents[1]


def package_files() -> list[Path]:
    return sorted(path for path in ROOT.rglob("*") if path.is_file())


class PublicationSafetyTests(unittest.TestCase):
    def test_generated_python_artifacts_are_excluded(self) -> None:
        generated = [
            path.relative_to(ROOT)
            for path in package_files()
            if "__pycache__" in path.parts or path.suffix.lower() in {".pyc", ".pyo"}
        ]
        self.assertFalse(generated, generated)

    def test_required_publication_files_exist(self) -> None:
        required = {
            ROOT / "README.md",
            ROOT / "DATA_MODEL.md",
            ROOT / "DATA_AND_USAGE.md",
            ROOT / "METHODS_AND_LIMITATIONS.md",
            ROOT / "VISUAL_SUMMARY_DESIGN.md",
            ROOT / "LICENSE",
            ROOT / "assets" / "wardrobe-intelligence-summary.png",
            ROOT / "data" / "demo_collection.csv",
            ROOT / "data" / "demo_wear_log.csv",
            ROOT / "scripts" / "create_visual_summary.py",
        }
        self.assertFalse([path.relative_to(ROOT) for path in required if not path.is_file()])

    def test_readme_states_demo_and_claim_boundaries(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        required = {
            "synthetic demonstration data",
            "No cloud account is required",
            "cost per logged wear",
            "explainable heuristic",
            "does not predict personal preference",
            "not scraped from Fragrantica or Parfumo",
        }
        self.assertTrue(all(statement in readme for statement in required))
        self.assertIn(
            "assets/wardrobe-intelligence-summary.png",
            readme,
        )

    def test_visual_summary_is_a_reviewable_png(self) -> None:
        path = ROOT / "assets" / "wardrobe-intelligence-summary.png"
        header = path.read_bytes()[:24]
        self.assertEqual(header[:8], b"\x89PNG\r\n\x1a\n")
        width = int.from_bytes(header[16:20], "big")
        height = int.from_bytes(header[20:24], "big")
        self.assertEqual((width, height), (1600, 1000))
        self.assertLess(path.stat().st_size, 2_000_000)

    def test_demo_data_is_valid_and_referentially_consistent(self) -> None:
        collection = load_collection(ROOT / "data" / "demo_collection.csv")
        self.assertGreaterEqual(len(collection), 8)
        self.assertTrue(all(item.fragrance_id.startswith("demo-") for item in collection))
        wears = load_wear_log(
            ROOT / "data" / "demo_wear_log.csv",
            {item.fragrance_id for item in collection},
        )
        self.assertGreaterEqual(len(wears), 16)

    def test_no_private_paths_secrets_or_course_archives(self) -> None:
        patterns = {
            "private_path": re.compile(r"/(?:Users|Volumes|home)/[^\s`]+"),
            "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
            "access_key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
            "secret_assignment": re.compile(
                r"(?i)(api[_-]?key|client[_-]?secret|private[_-]?key)"
                r"\s*[:=]\s*['\"][^'\"]+"
            ),
            "canvas_archive": re.compile(r"(?i)canvas.{0,20}(submission|download|grade)"),
        }
        forbidden_suffixes = {".pdf", ".docx", ".pptx", ".zip", ".key", ".twb", ".twbx"}
        self.assertFalse(
            [path.relative_to(ROOT) for path in package_files() if path.suffix.lower() in forbidden_suffixes]
        )
        findings: list[str] = []
        for path in package_files():
            if path.name == "test_publication_safety.py" or path.suffix == ".pyc":
                continue
            content = path.read_text(encoding="utf-8", errors="ignore")
            for label, pattern in patterns.items():
                if pattern.search(content):
                    findings.append(f"{path.relative_to(ROOT)}: {label}")
        self.assertFalse(findings, findings)

    def test_markdown_links_resolve(self) -> None:
        missing: list[str] = []
        for markdown in ROOT.rglob("*.md"):
            content = markdown.read_text(encoding="utf-8")
            for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", content):
                if re.match(r"^[a-z]+://", target, re.I) or target.startswith("#"):
                    continue
                if not (markdown.parent / target.split("#", 1)[0]).is_file():
                    missing.append(f"{markdown.relative_to(ROOT)} -> {target}")
        self.assertFalse(missing, missing)


if __name__ == "__main__":
    unittest.main()
