"""
Configurable settings for premium / sum-insured extraction.

Override via PremiumExtractRequest.config or environment later.
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class PremiumExtractionConfig:
    # Hybrid label score weights (must sum conceptually to ~1.0)
    rule_weight: float = 0.55
    semantic_weight: float = 0.45

    # Minimum hybrid score to accept a label cell
    min_label_confidence: float = 0.25

    # Nearby value search radius (in cells) beyond primary directions
    search_window: int = 3

    # Direction priority weights used when ranking value candidates
    direction_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "same_cell": 1.00,
            "right": 0.95,
            "left": 0.80,
            "below": 0.75,
            "above": 0.65,
            "nearby": 0.45,
        }
    )

    # Candidate ranking weights
    distance_weight: float = 0.35
    direction_weight: float = 0.30
    format_weight: float = 0.20
    context_weight: float = 0.15

    # Sentence embedding model for semantic matching
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Keyword dictionaries (case-insensitive, partial match)
    sum_insured_keywords: List[str] = field(
        default_factory=lambda: [
            "total sum insured",
            "sum insured",
            "tsi",
            "total si",
            "sum insured (inr)",
            "total sum insured (inr)",
            "insured value",
            "total insured value",
            "si amount",
            "sum insured amount",
        ]
    )

    premium_keywords: List[str] = field(
        default_factory=lambda: [
            "premium",
            "total premium",
            "net premium",
            "gross premium",
            "premium amount",
            "premium (inr)",
            "final premium",
            "payable premium",
            "premium payable",
            "od premium",
        ]
    )

    # Prototype phrases for semantic similarity
    sum_insured_prototypes: List[str] = field(
        default_factory=lambda: [
            "total sum insured",
            "sum insured amount",
            "total insured value",
            "TSI",
        ]
    )

    premium_prototypes: List[str] = field(
        default_factory=lambda: [
            "premium amount",
            "total premium",
            "gross premium payable",
            "net premium",
        ]
    )


DEFAULT_CONFIG = PremiumExtractionConfig()
