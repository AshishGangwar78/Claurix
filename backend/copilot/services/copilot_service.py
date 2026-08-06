"""Copilot application service — orchestrates memory + LangGraph."""

from __future__ import annotations

import time
from typing import Any, Dict, Generator, Optional

from backend.core.logging import get_logger
from backend.copilot.graph.builder import get_compiled_graph
from backend.copilot.schemas.chat import (
    CopilotChatResponse,
    CopilotErrorCode,
    StreamEvent,
    StreamEventType,
)
from backend.copilot.services.memory import ConversationMemory, conversation_memory
from backend.copilot.services.response_builder import build_envelope, new_message_id

logger = get_logger(__name__)


class CopilotService:
    def __init__(self, memory: Optional[ConversationMemory] = None) -> None:
        self.memory = memory or conversation_memory
        self.graph = get_compiled_graph()

    def chat(
        self,
        *,
        message: str,
        conversation_id: Optional[str] = None,
        case_id: Optional[str] = None,
        debug: bool = False,
        user_id: Optional[str] = None,
    ) -> CopilotChatResponse:
        started = time.perf_counter()
        conversation_id = self.memory.ensure_conversation_id(conversation_id)
        message_id = new_message_id()
        history = self.memory.get_history(conversation_id)

        logger.info(
            "Copilot chat | user=%s | case=%s | conversation=%s | message_id=%s | query=%s",
            user_id,
            case_id,
            conversation_id,
            message_id,
            message[:200],
        )

        initial_state = {
            "user_query": message,
            "chat_history": history,
            "case_id": case_id,
            "retry_count": 0,
            "rows_returned": 0,
        }

        try:
            result = self.graph.invoke(initial_state)
        except Exception as exc:
            logger.exception("Copilot graph failed")
            elapsed = time.perf_counter() - started
            answer = (
                "Something went wrong while processing your question. "
                "Please try again."
            )
            envelope = build_envelope(
                conversation_id=conversation_id,
                message_id=message_id,
                answer=answer,
                execution_time=elapsed,
                case_id=case_id,
                debug=debug,
                internal_error=str(exc.__class__.__name__),
            )
            # Force internal error code for unexpected exceptions
            if envelope.error is None:
                envelope = build_envelope(
                    conversation_id=conversation_id,
                    message_id=message_id,
                    answer=answer,
                    execution_time=elapsed,
                    case_id=case_id,
                    debug=debug,
                    internal_error="INTERNAL_ERROR",
                )
            self.memory.append(conversation_id, "user", message)
            self.memory.append(conversation_id, "assistant", answer)
            return envelope

        envelope = self._result_to_envelope(
            result=result,
            conversation_id=conversation_id,
            message_id=message_id,
            case_id=case_id,
            debug=debug,
            execution_time=time.perf_counter() - started,
        )

        answer_text = ""
        if envelope.response and isinstance(envelope.response.content, str):
            answer_text = envelope.response.content

        self.memory.append(conversation_id, "user", message)
        self.memory.append(conversation_id, "assistant", answer_text or "")

        logger.info(
            "Copilot done | intent=%s | rows=%s | retries=%s | success=%s | seconds=%.3f",
            envelope.metadata.intent,
            envelope.metadata.rows_returned,
            envelope.metadata.retries,
            envelope.success,
            envelope.metadata.execution_time,
        )
        return envelope

    def chat_stream(
        self,
        *,
        message: str,
        conversation_id: Optional[str] = None,
        case_id: Optional[str] = None,
        debug: bool = False,
        user_id: Optional[str] = None,
    ) -> Generator[StreamEvent, None, None]:
        """
        Stream progress events then a final `completed` event with the full envelope.

        Event types are stable for frontend clients; unknown future events should
        be ignored by the UI.
        """
        started = time.perf_counter()
        conversation_id = self.memory.ensure_conversation_id(conversation_id)
        message_id = new_message_id()
        history = self.memory.get_history(conversation_id)

        def _event(event: StreamEventType, data: Dict[str, Any]) -> StreamEvent:
            return StreamEvent(
                event=event,
                conversation_id=conversation_id,
                message_id=message_id,
                data=data,
            )

        logger.info(
            "Copilot stream | user=%s | case=%s | conversation=%s | message_id=%s",
            user_id,
            case_id,
            conversation_id,
            message_id,
        )

        yield _event(
            StreamEventType.planning,
            {"status": "started"},
        )

        initial_state = {
            "user_query": message,
            "chat_history": history,
            "case_id": case_id,
            "retry_count": 0,
            "rows_returned": 0,
        }

        merged: Dict[str, Any] = dict(initial_state)

        try:
            for update in self.graph.stream(initial_state, stream_mode="updates"):
                # update is {node_name: partial_state}
                for node_name, partial in (update or {}).items():
                    if not isinstance(partial, dict):
                        continue
                    merged.update(partial)

                    if node_name == "planner":
                        planner = partial.get("planner_output") or {}
                        yield _event(
                            StreamEventType.planning,
                            {
                                "status": "completed",
                                "intent": planner.get("intent"),
                            },
                        )

                    elif node_name == "sql_generator":
                        yield _event(
                            StreamEventType.tool_call,
                            {
                                "tool": "sql_mastersheet",
                                "status": "generating_sql",
                            },
                        )

                    elif node_name == "sql_validator" and partial.get("sql_valid"):
                        yield _event(
                            StreamEventType.tool_call,
                            {
                                "tool": "sql_mastersheet",
                                "status": "running",
                            },
                        )

                    elif node_name == "sql_executor":
                        yield _event(
                            StreamEventType.tool_result,
                            {
                                "tool": "sql_mastersheet",
                                "rows_returned": int(partial.get("rows_returned") or 0),
                                "status": "completed",
                            },
                        )

                    elif node_name in {"answer_generator", "unsupported", "give_up"}:
                        answer = partial.get("final_answer") or merged.get("final_answer") or ""
                        if answer:
                            # Emit as one chunk for V1 (chunking can be finer later)
                            yield _event(
                                StreamEventType.answer_chunk,
                                {"index": 0, "content": answer},
                            )

        except Exception as exc:
            logger.exception("Copilot stream failed")
            elapsed = time.perf_counter() - started
            answer = (
                "Something went wrong while processing your question. "
                "Please try again."
            )
            envelope = build_envelope(
                conversation_id=conversation_id,
                message_id=message_id,
                answer=answer,
                execution_time=elapsed,
                case_id=case_id,
                debug=debug,
                internal_error=str(exc.__class__.__name__),
            )
            yield _event(
                StreamEventType.error,
                {
                    "code": CopilotErrorCode.INTERNAL_ERROR.value,
                    "message": answer,
                },
            )
            yield _event(
                StreamEventType.completed,
                {"envelope": envelope.model_dump()},
            )
            self.memory.append(conversation_id, "user", message)
            self.memory.append(conversation_id, "assistant", answer)
            return

        envelope = self._result_to_envelope(
            result=merged,
            conversation_id=conversation_id,
            message_id=message_id,
            case_id=case_id,
            debug=debug,
            execution_time=time.perf_counter() - started,
        )

        # Ensure an answer_chunk was emitted even if answer came from executor early-exit
        if envelope.response and isinstance(envelope.response.content, str):
            answer_text = envelope.response.content
            if not merged.get("_answer_chunk_emitted"):
                yield _event(
                    StreamEventType.answer_chunk,
                    {"index": 0, "content": answer_text},
                )
        else:
            answer_text = ""

        if not envelope.success and envelope.error:
            yield _event(
                StreamEventType.error,
                {
                    "code": envelope.error.code.value,
                    "message": envelope.error.message,
                },
            )

        yield _event(
            StreamEventType.completed,
            {"envelope": envelope.model_dump()},
        )

        self.memory.append(conversation_id, "user", message)
        self.memory.append(conversation_id, "assistant", answer_text)

    def _result_to_envelope(
        self,
        *,
        result: Dict[str, Any],
        conversation_id: str,
        message_id: str,
        case_id: Optional[str],
        debug: bool,
        execution_time: float,
    ) -> CopilotChatResponse:
        answer = result.get("final_answer") or "No matching data found."
        planner_output = result.get("planner_output") or {}
        sql_result = result.get("sql_result")
        if sql_result is None:
            sql_rows: list = []
        elif isinstance(sql_result, list):
            sql_rows = sql_result
        else:
            sql_rows = []

        return build_envelope(
            conversation_id=conversation_id,
            message_id=message_id,
            answer=answer,
            planner_output=planner_output,
            sql_query=result.get("sql_query"),
            sql_result=sql_rows if isinstance(sql_rows, list) else [],
            rows_returned=int(result.get("rows_returned") or 0),
            retries=int(result.get("retry_count") or 0),
            execution_time=execution_time,
            case_id=case_id,
            debug=debug,
            internal_error=result.get("error"),
            tools_used=["sql_mastersheet"] if result.get("sql_query") else [],
        )


copilot_service = CopilotService()
