"""Locate numeric values near an identified label cell."""

from typing import Dict, List, Optional, Tuple

from backend.services.premium_calculation.cell_utils import (
    build_cell_index,
    clean_text,
    looks_like_amount,
    parse_numeric,
)
from backend.services.premium_calculation.config import PremiumExtractionConfig


def _manhattan(a_row: int, a_col: int, b_row: int, b_col: int) -> int:
    return abs(a_row - b_row) + abs(a_col - b_col)


def _classify_direction(
    label_row: int,
    label_col: int,
    value_row: int,
    value_col: int,
) -> str:
    if value_row == label_row and value_col == label_col:
        return "same_cell"
    if value_row == label_row and value_col > label_col:
        return "right"
    if value_row == label_row and value_col < label_col:
        return "left"
    if value_col == label_col and value_row > label_row:
        return "below"
    if value_col == label_col and value_row < label_row:
        return "above"
    return "nearby"


def _context_score(
    label: Dict,
    candidate: Dict,
    field_name: str,
    cell_index: Dict[Tuple[int, int], Dict],
) -> float:
    """Boost when surrounding text reinforces the field type."""
    score = 0.0
    text = clean_text(candidate.get("value", "")).lower()
    label_text = clean_text(label.get("value", "")).lower()

    if field_name == "premium":
        tokens = ("premium", "prem", "rate")
    else:
        tokens = ("sum insured", "tsi", "insured", "si")

    if any(t in text for t in tokens):
        score += 0.35
    if any(t in label_text for t in tokens):
        score += 0.25

    # Neighbor labels around the candidate
    for dr, dc in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        neighbor = cell_index.get((candidate["row"] + dr, candidate["col"] + dc))
        if not neighbor:
            continue
        ntext = clean_text(neighbor.get("value", "")).lower()
        if any(t in ntext for t in tokens):
            score += 0.15

    return min(score, 1.0)


def _collect_candidates(
    label: Dict,
    cells: List[Dict],
    config: PremiumExtractionConfig,
) -> List[Dict]:
    label_row = label["row"]
    label_col = label["col"]
    window = max(int(config.search_window), 1)
    cell_index = build_cell_index(cells)

    ordered_coords: List[Tuple[int, int, str]] = []

    # 1) Same cell
    ordered_coords.append((label_row, label_col, "same_cell"))

    # 2) Right / Left along the row
    for distance in range(1, window + 1):
        ordered_coords.append((label_row, label_col + distance, "right"))
    for distance in range(1, window + 1):
        ordered_coords.append((label_row, label_col - distance, "left"))

    # 3) Below / Above along the column
    for distance in range(1, window + 1):
        ordered_coords.append((label_row + distance, label_col, "below"))
    for distance in range(1, window + 1):
        ordered_coords.append((label_row - distance, label_col, "above"))

    # 4) Remaining nearby cells within the window (Chebyshev)
    nearby = []
    for cell in cells:
        r, c = cell["row"], cell["col"]
        if max(abs(r - label_row), abs(c - label_col)) > window:
            continue
        if (r, c) == (label_row, label_col):
            continue
        if r == label_row or c == label_col:
            continue
        nearby.append((r, c, "nearby"))

    nearby.sort(key=lambda item: _manhattan(label_row, label_col, item[0], item[1]))
    ordered_coords.extend(nearby)

    seen = set()
    candidates = []

    for row, col, preferred_direction in ordered_coords:
        key = (row, col)
        if key in seen:
            continue
        seen.add(key)

        cell = cell_index.get(key)
        if not cell:
            # Same-cell may need parsing even when index uses cleaned value
            continue

        number = cell.get("numeric")
        if number is None:
            number = parse_numeric(cell.get("value"))
        if number is None:
            continue

        direction = _classify_direction(label_row, label_col, row, col)
        # Keep the preferred primary-direction tag when on-axis
        if preferred_direction in {"same_cell", "right", "left", "below", "above"}:
            direction = preferred_direction

        candidates.append(
            {
                "row": row,
                "col": col,
                "value": cell.get("value"),
                "numeric": number,
                "direction": direction,
                "distance": _manhattan(label_row, label_col, row, col),
            }
        )

    return candidates


def rank_value_candidates(
    label: Dict,
    candidates: List[Dict],
    field_name: str,
    cells: List[Dict],
    config: PremiumExtractionConfig,
) -> Optional[Dict]:
    if not candidates:
        return None

    cell_index = build_cell_index(cells)
    max_distance = max((c["distance"] for c in candidates), default=1) or 1
    best = None

    for candidate in candidates:
        distance_score = 1.0 - (candidate["distance"] / max_distance)
        direction_score = config.direction_weights.get(candidate["direction"], 0.4)
        format_score = looks_like_amount(candidate.get("value"))
        context = _context_score(label, candidate, field_name, cell_index)

        total = (
            config.distance_weight * distance_score
            + config.direction_weight * direction_score
            + config.format_weight * format_score
            + config.context_weight * context
        )

        scored = {
            **candidate,
            "distance_score": distance_score,
            "direction_score": direction_score,
            "format_score": format_score,
            "context_score": context,
            "value_score": total,
        }

        if best is None or scored["value_score"] > best["value_score"]:
            best = scored

    return best


def find_value_for_label(
    label: Dict,
    cells: List[Dict],
    field_name: str,
    config: PremiumExtractionConfig,
) -> Optional[Dict]:
    candidates = _collect_candidates(label, cells, config)
    return rank_value_candidates(label, candidates, field_name, cells, config)
