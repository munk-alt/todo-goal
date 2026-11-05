"""开发辅助：向指定数据库写入演示数据（用于截图/手工验收）。

用法： python scripts/seed_demo.py <db_path>
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from todo.service import TodoService  # noqa: E402
from todo.storage import TaskRepository  # noqa: E402


def main(db_path: str) -> int:
    repo = TaskRepository(db_path)
    service = TodoService(repo)

    service.add("周三 上午 9:00", "3 楼会议室", "参加部门月度例会")
    service.add("周四 下午 5:00", "金融中心", "培训课程")
    service.add("周日 上午 10:00", "虹桥机场", "飞往上海出差")
    service.add("周五 19:30", "老地方", "小组聚会")
    service.add("下个周末", "老家", "回家看看父母")
    service.add("", "超市", "下班去超市买猫粮")
    service.add("明天 15:00", "理发店", "预约 tong 老师剪头发")

    service.save_note("便签示例：\n- 记得带身份证\n- 本周内提交报销单据\n- 给妈妈打个电话")
    print(f"seeded {len(service.list())} todos into {db_path}")
    repo.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else ":memory:"))
