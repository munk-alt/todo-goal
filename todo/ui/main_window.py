"""便笺风主窗口：无边框、半透明、可拖动/置顶/缩放。

结构：
  [标题栏：Todo · 便签   ……   亮/暗  置顶  关闭]
  [待办  ＋添加]
  [ 待办列表（可滚动、拖拽排序、右键菜单） ]
  [ ———————— ]
  [便签]
  [ 便签文本（自动保存） ]
"""

from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from typing import List, Optional

from ..models import Todo
from ..service import TodoService
from . import theme
from .todo_dialog import TodoDialog
from .widgets import ScrollableFrame, enable_window_drag

DEFAULT_WIDTH = 362
DEFAULT_HEIGHT = 560
SCREEN_MARGIN = 36


class MainWindow:
    def __init__(self, root: tk.Tk, service: TodoService, data_dir):
        self.root = root
        self.service = service
        self.data_dir = Path(data_dir)
        self.settings_path = self.data_dir / "settings.json"
        self.settings = self._load_settings()

        self.theme_name = self.settings.get("theme", "dark")
        if self.theme_name not in theme.THEMES:
            self.theme_name = "dark"
        self.colors = theme.get_theme(self.theme_name)
        self._topmost = bool(self.settings.get("topmost", True))

        theme.pick_font_family(root)
        self.family = theme.font_family()
        self.symbol = theme.pick_symbol_font(root)

        self._todos: List[Todo] = []
        self._row_frames = []
        self._drag_tid: Optional[int] = None
        self._note_job = None
        self._note_cache = ""
        self._resize_state = None

        root.overrideredirect(True)
        root.configure(bg=self.colors["window_bg"])
        self._apply_window_attrs()
        self._restore_geometry()
        self._build()
        self.refresh_todos()
        self._load_note()

        root.bind("<Control-n>", lambda e: self._add_todo())

    # ------------------------------------------------------------------
    # 窗口属性 / 几何
    # ------------------------------------------------------------------
    def _apply_window_attrs(self) -> None:
        try:
            self.root.attributes("-topmost", self._topmost)
            self.root.attributes("-alpha", self.colors["alpha"])
        except tk.TclError:
            pass

    def _restore_geometry(self) -> None:
        width = int(self.settings.get("width", DEFAULT_WIDTH))
        height = int(self.settings.get("height", DEFAULT_HEIGHT))
        width = max(width, 300)
        height = max(height, 360)
        x = self.settings.get("x")
        y = self.settings.get("y")
        if x is None or y is None:
            screen_w = self.root.winfo_screenwidth()
            x = max(20, min(int(screen_w * 0.62), screen_w - width - 20))
            y = 100
        self.root.geometry(f"{width}x{height}+{int(x)}+{int(y)}")

    def _load_settings(self) -> dict:
        try:
            if self.settings_path.exists():
                return json.loads(self.settings_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
        return {}

    def _save_settings(self) -> None:
        data = {
            "x": self.root.winfo_x(),
            "y": self.root.winfo_y(),
            "width": self.root.winfo_width(),
            "height": self.root.winfo_height(),
            "theme": self.theme_name,
            "topmost": self._topmost,
        }
        try:
            self.settings_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass

    # ------------------------------------------------------------------
    # 构建界面
    # ------------------------------------------------------------------
    def _build(self) -> None:
        colors = self.colors
        self.outer = tk.Frame(self.root, bg=colors["window_bg"])
        self.outer.pack(fill="both", expand=True)
        self.outer.columnconfigure(0, weight=1)
        self.outer.rowconfigure(2, weight=4, minsize=140)
        self.outer.rowconfigure(5, weight=3, minsize=96)

        self._build_titlebar()
        self._build_todo_section()
        self._build_note_section()
        self._build_resize_grip()

    def _build_titlebar(self) -> None:
        colors = self.colors
        bar = tk.Frame(self.outer, bg=colors["window_bg"], height=42)
        bar.grid(row=0, column=0, sticky="ew")
        bar.pack_propagate(False)

        title = tk.Label(bar, text="Todo · 便签", bg=colors["window_bg"],
                         fg=colors["text"], font=(self.family, 12, "bold"))
        title.pack(side="left", padx=(16, 0))
        enable_window_drag(bar, self.root)
        enable_window_drag(title, self.root)

        controls = tk.Frame(bar, bg=colors["window_bg"])
        controls.pack(side="right", padx=(0, 8))
        self._icon_button(controls, "✕", self._on_close)
        self._pin_btn = self._icon_button(controls, "顶", self._toggle_pin,
                                          active=self._topmost)
        self._theme_btn = self._icon_button(controls, "亮" if self.theme_name == "dark" else "暗",
                                            self._toggle_theme)

    def _icon_button(self, parent, text: str, command, active: bool = False) -> tk.Label:
        colors = self.colors
        label = tk.Label(parent, text=text, bg=colors["window_bg"],
                         fg=colors["accent"] if active else colors["muted"],
                         font=(self.family, 10, "bold"), cursor="hand2", padx=7, pady=2)
        label.pack(side="right", padx=1)
        label.bind("<Button-1>", lambda e: command())
        label.bind("<Enter>", lambda e: label.configure(bg=colors["hover"]))
        label.bind("<Leave>", lambda e: label.configure(bg=colors["window_bg"]))
        return label

    def _build_todo_section(self) -> None:
        colors = self.colors
        head = tk.Frame(self.outer, bg=colors["window_bg"])
        head.grid(row=1, column=0, sticky="ew", padx=14, pady=(4, 2))

        tk.Label(head, text="待办", bg=colors["window_bg"], fg=colors["text"],
                 font=(self.family, 10, "bold")).pack(side="left")
        self.count_label = tk.Label(head, text="0 项", bg=colors["window_bg"],
                                    fg=colors["muted"], font=(self.family, 9))
        self.count_label.pack(side="left", padx=(8, 0))

        add = tk.Label(head, text="＋ 添加", bg=colors["window_bg"], fg=colors["accent"],
                       font=(self.family, 9, "bold"), cursor="hand2")
        add.pack(side="right")
        add.bind("<Button-1>", lambda e: self._add_todo())
        add.bind("<Enter>", lambda e: add.configure(fg=colors["text"]))
        add.bind("<Leave>", lambda e: add.configure(fg=colors["accent"]))

        self.todo_scroll = ScrollableFrame(self.outer, bg=colors["window_bg"])
        self.todo_scroll.grid(row=2, column=0, sticky="nsew", padx=(8, 4), pady=(0, 6))

        sep = tk.Frame(self.outer, bg=colors["divider"], height=1)
        sep.grid(row=3, column=0, sticky="ew", padx=14, pady=(2, 4))

    def _build_note_section(self) -> None:
        colors = self.colors
        head = tk.Frame(self.outer, bg=colors["window_bg"])
        head.grid(row=4, column=0, sticky="ew", padx=14, pady=(0, 2))

        tk.Label(head, text="便签", bg=colors["window_bg"], fg=colors["text"],
                 font=(self.family, 10, "bold")).pack(side="left")
        self.saved_label = tk.Label(head, text="", bg=colors["window_bg"],
                                    fg=colors["muted"], font=(self.family, 8))
        self.saved_label.pack(side="right")

        self.note_text = tk.Text(
            self.outer, wrap="word", bg=colors["input_bg"], fg=colors["text"],
            insertbackground=colors["accent"], relief="flat", bd=0, height=6,
            highlightthickness=1, highlightbackground=colors["divider"],
            highlightcolor=colors["accent"], font=(self.family, 10),
            padx=10, pady=8, undo=True,
        )
        self.note_text.grid(row=5, column=0, sticky="nsew", padx=14, pady=(0, 12))
        self.note_text.bind("<KeyRelease>", self._on_note_edit)
        self.note_text.bind("<FocusOut>", lambda e: self._save_note_now())

    def _build_resize_grip(self) -> None:
        colors = self.colors
        grip = tk.Label(self.outer, text="◢", bg=colors["window_bg"], fg=colors["muted"],
                        font=(self.symbol, 9), cursor="size_nw_se")
        grip.place(relx=1.0, rely=1.0, anchor="se")
        grip.bind("<Button-1>", self._resize_press)
        grip.bind("<B1-Motion>", self._resize_drag)

    # ------------------------------------------------------------------
    # 待办渲染
    # ------------------------------------------------------------------
    def refresh_todos(self) -> None:
        colors = self.colors
        for child in self.todo_scroll.inner.winfo_children():
            child.destroy()
        self._todos = self.service.list()
        self._row_frames = []

        if not self._todos:
            tk.Label(self.todo_scroll.inner, text="暂无待办，点右上「＋ 添加」",
                     bg=colors["window_bg"], fg=colors["muted"],
                     font=(self.family, 9), pady=18).pack(fill="x")
        else:
            for todo in self._todos:
                row = self._build_row(self.todo_scroll.inner, todo)
                self._row_frames.append((todo.id, row))

        self.count_label.config(text=f"{len(self._todos)} 项")
        self.todo_scroll.attach(self.todo_scroll.inner)
        self.root.after_idle(self.todo_scroll.refresh_scrollregion)

    def _build_row(self, parent: tk.Misc, todo: Todo) -> tk.Frame:
        colors = self.colors
        row = tk.Frame(parent, bg=colors["window_bg"])
        row.pack(fill="x", pady=1)

        mark = "☑" if todo.done else "☐"
        chk = tk.Label(row, text=mark, bg=colors["window_bg"],
                       fg=colors["done"] if todo.done else colors["accent"],
                       font=(self.symbol, 12), cursor="hand2")
        chk.pack(side="left", padx=(4, 6))
        chk.bind("<Button-1>", lambda e, tid=todo.id: self._toggle(tid))

        text_box = tk.Frame(row, bg=colors["window_bg"])
        text_box.pack(side="left", fill="x", expand=True)

        title_fg = colors["done"] if todo.done else colors["text"]
        title_font = (self.family, 10, "overstrike") if todo.done else (self.family, 10)
        title = tk.Label(text_box, text=todo.display_title, bg=colors["window_bg"],
                         fg=title_fg, font=title_font, anchor="w", justify="left")
        title.pack(fill="x", anchor="w")
        text_box.bind("<Configure>",
                      lambda e, lbl=title: lbl.configure(wraplength=max(80, e.width - 4)))

        meta = None
        if todo.meta_text:
            meta = tk.Label(text_box, text=todo.meta_text, bg=colors["window_bg"],
                            fg=colors["muted"], font=(self.family, 8), anchor="w")
            meta.pack(fill="x", anchor="w")

        grip = tk.Label(row, text="≡", bg=colors["window_bg"], fg=colors["muted"],
                        font=(self.family, 12), cursor="fleur")
        grip.pack(side="right", padx=(4, 6))
        grip.bind("<Button-1>", lambda e, tid=todo.id: self._drag_press(e, tid))
        grip.bind("<B1-Motion>", self._drag_motion)
        grip.bind("<ButtonRelease-1>", self._drag_release)

        # 双击编辑 / 右键菜单
        text_widgets = [w for w in (title, meta) if w is not None]
        for widget in [row, text_box, chk, grip] + text_widgets:
            widget.bind("<Button-3>", lambda e, tid=todo.id: self._popup_menu(e, tid))
        for widget in [text_box] + text_widgets:
            widget.bind("<Double-Button-1>", lambda e, tid=todo.id: self._edit_todo(tid))

        return row

    # ------------------------------------------------------------------
    # 待办操作
    # ------------------------------------------------------------------
    def _add_todo(self) -> None:
        dialog = TodoDialog(self.root, self.service, self.colors, None)
        self.root.wait_window(dialog)
        if dialog.result:
            self.refresh_todos()
            self.todo_scroll.scroll_to_top()

    def _edit_todo(self, todo_id: int) -> None:
        todo = self.service.get(todo_id)
        if todo is None:
            return
        dialog = TodoDialog(self.root, self.service, self.colors, todo)
        self.root.wait_window(dialog)
        if dialog.result:
            self.refresh_todos()

    def _toggle(self, todo_id: int) -> None:
        self.service.toggle(todo_id)
        self.refresh_todos()

    def _move(self, todo_id: int, delta: int) -> None:
        if self.service.move(todo_id, delta):
            self.refresh_todos()

    def _delete(self, todo_id: int) -> None:
        todo = self.service.get(todo_id)
        if todo is None:
            return
        if not messagebox.askyesno(
                "删除待办", f"确定删除「{todo.display_title}」吗？", parent=self.root):
            return
        self.service.delete(todo_id)
        self.refresh_todos()

    def _popup_menu(self, event, todo_id: int) -> None:
        colors = self.colors
        menu = tk.Menu(self.root, tearoff=0, bg=colors["panel"], fg=colors["text"],
                       activebackground=colors["accent"], activeforeground=colors["window_bg"],
                       bd=0, activeborderwidth=0)
        menu.add_command(label="编辑", command=lambda: self._edit_todo(todo_id))
        menu.add_command(label="上移", command=lambda: self._move(todo_id, -1))
        menu.add_command(label="下移", command=lambda: self._move(todo_id, 1))
        menu.add_separator()
        menu.add_command(label="删除", command=lambda: self._delete(todo_id))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    # ---------------- 拖拽排序 ----------------
    def _drag_press(self, event, todo_id: int) -> None:
        self._drag_tid = todo_id

    def _drag_motion(self, event) -> None:
        return None

    def _drag_release(self, event) -> None:
        todo_id = self._drag_tid
        self._drag_tid = None
        if todo_id is None:
            return
        y = event.y_root
        final_index = len(self._todos) - 1
        for index, (_, frame) in enumerate(self._row_frames):
            top = frame.winfo_rooty()
            height = frame.winfo_height() or 28
            if y < top + height / 2:
                final_index = index
                break
        self.service.move_to_index(todo_id, final_index)
        self.refresh_todos()

    # ------------------------------------------------------------------
    # 便签
    # ------------------------------------------------------------------
    def _load_note(self) -> None:
        note = self.service.get_note()
        self._note_cache = note.content
        self.note_text.delete("1.0", "end")
        if note.content:
            self.note_text.insert("1.0", note.content)
        self.saved_label.config(text="")

    def _on_note_edit(self, _event=None) -> None:
        if self._note_job is not None:
            try:
                self.root.after_cancel(self._note_job)
            except tk.TclError:
                pass
        self._note_job = self.root.after(700, self._save_note_now)

    def _save_note_now(self) -> None:
        self._note_job = None
        try:
            content = self.note_text.get("1.0", "end-1c")
        except tk.TclError:
            return
        if content != self._note_cache:
            self.service.save_note(content)
            self._note_cache = content
            self.saved_label.config(text="已保存", fg=self.colors["accent"])
            self.root.after(1500, lambda: self._reset_saved_label())

    def _reset_saved_label(self) -> None:
        try:
            self.saved_label.config(text="", fg=self.colors["muted"])
        except tk.TclError:
            pass

    # ------------------------------------------------------------------
    # 主题 / 置顶 / 缩放 / 关闭
    # ------------------------------------------------------------------
    def _toggle_theme(self) -> None:
        self._save_note_now()
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self.colors = theme.get_theme(self.theme_name)
        self._apply_window_attrs()
        self.root.configure(bg=self.colors["window_bg"])
        for child in self.root.winfo_children():
            child.destroy()
        self._build()
        self.refresh_todos()
        self._load_note()
        self._save_settings()

    def _toggle_pin(self) -> None:
        self._topmost = not self._topmost
        try:
            self.root.attributes("-topmost", self._topmost)
        except tk.TclError:
            pass
        self._pin_btn.configure(fg=self.colors["accent"] if self._topmost else self.colors["muted"])
        self._save_settings()

    def _resize_press(self, event) -> None:
        self._resize_state = (event.x_root, event.y_root,
                              self.root.winfo_width(), self.root.winfo_height())

    def _resize_drag(self, event) -> None:
        if not self._resize_state:
            return
        x0, y0, w0, h0 = self._resize_state
        width = max(300, w0 + (event.x_root - x0))
        height = max(360, h0 + (event.y_root - y0))
        self.root.geometry(f"{width}x{height}")

    def _on_close(self) -> None:
        self._save_note_now()
        self._save_settings()
        self.root.destroy()
