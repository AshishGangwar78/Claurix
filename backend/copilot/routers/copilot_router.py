"""
Copilot HTTP router — public REST contract for frontend integration.

Endpoints:
  POST /api/copilot/chat         — synchronous envelope response
  POST /api/copilot/chat/stream  — Server-Sent Events progress stream
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse

from backend.api.deps import get_current_user
from backend.copilot.schemas.chat import (
    CopilotChatRequest,
    CopilotChatResponse,
    CopilotErrorCode,
    StreamEvent,
    StreamEventType,
)
from backend.copilot.services.copilot_service import copilot_service
from backend.copilot.services.memory import conversation_memory
from backend.copilot.services.response_builder import build_envelope, new_message_id

router = APIRouter(prefix="/api/copilot", tags=["copilot"])


@router.post(
    "/chat",
    response_model=CopilotChatResponse,
    summary="Copilot chat (synchronous)",
    response_description="Standard Copilot envelope (success or structured error)",
)
async def copilot_chat(
    payload: CopilotChatRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    x_case_id: Optional[str] = Header(default=None, alias="X-Case-Id"),
) -> CopilotChatResponse:
    """
    Ask a natural-language question over the active case MasterSheet.

    The response always uses the standard envelope:

    - `success`, `conversation_id`, `message_id`
    - `response` (text | markdown | table | chart)
    - `artifacts` (table | chart | markdown | json | file)
    - `suggestions`, `metadata`
    - `error` with structured codes when `success=false`

    LangGraph internals are never exposed. When `debug=true`, planner/SQL
    details are nested under `metadata.debug` only.
    """
    if not payload.message.strip():
        conversation_id = conversation_memory.ensure_conversation_id(
            payload.conversation_id
        )
        return build_envelope(
            conversation_id=conversation_id,
            message_id=new_message_id(),
            answer="Message cannot be empty.",
            case_id=payload.case_id or x_case_id,
            debug=payload.debug,
            internal_error="VALIDATION_ERROR",
        )

    case_id = payload.case_id or x_case_id
    return copilot_service.chat(
        message=payload.message,
        conversation_id=payload.conversation_id,
        case_id=case_id,
        debug=payload.debug,
        user_id=str(user.get("user_id")),
    )


@router.post(
    "/chat/stream",
    summary="Copilot chat (SSE stream)",
    response_description="text/event-stream of Copilot progress events",
    responses={
        200: {
            "content": {
                "text/event-stream": {
                    "schema": {"$ref": "#/components/schemas/StreamEvent"}
                }
            },
            "description": (
                "SSE stream emitting planning, tool_call, tool_result, "
                "answer_chunk, completed, and error events"
            ),
        }
    },
)
async def copilot_chat_stream(
    payload: CopilotChatRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    x_case_id: Optional[str] = Header(default=None, alias="X-Case-Id"),
):
    """
    Stream Copilot progress via Server-Sent Events (SSE).

    Each event is a JSON `StreamEvent`:

    ```json
    {
      "event": "planning | tool_call | tool_result | answer_chunk | completed | error",
      "conversation_id": "...",
      "message_id": "...",
      "data": {}
    }
    ```

    The final `completed` event includes the full response envelope under
    `data.envelope`, so the UI can reconcile streamed chunks with the
    canonical message payload.
    """
    case_id = payload.case_id or x_case_id

    def event_generator():
        try:
            for event in copilot_service.chat_stream(
                message=payload.message,
                conversation_id=payload.conversation_id,
                case_id=case_id,
                debug=payload.debug,
                user_id=str(user.get("user_id")),
            ):
                payload_json = event.model_dump()
                yield (
                    f"event: {event.event.value}\n"
                    f"data: {json.dumps(payload_json, default=str)}\n\n"
                )
        except Exception:
            conversation_id = conversation_memory.ensure_conversation_id(
                payload.conversation_id
            )
            message_id = new_message_id()
            err = StreamEvent(
                event=StreamEventType.error,
                conversation_id=conversation_id,
                message_id=message_id,
                data={
                    "code": CopilotErrorCode.INTERNAL_ERROR.value,
                    "message": "Streaming failed unexpectedly.",
                },
            )
            yield (
                f"event: error\n"
                f"data: {json.dumps(err.model_dump(), default=str)}\n\n"
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
