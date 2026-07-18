"""Shared helpers for premium calculation cells."""

import re
from typing import Any, Dict, List, Optional, Tuple

from backend.utils.excel_helpers import column_number_to_excel


def cell_ref(row: int, col: int) -> str:
    return f"{column_number_to_excel(col)}{row}"


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "null"}:
        return ""
    return text


def parse_numeric(value: Any) -> Optional[float]:
    """
    Extract a numeric amount from a cell.

    Supports: 1,00,000 / 1,000,000.50 / Rs. 25000 / INR 12.5
    """
    text = clean_text(value)
    if not text:
        return None

    if not re.search(r"\d", text):
        return None

    # Strip currency markers, keep digits / separators
    cleaned = re.sub(r"(?i)rs\.?|inr|usd|₹|\$", " ", text)
    cleaned = cleaned.replace(" ", "")

    patterns = [
        # Indian / western grouped amounts with commas
        r"[-+]?\d{1,3}(?:,\d{2,3})+(?:\.\d+)?",
        # Plain integer or decimal (no comma grouping)
        r"[-+]?\d+(?:\.\d+)?",
    ]

    candidates = []
    for pattern in patterns:
        for match in re.finditer(pattern, cleaned):
            candidates.append(match.group(0))

    if not candidates:
        return None

    # Prefer the longest match (avoids splitting 500000 into 500 + 000)
    raw = max(candidates, key=lambda item: (len(item), item))
    raw = raw.replace(",", "")

    try:
        return float(raw)
    except ValueError:
        return None


def looks_like_amount(value: Any) -> float:
    """Heuristic 0..1 for whether a cell looks like a monetary amount."""
    text = clean_text(value)
    number = parse_numeric(value)
    if number is None:
        return 0.0

    score = 0.55
    if re.search(r"(?i)rs\.?|inr|₹|\$|usd", text):
        score += 0.25
    if "," in text:
        score += 0.10
    if re.search(r"\.\d{1,2}\b", text):
        score += 0.05
    # Prefer realistic positive amounts over tiny integers that may be codes
    if number >= 100:
        score += 0.05
    return min(score, 1.0)


def grid_to_cells(
    grid: List[List[Any]],
    start_row: int = 1,
    start_col: int = 1,
) -> List[Dict]:
    cells = []
    for r_idx, row in enumerate(grid or []):
        for c_idx, value in enumerate(row or []):
            text = clean_text(value)
            if not text:
                continue
            cells.append(
                {
                    "row": start_row + r_idx,
                    "col": start_col + c_idx,
                    "value": text,
                    "numeric": parse_numeric(text),
                }
            )
    return cells


def cells_list_to_cells(cells_input: List[Any]) -> List[Dict]:
    cells = []
    for item in cells_input or []:
        if hasattr(item, "model_dump"):
            item = item.model_dump()
        text = clean_text(item.get("value", ""))
        if not text:
            continue
        row = int(item["row"])
        col = int(item["col"])
        cells.append(
            {
                "row": row,
                "col": col,
                "value": text,
                "numeric": parse_numeric(text),
            }
        )
    return cells


def build_cell_index(cells: List[Dict]) -> Dict[Tuple[int, int], Dict]:
    return {(c["row"], c["col"]): c for c in cells}
