"""
Audit Store — Persistent SQLite-backed task and step history.

Every task and every step the agent takes is written here.
This gives you a complete, permanent audit trail that survives
server restarts — replacing the previous in-memory-only approach.

Design notes:
- Uses aiosqlite for non-blocking async writes (safe in FastAPI).
- Schema is intentionally minimal — extend it as you add features.
- The store is a singleton accessed via get_audit_store().
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Optional

import aiosqlite

# Database file lives next to main.py in the backend directory
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "agent_audit.db")


class AuditStore:
    """
    Async SQLite-backed store for task history and step audit logs.

    Usage:
        store = await get_audit_store()
        await store.save_task(task)
        await store.save_step(task_id, step)
        history = await store.get_task_history(limit=20)
    """

    def __init__(self, db_path: str = DB_PATH):
        self._db_path = os.path.abspath(db_path)
        self._ready = False

    async def init(self) -> None:
        """Create tables if they don't exist. Call once at startup."""
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id     TEXT PRIMARY KEY,
                    goal        TEXT NOT NULL,
                    status      TEXT NOT NULL,
                    created_at  TEXT NOT NULL,
                    completed_at TEXT,
                    error       TEXT,
                    total_steps INTEGER DEFAULT 0,
                    memory      TEXT DEFAULT '{}'
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS steps (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id     TEXT NOT NULL,
                    step_number INTEGER NOT NULL,
                    tool_name   TEXT NOT NULL,
                    tool_args   TEXT NOT NULL,
                    result      TEXT NOT NULL,
                    status      TEXT NOT NULL,
                    error       TEXT,
                    timestamp   TEXT NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES tasks(task_id)
                )
            """)
            await db.commit()
        self._ready = True

    async def save_task(self, task_id: str, goal: str, status: str,
                         created_at: datetime, completed_at=None,
                         error=None, total_steps: int = 0,
                         memory: dict = {}) -> None:
        """Upsert a task record (insert or update on conflict)."""
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("""
                INSERT INTO tasks (task_id, goal, status, created_at, completed_at, error, total_steps, memory)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    status       = excluded.status,
                    completed_at = excluded.completed_at,
                    error        = excluded.error,
                    total_steps  = excluded.total_steps,
                    memory       = excluded.memory
            """, (
                task_id, goal, status,
                created_at.isoformat(),
                completed_at.isoformat() if completed_at else None,
                error, total_steps,
                json.dumps(memory),
            ))
            await db.commit()

    async def save_step(self, task_id: str, step_number: int, tool_name: str,
                         tool_args: dict, result: dict, status: str,
                         error, timestamp: datetime) -> None:
        """Append a step to the audit log."""
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("""
                INSERT INTO steps (task_id, step_number, tool_name, tool_args, result, status, error, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id, step_number, tool_name,
                json.dumps(tool_args), json.dumps(result),
                status, error, timestamp.isoformat(),
            ))
            await db.commit()

    async def get_task_history(self, limit: int = 50) -> list:
        """Return the most recent tasks (newest first)."""
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_task_steps(self, task_id: str) -> list:
        """Return all steps for a given task, ordered by step number."""
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM steps WHERE task_id = ? ORDER BY step_number ASC",
                (task_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]


# ── Singleton accessor ───────────────────────────────────────────────

_store = None
_lock = asyncio.Lock()


async def get_audit_store() -> AuditStore:
    """Return the initialized singleton AuditStore."""
    global _store
    async with _lock:
        if _store is None:
            _store = AuditStore()
            await _store.init()
    return _store
