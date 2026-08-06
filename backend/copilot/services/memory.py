"""
Short-term conversation memory.

In-memory store for Version 1. Replace with Redis / DB-backed store later
by implementing the ConversationMemory interface.
"""

from __future__ import annotations

import threading
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from typing import Deque, Dict, List, Optional

from backend.core.settings import get_settings


class ConversationMemory(ABC):
    @abstractmethod
    def get_history(self, conversation_id: str) -> List[Dict[str, str]]:
        raise NotImplementedError

    @abstractmethod
    def append(
        self,
        conversation_id: str,
        role: str,
        content: str,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def ensure_conversation_id(self, conversation_id: Optional[str]) -> str:
        raise NotImplementedError


class InMemoryConversationMemory(ConversationMemory):
    def __init__(self, max_turns: Optional[int] = None) -> None:
        settings = get_settings()
        self.max_turns = max_turns or settings.copilot_memory_turns
        self._store: Dict[str, Deque[Dict[str, str]]] = defaultdict(
            lambda: deque(maxlen=self.max_turns * 2)
        )
        self._lock = threading.Lock()

    def ensure_conversation_id(self, conversation_id: Optional[str]) -> str:
        return conversation_id or str(uuid.uuid4())

    def get_history(self, conversation_id: str) -> List[Dict[str, str]]:
        with self._lock:
            return list(self._store.get(conversation_id, []))

    def append(self, conversation_id: str, role: str, content: str) -> None:
        with self._lock:
            self._store[conversation_id].append(
                {"role": role, "content": content}
            )


# Default process memory (swap for Redis implementation later)
conversation_memory = InMemoryConversationMemory()
