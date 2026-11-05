"""主题配色与字体（便笺风：浅黑 / 浅白两套半透明主题）。"""

from __future__ import annotations

import tkinter as tk
from tkinter import font

FONT_FAMILY_CANDIDATES = [
    "Microsoft YaHei UI",
    "Microsoft YaHei",
    "Segoe UI",
    "SimHei",
    "Arial",
]

# 图标使用符号字体，尽量保证 ☐ ☑ ≡ ✕ 等能正常显示
SYMBOL_FONTS = ["Segoe UI Symbol", "Segoe UI Emoji", "Microsoft YaHei UI"]

THEMES = {
    "dark": {
        "name": "dark",
        "window_bg": "#202124",   # 浅黑
        "panel": "#26282c",
        "text": "#e8eaed",
        "muted": "#8b9096",
        "done": "#5f6368",
        "accent": "#f2c94c",      # 小黄条式强调色
        "divider": "#34373c",
        "input_bg": "#2a2c30",
        "badge_bg": "#34373c",
        "badge_fg": "#d6d9dd",
        "hover": "#303338",
        "alpha": 0.95,
    },
    "light": {
        "name": "light",
        "window_bg": "#f7f7f4",   # 浅白
        "panel": "#ffffff",
        "text": "#2b2c2e",
        "muted": "#8a8f98",
        "done": "#b3b7bd",
        "accent": "#e0a800",
        "divider": "#e4e6ea",
        "input_bg": "#f0f1f3",
        "badge_bg": "#eceef1",
        "badge_fg": "#5f6368",
        "hover": "#eeeef0",
        "alpha": 0.97,
    },
}

_FONT_FAMILY = "Microsoft YaHei UI"


def get_theme(name: str) -> dict:
    return THEMES.get(name, THEMES["dark"])


def pick_font_family(root: tk.Misc) -> str:
    global _FONT_FAMILY
    try:
        available = set(font.families(root))
    except tk.TclError:
        available = set()
    for candidate in FONT_FAMILY_CANDIDATES:
        if candidate in available:
            _FONT_FAMILY = candidate
            return candidate
    _FONT_FAMILY = "Segoe UI"
    return _FONT_FAMILY


def font_family() -> str:
    return _FONT_FAMILY


def pick_symbol_font(root: tk.Misc) -> str:
    try:
        available = set(font.families(root))
    except tk.TclError:
        available = set()
    for candidate in SYMBOL_FONTS:
        if candidate in available:
            return candidate
    return _FONT_FAMILY
