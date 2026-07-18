"""
Request/response schema placeholders for the upload API.

Current endpoints still use FastAPI Form/File parameters directly
to preserve the existing HTTP contract. These models document the
shapes for future OpenAPI/Pydantic validation and PostgreSQL DTOs.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class PolicyConfigItem(BaseModel):
    policy: str
    sheet_name: str
    start_row: int
    end_row: int


class UploadResponse(BaseModel):
    status: str
    user_id: str
    case_id: str
    document_type: str
    policies_processed: int
    files_uploaded: int


class UploadErrorResponse(BaseModel):
    error: str


class UploadedFileInfo(BaseModel):
    original_filename: str
    stored_filename: str
    file_path: str


class UploadRequestMeta(BaseModel):
    """Logical upload request metadata (Form fields today)."""

    user_id: str
    case_id: str
    document_type: str
    policy_config: Optional[List[PolicyConfigItem]] = Field(default=None)
