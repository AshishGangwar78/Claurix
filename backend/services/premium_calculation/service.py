"""Service layer entrypoint for premium calculation extraction."""

from typing import Any, Dict, List, Optional

from backend.services.premium_calculation.extractor import extract_premiums_from_blocks


def extract_premium_values(
    blocks: List[Dict[str, Any]],
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Extract Total Sum Insured and Premium from one or more policy blocks.

    Returns a response payload ready for the API layer.
    """
    results = extract_premiums_from_blocks(blocks, config_overrides=config)

    return {
        "status": "success",
        "results": results,
    }
