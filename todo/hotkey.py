"""Windows 全局快捷键（RegisterHotKey + 独立消息循环线程）。

默认组合：Ctrl + Shift + 空格。
回调在热键线程中触发，调用方应自行转到 GUI 线程（例如放入 queue，再在 Tk 里轮询）。
"""

from __future__ import annotations

import ctypes
import threading
from ctypes import wintypes

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

WM_HOTKEY = 0x0312
WM_QUIT = 0x0012

VK_SPACE = 0x20
VK_N = 0x4E

# 单实例唤醒用命名事件
SHOW_EVENT_NAME = "Local\\TodoStickyShowEvent_v2"
EVENT_MODIFY_STATE = 0x0002


class GlobalHotkey(threading.Thread):
    def __init__(self, callback, modifiers: int = MOD_CONTROL | MOD_SHIFT,
                 vk: int = VK_SPACE, hotkey_id: int = 0xA11CE):
        super().__init__(daemon=True)
        self.callback = callback
        self.modifiers = modifiers
        self.vk = vk
        self.hotkey_id = hotkey_id
        self.registered = False
        self.error: int | None = None
        self._ready = threading.Event()
        self._thread_id: int | None = None

    def run(self) -> None:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        self._thread_id = kernel32.GetCurrentThreadId()
        ctypes.set_last_error(0)
        ok = user32.RegisterHotKey(None, self.hotkey_id, self.modifiers | MOD_NOREPEAT, self.vk)
        self.registered = bool(ok)
        if not ok:
            self.error = ctypes.get_last_error()
            self._ready.set()
            return
        self._ready.set()

        msg = wintypes.MSG()
        try:
            while True:
                ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if ret == 0 or ret == -1:
                    break
                if msg.message == WM_HOTKEY and int(msg.wParam) == self.hotkey_id:
                    try:
                        self.callback()
                    except Exception:  # noqa: BLE001
                        pass
        finally:
            user32.UnregisterHotKey(None, self.hotkey_id)

    def start_and_wait(self, timeout: float = 1.5) -> bool:
        self.start()
        self._ready.wait(timeout)
        return self.registered

    def stop(self) -> None:
        if self._thread_id:
            try:
                ctypes.windll.user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
            except Exception:  # noqa: BLE001
                pass
