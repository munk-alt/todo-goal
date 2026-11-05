"""UI 冒烟测试（便笺风）：构建主窗口、验证渲染与基本操作后自动关闭。

运行： python scripts/smoke_ui.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import tkinter as tk  # noqa: E402

from todo.service import TodoService  # noqa: E402
from todo.storage import TaskRepository  # noqa: E402
from todo.ui.main_window import MainWindow  # noqa: E402


def main() -> int:
    tmp = Path(__file__).resolve().parent / "_smoke_data"
    tmp.mkdir(parents=True, exist_ok=True)

    repo = TaskRepository(":memory:")
    service = TodoService(repo)
    service.add("周三 9:00", "会议室", "部门月度例会")
    service.add("", "", "下班去超市买猫粮")
    service.add("周日 10:00", "虹桥机场", "飞上海出差")
    service.save_note("备忘：记得带身份证\n出差报销单据")

    root = tk.Tk()
    app = MainWindow(root, service, tmp)
    root.update_idletasks()
    root.update()

    print("todos rendered:", len(app._todos))
    assert len(app._todos) == 3
    assert app.note_text.get("1.0", "end-1c").startswith("备忘")

    # 完成切换
    app._toggle(app._todos[0].id)
    root.update()
    print("done count:", app.service.counts()["done"])
    assert app.service.counts()["done"] == 1

    # 排序：把最后一条移到最前
    last_id = app._todos[-1].id
    app.service.move_to_index(last_id, 0)
    app.refresh_todos()
    root.update()
    print("first id:", app._todos[0].id)
    assert app._todos[0].id == last_id

    # 便签保存
    app._save_note_now()
    assert app.service.get_note().content.startswith("备忘")
    print("note ok")

    # 对话框新增
    from todo.ui.todo_dialog import TodoDialog

    before = len(app.service.list())
    dlg = TodoDialog(root, service, app.colors, None)
    dlg._time_entry.insert(0, "明天 10:00")
    dlg._place_entry.insert(0, "公司")
    dlg._content_entry.insert(0, "测试新增项")
    dlg._save()
    root.update()
    assert dlg.result is not None and dlg.result.content_text == "测试新增项"
    assert len(app.service.list()) == before + 1
    print("dialog add ok")

    root.after(150, root.destroy)
    root.update()
    print("SMOKE OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
