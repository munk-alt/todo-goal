"""应用入口。

用法： python app.py
打包： 见 build.ps1
"""

from __future__ import annotations

import os
import sys
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

# 确保以脚本方式运行时能导入 todo 包
sys.path.insert(0, str(Path(__file__).resolve().parent))

from todo.service import TodoService  # noqa: E402
from todo.storage import TaskRepository  # noqa: E402
from todo.ui.main_window import MainWindow  # noqa: E402


def app_data_dir() -> Path:
    base = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or str(Path.home())
    return Path(base) / "TodoApp"


def enable_dpi_awareness() -> None:
    """让窗口在高分屏下清晰、坐标与真实像素一致。"""
    try:
        import ctypes

        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # 按显示器 DPI 感知
        except Exception:  # noqa: BLE001
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:  # noqa: BLE001
        pass


def main() -> int:
    enable_dpi_awareness()
    data_dir = app_data_dir()
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        # 回退到程序目录下的 data 文件夹
        data_dir = Path(__file__).resolve().parent / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

    db_path = data_dir / "todo.db"
    try:
        repo = TaskRepository(str(db_path))
    except Exception as exc:  # noqa: BLE001
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "启动失败",
            f"无法打开数据库：\n{db_path}\n\n{exc}\n\n"
            "请检查该路径是否可写，或删除损坏的数据库文件后重试。",
        )
        root.destroy()
        return 1

    service = TodoService(repo)
    root = tk.Tk()
    root.title("Todo · 便签")
    try:
        MainWindow(root, service, data_dir)
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        messagebox.showerror("启动失败", "界面初始化失败，详情见控制台输出。")
        root.destroy()
        repo.close()
        return 1

    root.mainloop()
    repo.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
