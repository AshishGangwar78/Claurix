"""
SQL execution tool.

The LangGraph nodes must never talk to PostgreSQL directly — they call
execute_sql() via this tool / the tool registry.
"""

from typing import Any, Optional, Tuple

import pandas as pd

from backend.core.database import session_scope
from backend.core.logging import get_logger
from backend.copilot.tools.registry import tool_registry
from backend.copilot.utils.sql_guard import normalize_sql, validate_select_sql

logger = get_logger(__name__)


class SQLExecutionError(Exception):
    """Raised when SQL cannot be executed safely."""


def execute_sql(sql: str) -> pd.DataFrame:
    """
    Validate and execute a read-only SQL statement.

    Returns a pandas DataFrame. Raises SQLExecutionError on failure.
    """
    cleaned = normalize_sql(sql)
    valid, reason = validate_select_sql(cleaned)
    if not valid:
        raise SQLExecutionError(f"SQL rejected by safety guard: {reason}")

    with session_scope() as session:
        if session is None:
            raise SQLExecutionError(
                "Database is not configured. Set DATABASE_URL to enable MasterSheet queries."
            )

        try:
            from sqlalchemy import text

            result = session.execute(text(cleaned))
            rows = result.fetchall()
            columns = list(result.keys()) if result.keys() else []
            frame = pd.DataFrame(rows, columns=columns)
            logger.info("SQL executed successfully | rows=%s", len(frame))
            return frame
        except SQLExecutionError:
            raise
        except Exception as exc:
            logger.exception("SQL execution failed")
            # Never expose raw DB exception details to callers that bubble to users
            raise SQLExecutionError(
                "Unable to execute the query against MasterSheet right now."
            ) from exc


def execute_sql_safe(sql: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Convenience wrapper returning (dataframe, error_message)."""
    try:
        return execute_sql(sql), None
    except SQLExecutionError as exc:
        return None, str(exc)


# Register for future multi-tool planner routing
tool_registry.register("sql_mastersheet", execute_sql)
