"""Conditional routing helpers for the Copilot graph."""

from backend.core.settings import get_settings
from backend.copilot.graph.state import CopilotState


def after_planner(state: CopilotState) -> str:
    planner = state.get("planner_output") or {}
    if planner.get("can_answer_from_mastersheet") is False:
        return "unsupported"
    return "sql_generator"


def after_validator(state: CopilotState) -> str:
    settings = get_settings()
    max_retries = settings.copilot_max_sql_retries

    if state.get("sql_valid"):
        return "sql_executor"

    retry_count = int(state.get("retry_count") or 0)
    if retry_count < max_retries:
        return "sql_generator"

    return "give_up"


def after_executor(state: CopilotState) -> str:
    if state.get("final_answer") == "No matching data found.":
        return "end"
    if state.get("sql_result") is None and state.get("final_answer"):
        return "end"
    if int(state.get("rows_returned") or 0) == 0 and state.get("final_answer"):
        return "end"
    return "answer_generator"
