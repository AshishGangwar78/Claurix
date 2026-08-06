"""
Map internal Copilot/graph results to the public API envelope.

Keeps LangGraph state out of the HTTP contract. Future tools append
Artifacts here without changing response shape.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Tuple

from backend.copilot.schemas.chat import (
    Artifact,
    ArtifactType,
    CopilotChatResponse,
    CopilotDebugInfo,
    CopilotError,
    CopilotErrorCode,
    CopilotMetadata,
    ResponseContentType,
    ResponsePayload,
    Suggestion,
)


def new_message_id() -> str:
    return f"msg_{uuid.uuid4().hex[:16]}"


def _infer_response_type(planner_output: Dict[str, Any], has_table: bool) -> ResponseContentType:
    output_type = str(planner_output.get("output_type") or "").lower()
    if output_type == "table" and has_table:
        return ResponseContentType.markdown
    if output_type in {"narrative", "scalar", "list"}:
        return ResponseContentType.markdown
    return ResponseContentType.markdown


def build_table_artifact(
    rows: List[Dict[str, Any]],
    *,
    title: str = "Query results",
    artifact_id: Optional[str] = None,
) -> Artifact:
    columns: List[str] = []
    if rows:
        columns = list(rows[0].keys())
    return Artifact(
        id=artifact_id or f"art_table_{uuid.uuid4().hex[:8]}",
        type=ArtifactType.table,
        title=title,
        data={
            "columns": columns,
            "rows": rows,
        },
        schema_version="1.0",
    )


def build_suggestions(intent: Optional[str]) -> List[Suggestion]:
    intent = (intent or "").lower()
    if intent == "premium_analysis":
        return [
            Suggestion(label="Compare insurers", message="Compare the top two insurer premiums"),
            Suggestion(label="Average premium", message="Show average premium by insurer"),
        ]
    if intent == "clause_lookup":
        return [
            Suggestion(label="Accepted clauses", message="Which insurers accepted this clause?"),
            Suggestion(label="Deviations", message="Show deviations for this clause"),
        ]
    if intent == "acceptance_analytics":
        return [
            Suggestion(label="Highest acceptance", message="Which insurer has the highest acceptance rate?"),
            Suggestion(label="Fewest deviations", message="Which insurer has the fewest deviations?"),
        ]
    return [
        Suggestion(label="Lowest premium", message="Which insurer quoted the lowest premium?"),
        Suggestion(label="Clause remarks", message="Show remarks for the Flood clause"),
    ]


def map_error_code(internal_error: Optional[str], final_answer: str = "") -> Optional[CopilotErrorCode]:
    text = f"{internal_error or ''} {final_answer or ''}".lower()
    if "validation_error" in text or "message cannot be empty" in text:
        return CopilotErrorCode.VALIDATION_ERROR
    if "unsupported" in text:
        return CopilotErrorCode.UNSUPPORTED_QUERY
    if "database is not configured" in text or "database unavailable" in text:
        return CopilotErrorCode.DATABASE_UNAVAILABLE
    if "unable to execute" in text or "sql execution" in text or "couldn't retrieve mastersheet" in text:
        return CopilotErrorCode.SQL_EXECUTION_FAILED
    if "couldn't generate a safe" in text or "invalid sql" in text:
        return CopilotErrorCode.SQL_GENERATION_FAILED
    if "no matching data" in text:
        return None  # empty is a successful soft result, not an API error
    if "internal_error" in text or "timeout" in text:
        if "timeout" in text:
            return CopilotErrorCode.LLM_TIMEOUT
        return CopilotErrorCode.INTERNAL_ERROR
    if internal_error:
        return CopilotErrorCode.INTERNAL_ERROR
    return None


def build_envelope(
    *,
    conversation_id: str,
    message_id: str,
    answer: str,
    planner_output: Optional[Dict[str, Any]] = None,
    sql_query: Optional[str] = None,
    sql_result: Optional[List[Dict[str, Any]]] = None,
    rows_returned: int = 0,
    retries: int = 0,
    execution_time: float = 0.0,
    case_id: Optional[str] = None,
    debug: bool = False,
    internal_error: Optional[str] = None,
    tools_used: Optional[List[str]] = None,
    extra_artifacts: Optional[List[Artifact]] = None,
) -> CopilotChatResponse:
    planner_output = planner_output or {}
    sql_result = sql_result or []
    tools_used = tools_used or []

    artifacts: List[Artifact] = list(extra_artifacts or [])
    if sql_result:
        artifacts.append(
            build_table_artifact(
                sql_result,
                title="MasterSheet results",
            )
        )
        if "sql_mastersheet" not in tools_used:
            tools_used.append("sql_mastersheet")

    error_code = map_error_code(internal_error, answer)
    # Hard failures → success=false; empty data remains success=true with message
    hard_failure = error_code in {
        CopilotErrorCode.VALIDATION_ERROR,
        CopilotErrorCode.UNAUTHORIZED,
        CopilotErrorCode.UNSUPPORTED_QUERY,
        CopilotErrorCode.SQL_GENERATION_FAILED,
        CopilotErrorCode.SQL_EXECUTION_FAILED,
        CopilotErrorCode.DATABASE_UNAVAILABLE,
        CopilotErrorCode.INTERNAL_ERROR,
        CopilotErrorCode.LLM_TIMEOUT,
    }

    debug_info = None
    if debug:
        debug_info = CopilotDebugInfo(
            planner_output=planner_output or None,
            generated_sql=sql_query,
            execution_time=round(execution_time, 3),
            retry_count=retries,
        )

    metadata = CopilotMetadata(
        intent=planner_output.get("intent"),
        execution_time=round(execution_time, 3),
        rows_returned=rows_returned,
        retries=retries,
        case_id=case_id,
        tools_used=tools_used,
        debug=debug_info,
    )

    if hard_failure and error_code:
        return CopilotChatResponse(
            success=False,
            conversation_id=conversation_id,
            message_id=message_id,
            response=ResponsePayload(
                type=ResponseContentType.text,
                content=answer,
            ),
            artifacts=artifacts,
            suggestions=build_suggestions(planner_output.get("intent")),
            metadata=metadata,
            error=CopilotError(
                code=error_code,
                message=answer,
                details={"internal": internal_error} if debug and internal_error else None,
            ),
        )

    return CopilotChatResponse(
        success=True,
        conversation_id=conversation_id,
        message_id=message_id,
        response=ResponsePayload(
            type=_infer_response_type(planner_output, bool(sql_result)),
            content=answer,
        ),
        artifacts=artifacts,
        suggestions=build_suggestions(planner_output.get("intent")),
        metadata=metadata,
        error=None,
    )
