"""SQLite 存储层（便笺风待办版）。

表：
- todos：待办（时间/地点/内容/完成/排序）
- note ：单个便签（固定 id=1）

只负责持久化，不含业务规则。
"""

from __future__ import annotations

import os
import sqlite3
from typing import List, Optional, Sequence

from .models import Note, Todo, now_iso

SCHEMA_VERSION = 2

_SCHEMA = """
CREATE TABLE IF NOT EXISTS todos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    time_text    TEXT    NOT NULL DEFAULT '',
    place_text   TEXT    NOT NULL DEFAULT '',
    content_text TEXT    NOT NULL DEFAULT '',
    done         INTEGER NOT NULL DEFAULT 0,
    sort_order   INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT    NOT NULL,
    updated_at   TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_todos_order ON todos(sort_order);

CREATE TABLE IF NOT EXISTS note (
    id         INTEGER PRIMARY KEY CHECK (id = 1),
    content    TEXT NOT NULL DEFAULT '',
    updated_at TEXT
);
INSERT OR IGNORE INTO note (id, content, updated_at) VALUES (1, '', NULL);
"""


def _row_to_todo(row: sqlite3.Row) -> Todo:
    return Todo(
        id=row["id"],
        time_text=row["time_text"] or "",
        place_text=row["place_text"] or "",
        content_text=row["content_text"] or "",
        done=bool(row["done"]),
        sort_order=int(row["sort_order"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class TaskRepository:
    """基于 SQLite 的仓储（保留类名以兼容既有引用）。"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        if db_path != ":memory:":
            parent = os.path.dirname(os.path.abspath(db_path))
            if parent:
                os.makedirs(parent, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        try:
            self.conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.DatabaseError:
            pass
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._migrate()

    def _migrate(self) -> None:
        version = self.conn.execute("PRAGMA user_version").fetchone()[0]
        if version < 2:
            self.conn.executescript(_SCHEMA)
            self.conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        self.conn.commit()

    # ---------------- 待办 ----------------
    def list_todos(self) -> List[Todo]:
        cur = self.conn.execute("SELECT * FROM todos ORDER BY sort_order ASC, id ASC")
        return [_row_to_todo(r) for r in cur.fetchall()]

    def get_todo(self, todo_id: int) -> Optional[Todo]:
        cur = self.conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
        row = cur.fetchone()
        return _row_to_todo(row) if row else None

    def next_sort_order(self) -> int:
        row = self.conn.execute("SELECT COALESCE(MAX(sort_order), -1) FROM todos").fetchone()
        return int(row[0]) + 1

    def insert_todo(self, todo: Todo) -> Todo:
        ts = now_iso()
        todo.created_at = todo.created_at or ts
        todo.updated_at = ts
        cur = self.conn.execute(
            """
            INSERT INTO todos (time_text, place_text, content_text, done,
                               sort_order, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                todo.time_text,
                todo.place_text,
                todo.content_text,
                int(todo.done),
                int(todo.sort_order),
                todo.created_at,
                todo.updated_at,
            ),
        )
        self.conn.commit()
        todo.id = int(cur.lastrowid)
        return todo

    def update_todo(self, todo: Todo) -> Todo:
        if todo.id is None:
            raise ValueError("更新待办需要 id")
        todo.updated_at = now_iso()
        self.conn.execute(
            """
            UPDATE todos
               SET time_text = ?, place_text = ?, content_text = ?, done = ?,
                   sort_order = ?, updated_at = ?
             WHERE id = ?
            """,
            (
                todo.time_text,
                todo.place_text,
                todo.content_text,
                int(todo.done),
                int(todo.sort_order),
                todo.updated_at,
                todo.id,
            ),
        )
        self.conn.commit()
        return todo

    def delete_todo(self, todo_id: int) -> bool:
        cur = self.conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def set_orders(self, ordered_ids: Sequence[int]) -> None:
        """按给定 id 顺序重排（0..n-1）。"""
        self.conn.executemany(
            "UPDATE todos SET sort_order = ? WHERE id = ?",
            [(order, int(tid)) for order, tid in enumerate(ordered_ids)],
        )
        self.conn.commit()

    # ---------------- 便签 ----------------
    def get_note(self) -> Note:
        row = self.conn.execute("SELECT content, updated_at FROM note WHERE id = 1").fetchone()
        if not row:
            return Note(content="", updated_at=None)
        return Note(content=row["content"] or "", updated_at=row["updated_at"])

    def set_note(self, content: str) -> Note:
        ts = now_iso()
        self.conn.execute(
            "UPDATE note SET content = ?, updated_at = ? WHERE id = 1", (content, ts)
        )
        self.conn.commit()
        return Note(content=content, updated_at=ts)

    # ---------------- 生命周期 ----------------
    def close(self) -> None:
        try:
            self.conn.close()
        except sqlite3.Error:
            pass
