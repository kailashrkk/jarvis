"""
memory.py -- SQLite conversation history for Jarvis.

Stores the ongoing conversation so Jarvis remembers context
across questions within a session and optionally across sessions.

Usage:
    from memory import Memory
    mem = Memory()
    mem.add("user", "What time is it?")
    mem.add("assistant", "I don't have access to a clock.")
    history = mem.get_history()
"""

import sqlite3
import os
from datetime import datetime

DB_PATH     = "/home/kailash/jarvis/jarvis.db"
MAX_HISTORY = 20   # max message pairs to keep in context


class Memory:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    role       TEXT NOT NULL,
                    content    TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)

    def add(self, role: str, content: str) -> None:
        """Add a message to history."""
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO messages (role, content) VALUES (?, ?)",
                (role, content)
            )

    def get_history(self, max_messages: int = MAX_HISTORY) -> list[dict]:
        """
        Return the last N messages as a list of dicts for llama.cpp.
        Format: [{"role": "user"|"assistant", "content": "..."}]
        """
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT role, content FROM messages
                   ORDER BY id DESC LIMIT ?""",
                (max_messages,)
            ).fetchall()
        # Reverse to get chronological order
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

    def clear(self) -> None:
        """Clear all conversation history."""
        with self._conn() as conn:
            conn.execute("DELETE FROM messages")

    def _conn(self) -> sqlite3.Connection:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        return sqlite3.connect(self.db_path)


if __name__ == "__main__":
    mem = Memory()
    mem.clear()

    mem.add("user", "What is the capital of France?")
    mem.add("assistant", "The capital of France is Paris.")
    mem.add("user", "What about Germany?")

    history = mem.get_history()
    print("History:")
    for msg in history:
        print(f"  [{msg['role']}] {msg['content']}")

    assert len(history) == 3
    assert history[0]["role"] == "user"
    assert history[2]["content"] == "What about Germany?"
    print("memory.py smoke test complete.")
