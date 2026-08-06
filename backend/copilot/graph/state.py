"""LangGraph shared state for the Copilot."""

from typing import Any, Dict, List, Optional, TypedDict


class CopilotState(TypedDict, total=False):
    user_query: str
    chat_history: List[Dict[str, str]]
    case_id: Optional[str]
    planner_output: Dict[str, Any]
    sql_query: str
    sql_valid: bool
    sql_result: Any
    final_answer: str
    retry_count: int
    error: Optional[str]
    rows_returned: int
