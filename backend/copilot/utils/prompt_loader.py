"""Load markdown prompt templates from disk."""

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict


PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


@lru_cache(maxsize=32)
def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


def render_prompt(name: str, **variables: Any) -> str:
    template = load_prompt(name)
    try:
        return template.format(**variables)
    except KeyError as exc:
        missing = exc.args[0]
        raise KeyError(f"Missing prompt variable '{missing}' for {name}") from exc


def format_chat_history(history: list) -> str:
    if not history:
        return "(no prior turns)"
    lines = []
    for turn in history:
        role = turn.get("role", "user")
        content = turn.get("content", "")
        lines.append(f"{role.upper()}: {content}")
    return "\n".join(lines)
