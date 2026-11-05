"""可复用的小部件：可滚动容器、窗口拖动、文本占位。"""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional


class ScrollableFrame(tk.Frame):
    """一个带滚动的容器：内容放在 ``inner`` 里。

    - 画布宽度随容器变化；
    - 使用鼠标滚轮滚动（通过 ``attach`` 把滚轮事件绑定到子控件）。
    """

    def __init__(self, master, bg: str, **kwargs):
        super().__init__(master, bg=bg, **kwargs)
        self._bg = bg
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner = tk.Frame(self.canvas, bg=bg)
        self._window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.inner.bind("<MouseWheel>", self._on_wheel)

    def _on_inner_configure(self, _event=None) -> None:
        bbox = self.canvas.bbox("all")
        self.canvas.configure(scrollregion=bbox or (0, 0, 0, 0))

    def _on_canvas_configure(self, event) -> None:
        self.canvas.itemconfigure(self._window, width=event.width)

    def _on_wheel(self, event):
        delta = int(-event.delta / 120) if event.delta else 0
        if delta:
            self.canvas.yview_scroll(delta, "units")
        return "break"

    def attach(self, widget: tk.Misc) -> None:
        """递归地把滚轮事件绑定到 widget 及其子控件。"""
        try:
            widget.bind("<MouseWheel>", self._on_wheel)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self.attach(child)

    def refresh_scrollregion(self) -> None:
        self.inner.update_idletasks()
        bbox = self.canvas.bbox("all")
        self.canvas.configure(scrollregion=bbox or (0, 0, 0, 0))

    def scroll_to_top(self) -> None:
        self.canvas.yview_moveto(0)


def enable_window_drag(handle: tk.Misc, window: tk.Misc, on_move: Optional[Callable] = None) -> None:
    """按住 handle 拖动 window。"""
    state = {"dx": 0, "dy": 0}

    def _press(event):
        state["dx"] = event.x_root - window.winfo_x()
        state["dy"] = event.y_root - window.winfo_y()

    def _move(event):
        x = event.x_root - state["dx"]
        y = event.y_root - state["dy"]
        window.geometry(f"+{x}+{y}")
        if on_move:
            on_move()

    handle.bind("<Button-1>", _press)
    handle.bind("<B1-Motion>", _move)


def bind_recursive(widget: tk.Misc, sequence: str, callback) -> None:
    try:
        widget.bind(sequence, callback)
    except tk.TclError:
        pass
    for child in widget.winfo_children():
        bind_recursive(child, sequence, callback)
