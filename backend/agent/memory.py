"""
Execution memory for the agent.

Stores structured data discovered during task execution
(e.g., invoice numbers, amounts, dates). This is the agent's
short-term working memory — not a database, just a dict
that lives for the duration of one task.

Design note: Kept intentionally simple. If you need persistence
across tasks, wrap this with a database-backed store.
"""

from typing import Any


class ExecutionMemory:
    """
    Key-value store for data discovered during a task.

    Usage:
        memory = ExecutionMemory()
        memory.set("invoice_id", "ABC-1023")
        memory.get("invoice_id")  # → "ABC-1023"
    """

    def __init__(self):
        self._store: dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        """Store a value in memory."""
        self._store[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from memory."""
        return self._store.get(key, default)

    def update(self, data: dict[str, Any]) -> None:
        """Bulk update memory with a dictionary."""
        self._store.update(data)

    def to_dict(self) -> dict[str, Any]:
        """Export memory as a plain dictionary (for serialization)."""
        return self._store.copy()

    def clear(self) -> None:
        """Clear all stored data."""
        self._store.clear()

    def __repr__(self) -> str:
        return f"ExecutionMemory({self._store})"
