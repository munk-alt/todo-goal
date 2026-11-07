"""应用入口。

用法：
  python app.py            正常启动
  python app.py --hidden   静默启动（隐藏到后台，用 Ctrl+Shift+空格 唤出）
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

from todo.hotkey import SHOW_EVENT_NAME  # noqa: E402
from todo.service import TodoService  # noqa: E402
from todo.storage import TaskRepository  # noqa: E402
from todo.ui.main_window import MainWindow  # noqa: E402

WINDOW_TITLE = "Todo · 便签"


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


def single_instance_guard():
    """只允许一个实例；若已存在，则把已有窗口唤到前台并返回 (False, handle)。"""
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        kernel32.CreateMutexW.restype = ctypes.c_void_p
        kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
        mutex = kernel32.CreateMutexW(None, False, "Local\\TodoStickyNotesApp_v2")
        if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            # 先尝试通过命名事件唤醒已有实例
            try:
                kernel32.OpenEventW.restype = ctypes.c_void_p
                kernel32.OpenEventW.argtypes = [ctypes.c_uint, ctypes.c_bool, ctypes.c_wchar_p]
                kernel32.SetEvent.argtypes = [ctypes.c_void_p]
                event = kernel32.OpenEventW(0x0002, False, SHOW_EVENT_NAME)
                if event:
                    kernel32.SetEvent(event)
                    return False, mutex
            except Exception:  # noqa: BLE001
                pass
            # 退回：按标题找窗口并显示
            user32 = ctypes.windll.user32
            user32.FindWindowW.restype = ctypes.c_void_p
            user32.FindWindowW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
            user32.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
            user32.SetForegroundWindow.argtypes = [ctypes.c_void_p]
            hwnd = user32.FindWindowW(None, WINDOW_TITLE)
            if hwnd:
                user32.ShowWindow(hwnd, 5)  # SW_SHOW
                user32.SetForegroundWindow(hwnd)
            return False, mutex
        return True, mutex
    except Exception:  # noqa: BLE001
        return True, None


def main() -> int:
    hidden = "--hidden" in sys.argv[1:]
    first, mutex = single_instance_guard()
    if not first:
        return 0

    enable_dpi_awareness()
    data_dir = app_data_dir()
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
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
    root.title(WINDOW_TITLE)
    root._mutex = mutex  # 保持互斥量句柄存活
    try:
        app = MainWindow(root, service, data_dir)
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        messagebox.showerror("启动失败", "界面初始化失败，详情见控制台输出。")
        root.destroy()
        repo.close()
        return 1

    # 静默启动且快捷键可用时才隐藏；快捷键不可用则正常显示，避免无法唤出
    if hidden and getattr(app, "hotkey_ok", False):
        root.withdraw()

    root.mainloop()
    repo.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
