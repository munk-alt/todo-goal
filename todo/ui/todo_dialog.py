"""添加 / 编辑待办的浮动对话框（与便笺风格一致，无系统边框）。"""

from __future__ import annotations

import tkinter as tk
from typing import Optional

from ..models import Todo
from ..service import TodoService, ValidationError
from . import theme
from .widgets import enable_window_drag

_DLG_WIDTH = 336


class TodoDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, service: TodoService, colors: dict,
                 todo: Optional[Todo] = None):
        super().__init__(parent)
        self.service = service
        self.colors = colors
        self._existing = todo
        self.result: Optional[Todo] = None

        self.overrideredirect(True)
        self.configure(bg=colors["window_bg"])
        try:
            self.attributes("-topmost", True)
            self.attributes("-alpha", 0.99)
        except tk.TclError:
            pass

        self._build(todo)
        self._center_on(parent.winfo_toplevel())
        self.bind("<Escape>", lambda e: self._cancel())
        self.bind("<Control-Return>", lambda e: self._save())
        # 注意：overrideredirect 的主窗口若用 transient 会导致子窗口不显示，故不使用
        self.deiconify()
        self.lift()
        try:
            self.grab_set()
        except tk.TclError:
            pass
        self.focus_force()
        (self._time_entry if todo and todo.time_text else self._content_entry).focus_set()

    # ---------------- 布局 ----------------
    def _build(self, todo: Optional[Todo]) -> None:
        colors = self.colors
        family = theme.font_family()
        symbol = theme.pick_symbol_font(self)

        outer = tk.Frame(self, bg=colors["window_bg"], padx=14, pady=12)
        outer.pack(fill="both", expand=True)

        # 标题栏
        bar = tk.Frame(outer, bg=colors["window_bg"])
        bar.pack(fill="x", pady=(0, 10))
        title = tk.Label(bar, text=("编辑待办" if todo else "添加待办"),
                         bg=colors["window_bg"], fg=colors["text"],
                         font=(family, 12, "bold"), anchor="w")
        title.pack(side="left")
        close = tk.Label(bar, text="✕", bg=colors["window_bg"], fg=colors["muted"],
                         font=(symbol, 11), cursor="hand2")
        close.pack(side="right")
        close.bind("<Button-1>", lambda e: self._cancel())
        close.bind("<Enter>", lambda e: close.configure(fg=colors["text"]))
        close.bind("<Leave>", lambda e: close.configure(fg=colors["muted"]))
        enable_window_drag(bar, self)
        enable_window_drag(title, self)

        self._fields = {}
        self._time_entry = self._add_field(outer, "时间", todo.time_text if todo else "", family)
        self._place_entry = self._add_field(outer, "地点", todo.place_text if todo else "", family)
        self._content_entry = self._add_field(outer, "内容 *", todo.content_text if todo else "", family)

        self._error = tk.Label(outer, text="", bg=colors["window_bg"], fg="#e5534b",
                               font=(family, 9), anchor="w")
        self._error.pack(fill="x", pady=(2, 6))

        buttons = tk.Frame(outer, bg=colors["window_bg"])
        buttons.pack(fill="x", pady=(4, 0))
        save = tk.Button(buttons, text="保存", command=self._save, bd=0,
                         highlightthickness=0, relief="flat", cursor="hand2",
                         bg=colors["accent"], fg=colors["window_bg"],
                         activebackground=colors["accent"], activeforeground=colors["window_bg"],
                         font=(family, 10, "bold"), padx=16, pady=5)
        save.pack(side="right")
        cancel = tk.Button(buttons, text="取消", command=self._cancel, bd=0,
                           highlightthickness=0, relief="flat", cursor="hand2",
                           bg=colors["hover"], fg=colors["text"],
                           activebackground=colors["hover"], activeforeground=colors["text"],
                           font=(family, 10), padx=14, pady=5)
        cancel.pack(side="right", padx=(0, 8))

    def _add_field(self, parent, label_text: str, value: str, family: str) -> tk.Entry:
        colors = self.colors
        box = tk.Frame(parent, bg=colors["window_bg"])
        box.pack(fill="x", pady=(0, 8))
        tk.Label(box, text=label_text, bg=colors["window_bg"], fg=colors["muted"],
                 font=(family, 9), anchor="w").pack(fill="x")
        entry = tk.Entry(box, bg=colors["input_bg"], fg=colors["text"],
                         insertbackground=colors["accent"], relief="flat", bd=0,
                         highlightthickness=1, highlightbackground=colors["divider"],
                         highlightcolor=colors["accent"], font=(family, 10))
        entry.insert(0, value or "")
        entry.pack(fill="x", ipady=5, pady=(3, 0))
        entry.bind("<Return>", lambda e: self._save())
        return entry

    def _center_on(self, parent: tk.Misc) -> None:
        self.update_idletasks()
        h = self.winfo_reqheight()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        x = px + max((pw - _DLG_WIDTH) // 2, 0)
        y = py + max((ph - h) // 3, 0)
        self.geometry(f"{_DLG_WIDTH}x{h}+{x}+{y}")

    # ---------------- 事件 ----------------
    def _save(self) -> None:
        time_text = self._time_entry.get()
        place_text = self._place_entry.get()
        content_text = self._content_entry.get()
        try:
            if self._existing:
                todo = Todo(
                    id=self._existing.id,
                    time_text=time_text,
                    place_text=place_text,
                    content_text=content_text,
                    done=self._existing.done,
                    sort_order=self._existing.sort_order,
                    created_at=self._existing.created_at,
                )
                self.result = self.service.update(todo)
            else:
                self.result = self.service.add(time_text, place_text, content_text)
        except ValidationError as exc:
            self._error.configure(text=str(exc))
            self._content_entry.focus_set()
            return
        self.destroy()

    def _cancel(self) -> None:
        self.result = None
        self.destroy()
