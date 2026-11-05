"""数据模型与常量（便笺风待办版）。

不依赖 tkinter，可独立用于测试。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


def now_iso() -> str:
    """当前本地时间的 ISO 字符串（秒级）。"""
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


@dataclass
class Todo:
    """一条待办：时间 / 地点 / 内容 分字段保存，可手动排序。"""

    id: Optional[int] = None
    time_text: str = ""
    place_text: str = ""
    content_text: str = ""
    done: bool = False
    sort_order: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @property
    def display_title(self) -> str:
        return self.content_text or "（未填写内容）"

    @property
    def meta_text(self) -> str:
        """把时间与地点拼成副标题，空值自动省略。"""
        parts = [p for p in (self.time_text.strip(), self.place_text.strip()) if p]
        return " · ".join(parts)


@dataclass
class Note:
    """便签：一整段可自由编辑的文字。"""

    content: str = ""
    updated_at: Optional[str] = None
