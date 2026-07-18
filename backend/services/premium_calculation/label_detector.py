"""Hybrid label detection: rule-based keywords + semantic embeddings."""

from typing import Dict, List, Optional

from backend.services.premium_calculation.cell_utils import clean_text
from backend.services.premium_calculation.config import PremiumExtractionConfig
from backend.services.premium_calculation.keyword_matcher import keyword_match_score
from backend.services.premium_calculation.semantic_matcher import get_semantic_matcher


def score_label_cell(
    cell: Dict,
    field_name: str,
    config: PremiumExtractionConfig,
) -> Dict:
    text = clean_text(cell.get("value", ""))

    if field_name == "total_sum_insured":
        keywords = config.sum_insured_keywords
        prototypes = config.sum_insured_prototypes
    else:
        keywords = config.premium_keywords
        prototypes = config.premium_prototypes

    rule_score, matched_keyword = keyword_match_score(text, keywords)

    matcher = get_semantic_matcher(config.embedding_model_name)
    semantic_score, matched_proto = matcher.best_similarity(text, prototypes)

    hybrid = (
        config.rule_weight * rule_score
        + config.semantic_weight * semantic_score
    )

    return {
        "row": cell["row"],
        "col": cell["col"],
        "value": text,
        "rule_score": rule_score,
        "semantic_score": semantic_score,
        "hybrid_score": hybrid,
        "matched_keyword": matched_keyword,
        "matched_prototype": matched_proto,
        "method": "hybrid",
    }


def find_best_label(
    cells: List[Dict],
    field_name: str,
    config: PremiumExtractionConfig,
) -> Optional[Dict]:
    """Select the highest-confidence label cell for a field."""

    best = None

    for cell in cells:
        # Skip pure numeric cells as labels
        if cell.get("numeric") is not None and not any(
            ch.isalpha() for ch in clean_text(cell.get("value", ""))
        ):
            continue

        scored = score_label_cell(cell, field_name, config)

        if scored["hybrid_score"] < config.min_label_confidence:
            continue

        if best is None or scored["hybrid_score"] > best["hybrid_score"]:
            best = scored

    return best
