"""Request/response schemas for premium calculation extraction."""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class CellInput(BaseModel):
    row: int = Field(..., description="1-based Excel row number")
    col: int = Field(..., description="1-based Excel column number")
    value: Any = ""


class PremiumBlockInput(BaseModel):
    policy_name: str
    sheet_name: Optional[str] = None
    # Optional origin when sending a dense grid (1-based Excel coords of grid[0][0])
    start_row: int = 1
    start_col: int = 1
    # Either a 2D grid of cell values...
    grid: Optional[List[List[Any]]] = None
    # ...or an explicit sparse cell list
    cells: Optional[List[CellInput]] = None


class PremiumExtractionConfigOverride(BaseModel):
    rule_weight: Optional[float] = None
    semantic_weight: Optional[float] = None
    min_label_confidence: Optional[float] = None
    search_window: Optional[int] = None
    distance_weight: Optional[float] = None
    direction_weight: Optional[float] = None
    format_weight: Optional[float] = None
    context_weight: Optional[float] = None
    sum_insured_keywords: Optional[List[str]] = None
    premium_keywords: Optional[List[str]] = None


class PremiumExtractRequest(BaseModel):
    blocks: List[PremiumBlockInput]
    config: Optional[PremiumExtractionConfigOverride] = None


class FieldExtractionResult(BaseModel):
    value: Optional[Union[float, int, str]] = None
    label_cell: Optional[str] = None
    value_cell: Optional[str] = None
    label_row: Optional[int] = None
    label_col: Optional[int] = None
    value_row: Optional[int] = None
    value_col: Optional[int] = None
    confidence: float = 0.0
    label_score: float = 0.0
    value_score: float = 0.0
    method: Optional[str] = None


class PremiumBlockResult(BaseModel):
    policy_name: str
    sheet_name: Optional[str] = None
    total_sum_insured: FieldExtractionResult
    premium: FieldExtractionResult


class PremiumExtractResponse(BaseModel):
    status: str = "success"
    results: List[PremiumBlockResult]
