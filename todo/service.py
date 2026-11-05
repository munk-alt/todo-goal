"""业务逻辑层（便笺风待办版）。

封装校验、排序、移动等规则；不依赖 tkinter。
"""

from __future__ import annotations

from typing import List, Optional

from .models import Note, Todo
from .storage import TaskRepository


class ValidationError(ValueError):
    """输入校验失败。"""


class TodoService:
    def __init__(self, repo: TaskRepository):
        self.repo = repo

    # ---------------- 校验 ----------------
    def validate(self, todo: Todo) -> Todo:
        todo.time_text = (todo.time_text or "").strip()
        todo.place_text = (todo.place_text or "").strip()
        todo.content_text = (todo.content_text or "").strip()
        if not todo.content_text:
            raise ValidationError("「内容」不能为空。")
        return todo

    # ---------------- 待办写操作 ----------------
    def add(self, time_text: str = "", place_text: str = "", content_text: str = "") -> Todo:
        todo = Todo(
            time_text=time_text,
            place_text=place_text,
            content_text=content_text,
            sort_order=self.repo.next_sort_order(),
        )
        self.validate(todo)
        return self.repo.insert_todo(todo)

    def update(self, todo: Todo) -> Todo:
        self.validate(todo)
        return self.repo.update_todo(todo)

    def delete(self, todo_id: int) -> bool:
        return self.repo.delete_todo(todo_id)

    def toggle(self, todo_id: int) -> Optional[Todo]:
        todo = self.repo.get_todo(todo_id)
        if todo is None:
            return None
        todo.done = not todo.done
        return self.repo.update_todo(todo)

    def get(self, todo_id: int) -> Optional[Todo]:
        return self.repo.get_todo(todo_id)

    # ---------------- 排序 ----------------
    def list(self) -> List[Todo]:
        return self.repo.list_todos()

    def reorder(self, ordered_ids: List[int]) -> None:
        self.repo.set_orders(ordered_ids)

    def move(self, todo_id: int, delta: int) -> bool:
        """上移(delta=-1) / 下移(delta=+1)。"""
        todos = self.repo.list_todos()
        index = next((i for i, t in enumerate(todos) if t.id == todo_id), None)
        if index is None:
            return False
        target = index + delta
        if target < 0 or target >= len(todos):
            return False
        ids = [t.id for t in todos]
        ids[index], ids[target] = ids[target], ids[index]
        self.repo.set_orders(ids)
        return True

    def move_to_index(self, todo_id: int, new_index: int) -> bool:
        todos = self.repo.list_todos()
        ids = [t.id for t in todos]
        if todo_id not in ids:
            return False
        ids.remove(todo_id)
        new_index = max(0, min(new_index, len(ids)))
        ids.insert(new_index, todo_id)
        self.repo.set_orders(ids)
        return True

    # ---------------- 计数 ----------------
    def counts(self) -> dict:
        todos = self.repo.list_todos()
        total = len(todos)
        done = sum(1 for t in todos if t.done)
        return {"total": total, "done": done, "active": total - done}

    # ---------------- 便签 ----------------
    def get_note(self) -> Note:
        return self.repo.get_note()

    def save_note(self, content: str) -> Note:
        return self.repo.set_note(content or "")
