"""LangGraph node implementations for the Copilot."""

from __future__ import annotations

import json
from typing import Any, Dict

from backend.core.logging import get_logger
from backend.core.settings import get_settings
from backend.copilot.graph.state import CopilotState
from backend.copilot.schema.mastersheet import get_mastersheet_schema_prompt
from backend.copilot.tools.sql_tool import execute_sql_safe
from backend.copilot.utils.prompt_loader import format_chat_history, render_prompt
from backend.copilot.utils.sql_guard import normalize_sql, validate_select_sql
from backend.services import llm_service

logger = get_logger(__name__)


def _llm_text(prompt: str, *, json_mode: bool = False) -> str:
    settings = get_settings()
    kwargs: Dict[str, Any] = {
        "model": settings.ollama_model,
        "messages": [{"role": "user", "content": prompt}],
    }
    if json_mode:
        kwargs["format"] = "json"

    response = llm_service.chat(**kwargs)
    content = response["message"]["content"]
    return str(content).strip()


def _parse_json_content(content: str) -> Dict[str, Any]:
    text = content.replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    return {
        "intent": "general_mastersheet",
        "requires_reasoning": True,
        "output_type": "narrative",
        "can_answer_from_mastersheet": True,
        "notes": "Planner JSON parse fallback",
    }


def planner_node(state: CopilotState) -> Dict[str, Any]:
    prompt = render_prompt(
        "planner.md",
        case_id=state.get("case_id") or "None",
        chat_history=format_chat_history(state.get("chat_history") or []),
        user_query=state.get("user_query", ""),
    )
    raw = _llm_text(prompt, json_mode=True)
    planner_output = _parse_json_content(raw)
    logger.info(
        "Planner complete | intent=%s | can_answer=%s",
        planner_output.get("intent"),
        planner_output.get("can_answer_from_mastersheet"),
    )
    return {
        "planner_output": planner_output,
        "retry_count": state.get("retry_count", 0) or 0,
        "error": None,
    }


def sql_generator_node(state: CopilotState) -> Dict[str, Any]:
    planner_output = state.get("planner_output") or {}

    if planner_output.get("can_answer_from_mastersheet") is False:
        return {
            "final_answer": (
                "I can only answer questions from the Insurance MasterSheet "
                "(premiums, clauses, acceptance, deviations, and related fields)."
            ),
            "sql_valid": False,
            "error": "unsupported_intent",
        }

    prompt = render_prompt(
        "sql_generator.md",
        schema=get_mastersheet_schema_prompt(),
        case_id=state.get("case_id") or "None",
        planner_output=json.dumps(planner_output, ensure_ascii=False),
        chat_history=format_chat_history(state.get("chat_history") or []),
        previous_sql=state.get("sql_query") or "",
        validation_error=state.get("error") or "",
        user_query=state.get("user_query", ""),
    )
    sql = normalize_sql(_llm_text(prompt, json_mode=False))
    logger.info("SQL generated | length=%s", len(sql))
    return {
        "sql_query": sql,
        "sql_valid": False,
        "error": None,
    }


def sql_validator_node(state: CopilotState) -> Dict[str, Any]:
    sql = state.get("sql_query") or ""
    valid, reason = validate_select_sql(sql)
    retry_count = int(state.get("retry_count") or 0)

    if valid:
        logger.info("SQL validated successfully")
        return {
            "sql_valid": True,
            "error": None,
        }

    retry_count += 1
    logger.warning(
        "SQL invalid | reason=%s | retry=%s",
        reason,
        retry_count,
    )
    return {
        "sql_valid": False,
        "retry_count": retry_count,
        "error": reason,
    }


def sql_executor_node(state: CopilotState) -> Dict[str, Any]:
    sql = state.get("sql_query") or ""
    frame, error = execute_sql_safe(sql)

    if error:
        logger.error("SQL executor error | %s", error)
        return {
            "sql_result": None,
            "rows_returned": 0,
            "final_answer": (
                "I couldn't retrieve MasterSheet data right now. "
                "Please try again later or verify database connectivity."
            ),
            "error": error,
        }

    assert frame is not None
    rows = int(len(frame))
    records = frame.head(200).to_dict(orient="records")

    if rows == 0:
        return {
            "sql_result": [],
            "rows_returned": 0,
            "final_answer": "No matching data found.",
            "error": None,
        }

    logger.info("SQL executor returned rows=%s", rows)
    return {
        "sql_result": records,
        "rows_returned": rows,
        "error": None,
    }


def answer_generator_node(state: CopilotState) -> Dict[str, Any]:
    # If an earlier node already set a terminal answer (empty/unsupported/error), keep it
    if state.get("final_answer") and state.get("rows_returned", None) == 0:
        return {}
    if state.get("final_answer") and state.get("error") in {
        "unsupported_intent",
    }:
        return {}
    if state.get("final_answer") and state.get("sql_result") is None and state.get("error"):
        return {}

    result = state.get("sql_result") or []
    prompt = render_prompt(
        "answer_generator.md",
        user_query=state.get("user_query", ""),
        sql_query=state.get("sql_query") or "",
        sql_result=json.dumps(result, ensure_ascii=False, default=str),
    )
    answer = _llm_text(prompt, json_mode=False)
    logger.info("Answer generated | chars=%s", len(answer))
    return {
        "final_answer": answer,
        "error": None,
    }
