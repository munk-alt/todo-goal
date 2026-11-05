"""无控制台窗口启动入口（双击本文件即可运行）。

等价于 `pythonw TodoApp.pyw`，无需打包 exe 也能像应用一样双击启动。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
