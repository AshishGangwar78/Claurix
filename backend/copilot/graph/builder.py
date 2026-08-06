"""
Build the Version-1 LangGraph Copilot graph.

Topology:
  START → Planner → SQL Generator → SQL Validator
       ↺ (invalid SQL, max 3 retries)
       → SQL Executor → Answer Generator → END

Designed so future tools can be inserted after Planner by extending
routing and registering tools in tools/registry.py.
"""

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from backend.copilot.graph.nodes import (
    answer_generator_node,
    planner_node,
    sql_executor_node,
    sql_generator_node,
    sql_validator_node,
)
from backend.copilot.graph.routing import after_executor, after_planner, after_validator
from backend.copilot.graph.state import CopilotState


def _unsupported_node(state: CopilotState) -> dict:
    return {
        "final_answer": (
            "I can only answer questions from the Insurance MasterSheet "
            "(premiums, clauses, acceptance, deviations, and related fields)."
        ),
        "rows_returned": 0,
    }


def _give_up_node(state: CopilotState) -> dict:
    reason = state.get("error") or "invalid SQL"
    return {
        "final_answer": (
            "I couldn't generate a safe database query for that question. "
            f"Please rephrase and try again. ({reason})"
        ),
        "rows_returned": 0,
    }


def build_copilot_graph():
    graph = StateGraph(CopilotState)

    graph.add_node("planner", planner_node)
    graph.add_node("sql_generator", sql_generator_node)
    graph.add_node("sql_validator", sql_validator_node)
    graph.add_node("sql_executor", sql_executor_node)
    graph.add_node("answer_generator", answer_generator_node)
    graph.add_node("unsupported", _unsupported_node)
    graph.add_node("give_up", _give_up_node)

    graph.add_edge(START, "planner")
    graph.add_conditional_edges(
        "planner",
        after_planner,
        {
            "sql_generator": "sql_generator",
            "unsupported": "unsupported",
        },
    )
    graph.add_edge("sql_generator", "sql_validator")
    graph.add_conditional_edges(
        "sql_validator",
        after_validator,
        {
            "sql_executor": "sql_executor",
            "sql_generator": "sql_generator",
            "give_up": "give_up",
        },
    )
    graph.add_conditional_edges(
        "sql_executor",
        after_executor,
        {
            "answer_generator": "answer_generator",
            "end": END,
        },
    )
    graph.add_edge("answer_generator", END)
    graph.add_edge("unsupported", END)
    graph.add_edge("give_up", END)

    return graph.compile()


@lru_cache(maxsize=1)
def get_compiled_graph():
    return build_copilot_graph()
