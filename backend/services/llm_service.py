"""
Central LLM gateway.

All Ollama / model interactions must go through this module.
Prompt construction and response parsing stay in caller modules
so business logic is unchanged.
"""

import ollama


DEFAULT_MODEL = "qwen2.5:7b"


def chat(model=DEFAULT_MODEL, messages=None, format=None):
    """
    Thin wrapper around ollama.chat.

    Preserves exact call semantics used by clause extraction modules.
    """
    if messages is None:
        messages = []

    kwargs = {
        "model": model,
        "messages": messages,
    }

    if format is not None:
        kwargs["format"] = format

    return ollama.chat(**kwargs)
