"""
Repository placeholder for persisting premium extraction results.

Filesystem / PostgreSQL persistence can be plugged in later without
changing the API or extraction service contracts.
"""

from typing import Any, Dict, List, Optional

from backend.repositories.base import BaseRepository


class PremiumRepository(BaseRepository):
    """Future store for premium / TSI extraction results per policy block."""

    def get_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("PostgreSQL PremiumRepository not implemented yet")

    def save(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("PostgreSQL PremiumRepository not implemented yet")

    def delete(self, entity_id: str) -> bool:
        raise NotImplementedError("PostgreSQL PremiumRepository not implemented yet")

    def save_extraction(
        self,
        user_id: str,
        case_id: str,
        policy_name: str,
        result: Dict[str, Any],
    ) -> str:
        raise NotImplementedError("PostgreSQL PremiumRepository not implemented yet")

    def list_extractions(
        self,
        user_id: str,
        case_id: str,
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError("PostgreSQL PremiumRepository not implemented yet")
