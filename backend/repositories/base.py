"""
Repository layer placeholders for future PostgreSQL integration.

Current persistence remains filesystem-based under backend/storage/.
These classes define the intended data-access surface so services can
swap file I/O for DB calls without changing endpoint contracts.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseRepository(ABC):
    """Base repository interface."""

    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def save(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        raise NotImplementedError


class PolicyRepository(BaseRepository):
    """
    Future PostgreSQL repository for per-company policy JSON results.

    Intended operations (filesystem today via file_service):
    - save_policy(user_id, case_id, company, policy_name, data)
    - get_policy(user_id, case_id, company, policy_name)
    - list_policies(user_id, case_id)
    """

    def get_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("PostgreSQL PolicyRepository not implemented yet")

    def save(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("PostgreSQL PolicyRepository not implemented yet")

    def delete(self, entity_id: str) -> bool:
        raise NotImplementedError("PostgreSQL PolicyRepository not implemented yet")

    def save_policy(
        self,
        user_id: str,
        case_id: str,
        company: str,
        policy_name: str,
        data: Dict[str, Any],
    ) -> str:
        raise NotImplementedError("PostgreSQL PolicyRepository not implemented yet")

    def list_policy_files(
        self,
        user_id: str,
        case_id: str,
        policy_name: str,
    ) -> List[str]:
        raise NotImplementedError("PostgreSQL PolicyRepository not implemented yet")


class CaseRepository(BaseRepository):
    """Future repository for case / upload session metadata."""

    def get_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("PostgreSQL CaseRepository not implemented yet")

    def save(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("PostgreSQL CaseRepository not implemented yet")

    def delete(self, entity_id: str) -> bool:
        raise NotImplementedError("PostgreSQL CaseRepository not implemented yet")


class UploadRepository(BaseRepository):
    """Future repository for uploaded file metadata (not binary blobs)."""

    def get_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("PostgreSQL UploadRepository not implemented yet")

    def save(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("PostgreSQL UploadRepository not implemented yet")

    def delete(self, entity_id: str) -> bool:
        raise NotImplementedError("PostgreSQL UploadRepository not implemented yet")
