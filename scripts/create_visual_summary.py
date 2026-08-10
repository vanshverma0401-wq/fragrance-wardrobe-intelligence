"""Render the recruiter-facing summary from the public synthetic demo inputs."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fragrance_intelligence.analytics import (  # noqa: E402
    collection_coverage,
    cost_per_logged_wear,
    rotation_summary,
)
from fragrance_intelligence.inventory import load_collection  # noqa: E402
from fragrance_intelligence.wear_log import load_wear_log  # noqa: E402


WIDTH = 1600
HEIGHT = 1000
BACKGROUND = "#F5F7FB"
CARD = "#FFFFFF"
INK = "#172033"
MUTED = "#667085"
GRID = "#DDE3EC"
BLUE = "#285E8E"
BLUE_LIGHT = "#DCEAF6"
GOLD = "#D39A2C"
GOLD_LIGHT = "#F6E8C6"


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = (
        (
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        )
        if bold
        else (
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        )
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def text(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int],
    value: str,
    *,
    size: int,
    color: str = INK,
    bold: bool = False,
    anchor: Optional[str] = None,
) -> None:
    draw.text(xy, value, fill=color, font=font(size, bold), anchor=anchor)


def card(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int]) -> None:
    draw.rounded_rectangle(box, radius=22, fill=CARD, outline=GRID, width=2)


def metric_card(
    draw: ImageDraw.ImageDraw,
    box: Tuple[int, int, int, int],
    value: str,
    label: str,
    note: str,
) -> None:
    card(draw, box)
    left, top, _, _ = box
    text(draw, (left + 28, top + 26), value, size=42, bold=True, color=BLUE)
    text(draw, (left + 28, top + 81), label, size=18, bold=True)
    text(draw, (left + 28, top + 111), note, size=15, color=MUTED)


def format_money(value: float) -> str:
    return f"${value:,.2f}".replace(".00", "")


def render() -> Path:
    collection = load_collection(ROOT / "data" / "demo_collection.csv")
    by_id = {item.fragrance_id: item for item in collection}
    wears = load_wear_log(ROOT / "data" / "demo_wear_log.csv", set(by_id))
    rotation = rotation_summary(collection, wears)
    costs = cost_per_logged_wear(collection, wears)
    coverage = collection_coverage(collection)

    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)

    text(draw, (80, 58), "Fragrance Wardrobe Intelligence", size=42, bold=True)
    text(
        draw,
        (80, 116),
        "Synthetic demo snapshot • local-first Python analytics • as of 2026-08-10",
        size=20,
        color=MUTED,
    )

    metric_card(draw, (80, 176, 420, 326), "8", "Fictional bottles", "Public demo collection")
    metric_card(draw, (445, 176, 785, 326), "18", "Logged wears", "Synthetic event records")
    metric_card(
        draw,
        (810, 176, 1150, 326),
        f"{rotation['rotation_rate']:.1%}",
        "Rotation rate",
        "7 of 8 appear in the log",
    )
    metric_card(draw, (1175, 176, 1520, 326), "1", "Unworn bottle", "No logged wear event")

    card(draw, (80, 364, 1030, 918))
    text(draw, (112, 398), "Purchase cost per logged wear", size=25, bold=True)
    text(
        draw,
        (112, 435),
        "Purchase price ÷ logged wears • seven worn demo items • USD",
        size=16,
        color=MUTED,
    )

    ranked = sorted(
        ((fragrance_id, value) for fragrance_id, value in costs.items() if value is not None),
        key=lambda entry: (-entry[1], by_id[entry[0]].name),
    )
    max_value = max(value for _, value in ranked)
    label_x = 112
    bar_x = 370
    bar_width = 530
    value_x = 940
    first_y = 500
    row_gap = 57
    for index, (fragrance_id, value) in enumerate(ranked):
        y = first_y + index * row_gap
        item = by_id[fragrance_id]
        text(draw, (label_x, y + 14), item.name, size=17, bold=index == 0, anchor="lm")
        draw.rounded_rectangle(
            (bar_x, y, bar_x + bar_width, y + 28),
            radius=14,
            fill=BLUE_LIGHT,
        )
        filled = max(14, int(bar_width * value / max_value))
        draw.rounded_rectangle(
            (bar_x, y, bar_x + filled, y + 28),
            radius=14,
            fill=GOLD if index == 0 else BLUE,
        )
        text(
            draw,
            (value_x, y + 14),
            format_money(value),
            size=17,
            bold=True,
            anchor="rm",
            color=GOLD if index == 0 else INK,
        )

    card(draw, (1060, 364, 1520, 670))
    text(draw, (1092, 398), "Declared season coverage", size=24, bold=True)
    text(draw, (1092, 435), "Number of demo bottles tagged for each season", size=15, color=MUTED)
    season_order = ["spring", "summer", "fall", "winter"]
    season_max = max(coverage["seasons"].get(season, 0) for season in season_order)
    for index, season in enumerate(season_order):
        value = coverage["seasons"].get(season, 0)
        y = 488 + index * 43
        text(draw, (1092, y + 11), season.title(), size=16, anchor="lm")
        draw.rounded_rectangle((1192, y, 1428, y + 22), radius=11, fill=GOLD_LIGHT)
        filled = int(236 * value / season_max) if season_max else 0
        draw.rounded_rectangle((1192, y, 1192 + filled, y + 22), radius=11, fill=GOLD)
        text(draw, (1472, y + 11), str(value), size=16, bold=True, anchor="rm")

    card(draw, (1060, 700, 1520, 918))
    text(draw, (1092, 736), "Usage exception", size=22, bold=True, color=GOLD)
    text(draw, (1092, 782), "Velvet Signal", size=27, bold=True)
    text(draw, (1092, 824), "No logged wears in the synthetic demo.", size=17, color=MUTED)
    text(draw, (1092, 857), "The metric reports null—not $0—for cost per wear.", size=15, color=MUTED)

    text(
        draw,
        (80, 962),
        "Portfolio demonstration only • fictional products and events • no consumer or preference outcome is claimed",
        size=15,
        color=MUTED,
    )

    output = ROOT / "assets" / "wardrobe-intelligence-summary.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=True)
    return output


if __name__ == "__main__":
    print(render())
