"""Orchestrate premium / sum-insured extraction for policy blocks."""

from dataclasses import asdict
from typing import Any, Dict, List, Optional

from backend.services.premium_calculation.cell_utils import (
    cell_ref,
    cells_list_to_cells,
    grid_to_cells,
)
from backend.services.premium_calculation.config import (
    DEFAULT_CONFIG,
    PremiumExtractionConfig,
)
from backend.services.premium_calculation.label_detector import find_best_label
from backend.services.premium_calculation.value_locator import find_value_for_label


def _merge_config(overrides: Optional[Dict[str, Any]]) -> PremiumExtractionConfig:
    if not overrides:
        return DEFAULT_CONFIG

    data = asdict(DEFAULT_CONFIG)
    for key, value in overrides.items():
        if value is not None and key in data:
            data[key] = value
    return PremiumExtractionConfig(**data)


def _empty_field_result() -> Dict[str, Any]:
    return {
        "value": None,
        "label_cell": None,
        "value_cell": None,
        "label_row": None,
        "label_col": None,
        "value_row": None,
        "value_col": None,
        "confidence": 0.0,
        "label_score": 0.0,
        "value_score": 0.0,
        "method": None,
    }


def _extract_field(
    cells: List[Dict],
    field_name: str,
    config: PremiumExtractionConfig,
) -> Dict[str, Any]:
    label = find_best_label(cells, field_name, config)
    if not label:
        return _empty_field_result()

    value = find_value_for_label(label, cells, field_name, config)

    label_score = float(label.get("hybrid_score", 0.0))
    value_score = float(value.get("value_score", 0.0)) if value else 0.0
    confidence = round((0.6 * label_score) + (0.4 * value_score), 4) if value else round(
        0.6 * label_score, 4
    )

    result = {
        "value": value.get("numeric") if value else None,
        "label_cell": cell_ref(label["row"], label["col"]),
        "value_cell": cell_ref(value["row"], value["col"]) if value else None,
        "label_row": label["row"],
        "label_col": label["col"],
        "value_row": value["row"] if value else None,
        "value_col": value["col"] if value else None,
        "confidence": confidence,
        "label_score": round(label_score, 4),
        "value_score": round(value_score, 4),
        "method": label.get("method"),
    }
    return result


def normalize_block_cells(block: Dict[str, Any]) -> List[Dict]:
    if block.get("cells"):
        return cells_list_to_cells(block["cells"])

    if block.get("grid") is not None:
        return grid_to_cells(
            block["grid"],
            start_row=int(block.get("start_row", 1) or 1),
            start_col=int(block.get("start_col", 1) or 1),
        )

    return []


def extract_premium_from_block(
    block: Dict[str, Any],
    config: Optional[PremiumExtractionConfig] = None,
) -> Dict[str, Any]:
    cfg = config or DEFAULT_CONFIG
    cells = normalize_block_cells(block)

    return {
        "policy_name": block.get("policy_name", ""),
        "sheet_name": block.get("sheet_name"),
        "total_sum_insured": _extract_field(cells, "total_sum_insured", cfg),
        "premium": _extract_field(cells, "premium", cfg),
    }


def extract_premiums_from_blocks(
    blocks: List[Dict[str, Any]],
    config_overrides: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    config = _merge_config(config_overrides)
    return [extract_premium_from_block(block, config) for block in blocks]
