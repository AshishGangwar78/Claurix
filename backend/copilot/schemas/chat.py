"""
Production REST API contracts for the Copilot.

Frontend-facing models only — LangGraph internals are never part of the
public schema. Future tools attach results as Artifacts without changing
the envelope.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums / shared primitives
# ---------------------------------------------------------------------------


class ResponseContentType(str, Enum):
    text = "text"
    markdown = "markdown"
    table = "table"
    chart = "chart"


class ArtifactType(str, Enum):
    table = "table"
    chart = "chart"
    markdown = "markdown"
    json = "json"
    file = "file"  # reserved for future downloads / exports


class StreamEventType(str, Enum):
    planning = "planning"
    tool_call = "tool_call"
    tool_result = "tool_result"
    answer_chunk = "answer_chunk"
    completed = "completed"
    error = "error"


class CopilotErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    UNSUPPORTED_QUERY = "UNSUPPORTED_QUERY"
    SQL_GENERATION_FAILED = "SQL_GENERATION_FAILED"
    SQL_EXECUTION_FAILED = "SQL_EXECUTION_FAILED"
    DATABASE_UNAVAILABLE = "DATABASE_UNAVAILABLE"
    EMPTY_RESULT = "EMPTY_RESULT"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------


class CopilotChatRequest(BaseModel):
    """Chat request used by both /chat and /chat/stream."""

    message: str = Field(..., min_length=1, description="User natural-language question")
    conversation_id: Optional[str] = Field(
        default=None,
        description="Omit or null on first turn; reuse for follow-ups",
    )
    case_id: Optional[str] = Field(
        default=None,
        description="Active case — scopes MasterSheet queries when set",
    )
    debug: bool = Field(
        default=False,
        description="When true, metadata includes planner/SQL debug fields",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Which insurer quoted the lowest premium?",
                    "conversation_id": None,
                    "case_id": "101",
                    "debug": False,
                }
            ]
        }
    }


# ---------------------------------------------------------------------------
# Response envelope
# ---------------------------------------------------------------------------


class ResponsePayload(BaseModel):
    type: ResponseContentType = ResponseContentType.markdown
    content: Union[str, Dict[str, Any], List[Any]] = Field(
        ...,
        description="Primary user-visible content (markdown/text or structured)",
    )


class Artifact(BaseModel):
    """
    Extensible tool output container.

    New LangGraph tools should return artifacts instead of inventing new
    top-level response fields.
    """

    id: str = Field(..., description="Stable artifact id within the message")
    type: ArtifactType
    title: Optional[str] = None
    data: Any = Field(
        ...,
        description="Type-specific payload (table rows, chart spec, json, file meta)",
    )
    schema_version: str = Field(default="1.0")


class Suggestion(BaseModel):
    label: str
    message: str = Field(..., description="Prefill text if the user clicks the suggestion")


class CopilotDebugInfo(BaseModel):
    planner_output: Optional[Dict[str, Any]] = None
    generated_sql: Optional[str] = None
    execution_time: Optional[float] = None
    retry_count: Optional[int] = None


class CopilotMetadata(BaseModel):
    intent: Optional[str] = None
    execution_time: float = 0.0
    rows_returned: int = 0
    retries: int = 0
    case_id: Optional[str] = None
    tools_used: List[str] = Field(default_factory=list)
    debug: Optional[CopilotDebugInfo] = None


class CopilotError(BaseModel):
    code: CopilotErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None


class CopilotChatResponse(BaseModel):
    """Standard success/error envelope for POST /api/copilot/chat."""

    success: bool
    conversation_id: str
    message_id: str
    response: Optional[ResponsePayload] = None
    artifacts: List[Artifact] = Field(default_factory=list)
    suggestions: List[Suggestion] = Field(default_factory=list)
    metadata: CopilotMetadata = Field(default_factory=CopilotMetadata)
    error: Optional[CopilotError] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "conversation_id": "8f2c9e2a-1111-2222-3333-444444444444",
                    "message_id": "msg_01HXYZ",
                    "response": {
                        "type": "markdown",
                        "content": "**Tata AIG** quoted the lowest premium at **18500**.",
                    },
                    "artifacts": [
                        {
                            "id": "art_table_1",
                            "type": "table",
                            "title": "Premium by insurer",
                            "data": {
                                "columns": ["insurer", "lowest_premium"],
                                "rows": [
                                    {"insurer": "Tata AIG", "lowest_premium": 18500},
                                    {"insurer": "ICICI Lombard", "lowest_premium": 22000},
                                ],
                            },
                            "schema_version": "1.0",
                        }
                    ],
                    "suggestions": [
                        {
                            "label": "Compare top 2",
                            "message": "Compare Tata AIG and ICICI Lombard premiums",
                        }
                    ],
                    "metadata": {
                        "intent": "premium_analysis",
                        "execution_time": 1.84,
                        "rows_returned": 3,
                        "retries": 0,
                        "case_id": "101",
                        "tools_used": ["sql_mastersheet"],
                        "debug": None,
                    },
                    "error": None,
                }
            ]
        }
    }


# ---------------------------------------------------------------------------
# SSE stream events
# ---------------------------------------------------------------------------


class StreamEvent(BaseModel):
    """
    One Server-Sent Event payload for POST /api/copilot/chat/stream.

    Clients should switch on `event` and ignore unknown future event types.
    """

    event: StreamEventType
    conversation_id: str
    message_id: str
    data: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "event": "planning",
                    "conversation_id": "8f2c9e2a-....",
                    "message_id": "msg_01HXYZ",
                    "data": {"status": "started", "intent": None},
                },
                {
                    "event": "tool_call",
                    "conversation_id": "8f2c9e2a-....",
                    "message_id": "msg_01HXYZ",
                    "data": {"tool": "sql_mastersheet", "status": "running"},
                },
                {
                    "event": "tool_result",
                    "conversation_id": "8f2c9e2a-....",
                    "message_id": "msg_01HXYZ",
                    "data": {"tool": "sql_mastersheet", "rows_returned": 3},
                },
                {
                    "event": "answer_chunk",
                    "conversation_id": "8f2c9e2a-....",
                    "message_id": "msg_01HXYZ",
                    "data": {"index": 0, "content": "Tata AIG quoted the lowest premium"},
                },
                {
                    "event": "completed",
                    "conversation_id": "8f2c9e2a-....",
                    "message_id": "msg_01HXYZ",
                    "data": {"envelope": {"success": True}},
                },
            ]
        }
    }
