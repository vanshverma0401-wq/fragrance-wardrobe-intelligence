"""Command-line interface for local wardrobe analysis."""

from __future__ import annotations

import argparse
import json
from datetime import date
from typing import Any, Dict, List, Optional

from .analytics import (
    collection_coverage,
    cost_per_logged_wear,
    neglected_fragrances,
    rotation_summary,
)
from .inventory import load_collection
from .recommender import similar_fragrances
from .wear_log import load_wear_log


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fragrance-intelligence",
        description="Analyze a local fragrance collection and wear log.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    summary = commands.add_parser("summary", help="emit a wardrobe summary as JSON")
    summary.add_argument("--collection", required=True)
    summary.add_argument("--wear-log", required=True)
    summary.add_argument("--as-of", required=True, help="analysis date in YYYY-MM-DD")
    summary.add_argument("--neglect-days", type=int, default=30)

    similar = commands.add_parser(
        "similar", help="rank explainable alternatives within the collection"
    )
    similar.add_argument("--collection", required=True)
    similar.add_argument("--target", required=True)
    similar.add_argument("--limit", type=int, default=3)
    return parser


def _summary(args: argparse.Namespace) -> Dict[str, Any]:
    collection = load_collection(args.collection)
    collection_ids = {item.fragrance_id for item in collection}
    entries = load_wear_log(args.wear_log, collection_ids)
    as_of = date.fromisoformat(args.as_of)
    neglected = neglected_fragrances(
        collection,
        entries,
        as_of=as_of,
        threshold_days=args.neglect_days,
    )
    return {
        "analysis_as_of": as_of.isoformat(),
        "collection_size": len(collection),
        "wear_log_entries": len(entries),
        "rotation": rotation_summary(collection, entries),
        "cost_per_logged_wear": cost_per_logged_wear(collection, entries),
        "coverage": collection_coverage(collection),
        "neglected": [
            {
                "fragrance_id": entry.fragrance_id,
                "last_worn": entry.last_worn.isoformat() if entry.last_worn else None,
                "days_since_worn": entry.days_since_worn,
                "reason": entry.reason,
            }
            for entry in neglected
        ],
    }


def _similar(args: argparse.Namespace) -> Dict[str, Any]:
    collection = load_collection(args.collection)
    recommendations = similar_fragrances(args.target, collection, args.limit)
    return {
        "target": args.target,
        "recommendations": [
            {
                "fragrance_id": entry.fragrance_id,
                "score": entry.score,
                "reasons": list(entry.reasons),
                "components": entry.components,
            }
            for entry in recommendations
        ],
    }


def main(argv: Optional[List[str]] = None) -> int:
    args = _parser().parse_args(argv)
    payload = _summary(args) if args.command == "summary" else _similar(args)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
