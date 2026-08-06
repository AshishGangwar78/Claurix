"""
Extensible tool registry for the Agentic Copilot platform.

Version 1 registers only the SQL tool. Future tools (policy search,
gap analysis, document search, recommendations) register here without
changing graph node internals.
"""

from typing import Any, Callable, Dict, Optional


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Callable[..., Any]] = {}

    def register(self, name: str, tool: Callable[..., Any]) -> None:
        self._tools[name] = tool

    def get(self, name: str) -> Optional[Callable[..., Any]]:
        return self._tools.get(name)

    def list_tools(self) -> Dict[str, Callable[..., Any]]:
        return dict(self._tools)


# Process-wide registry instance
tool_registry = ToolRegistry()
