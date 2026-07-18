"""
Domain model placeholders for future ORM / PostgreSQL mapping.

These mirror the JSON structures already produced by the pipeline.
They are not wired into runtime yet to avoid changing behavior.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ClauseSource(BaseModel):
    sheet_name: Optional[str] = None
    excel_row: Optional[int] = None
    clause_cell: Optional[str] = None
    requirement_cell: Optional[str] = None
    uw_remark_cell: Optional[str] = None


class Clause(BaseModel):
    clause: str = ""
    requirement: str = ""
    uw_remark: str = ""
    remark_status: Optional[str] = None
    source: Optional[Dict[str, Any]] = None


class PolicyDocument(BaseModel):
    company: str = ""
    policy: str = ""
    column_mapping: Optional[Dict[str, Any]] = None
    clauses: List[Clause] = []


class MergedInsurer(BaseModel):
    company: str = ""
    uw_remark: str = ""
    remark_status: str = ""
    source: Dict[str, Any] = {}


class MergedClause(BaseModel):
    excel_row: Optional[int] = None
    clause: str = ""
    requirement: str = ""
    insurers: List[MergedInsurer] = []


class MergedPolicy(BaseModel):
    policy: str = ""
    clauses: List[MergedClause] = []
