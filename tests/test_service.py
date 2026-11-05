"""存储层与业务层单元测试（便笺风待办版）。

运行： python -m unittest discover -s tests -v
"""

import os
import shutil
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from todo.models import Todo  # noqa: E402
from todo.service import TodoService, ValidationError  # noqa: E402
from todo.storage import TaskRepository  # noqa: E402


class TodoServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.repo = TaskRepository(":memory:")
        self.service = TodoService(self.repo)

    def tearDown(self):
        self.repo.close()

    # ---- 新增与校验 ----
    def test_add_requires_content(self):
        with self.assertRaises(ValidationError):
            self.service.add(time_text="明天", place_text="公司", content_text="   ")

    def test_add_fields_stored(self):
        t = self.service.add(time_text="周三 9:00", place_text="会议室", content_text="月度例会")
        self.assertIsNotNone(t.id)
        got = self.service.get(t.id)
        self.assertEqual(got.time_text, "周三 9:00")
        self.assertEqual(got.place_text, "会议室")
        self.assertEqual(got.content_text, "月度例会")
        self.assertFalse(got.done)

    def test_fields_are_stripped(self):
        t = self.service.add(time_text="  今天  ", place_text=" 家 ", content_text="  买菜  ")
        self.assertEqual(t.time_text, "今天")
        self.assertEqual(t.place_text, "家")
        self.assertEqual(t.content_text, "买菜")

    def test_append_order(self):
        a = self.service.add(content_text="A")
        b = self.service.add(content_text="B")
        c = self.service.add(content_text="C")
        self.assertEqual([t.id for t in self.service.list()], [a.id, b.id, c.id])

    # ---- 更新 / 完成 / 删除 ----
    def test_update(self):
        t = self.service.add(content_text="旧内容")
        t.content_text = "新内容"
        t.place_text = "新地点"
        self.service.update(t)
        got = self.service.get(t.id)
        self.assertEqual(got.content_text, "新内容")
        self.assertEqual(got.place_text, "新地点")

    def test_toggle_done(self):
        t = self.service.add(content_text="完成我")
        t2 = self.service.toggle(t.id)
        self.assertTrue(t2.done)
        t3 = self.service.toggle(t.id)
        self.assertFalse(t3.done)

    def test_delete(self):
        t = self.service.add(content_text="删除")
        self.assertTrue(self.service.delete(t.id))
        self.assertIsNone(self.service.get(t.id))
        self.assertFalse(self.service.delete(t.id))

    # ---- 排序 ----
    def test_move_up_down(self):
        a = self.service.add(content_text="A")
        b = self.service.add(content_text="B")
        c = self.service.add(content_text="C")

        self.assertTrue(self.service.move(c.id, -1))
        self.assertEqual([t.id for t in self.service.list()], [a.id, c.id, b.id])

        self.assertTrue(self.service.move(a.id, 1))
        self.assertEqual([t.id for t in self.service.list()], [c.id, a.id, b.id])

        # 越界不生效
        self.assertFalse(self.service.move(c.id, -1))

    def test_move_to_index(self):
        a = self.service.add(content_text="A")
        b = self.service.add(content_text="B")
        c = self.service.add(content_text="C")
        self.assertTrue(self.service.move_to_index(c.id, 0))
        self.assertEqual([t.id for t in self.service.list()], [c.id, a.id, b.id])

    def test_reorder(self):
        a = self.service.add(content_text="A")
        b = self.service.add(content_text="B")
        c = self.service.add(content_text="C")
        self.service.reorder([b.id, c.id, a.id])
        self.assertEqual([t.id for t in self.service.list()], [b.id, c.id, a.id])

    # ---- 计数 ----
    def test_counts(self):
        a = self.service.add(content_text="A")
        self.service.add(content_text="B")
        self.service.toggle(a.id)
        c = self.service.counts()
        self.assertEqual(c["total"], 2)
        self.assertEqual(c["done"], 1)
        self.assertEqual(c["active"], 1)

    # ---- 便签 ----
    def test_note_default_empty(self):
        note = self.service.get_note()
        self.assertEqual(note.content, "")

    def test_note_save_and_reload(self):
        self.service.save_note("今天要记的一段话\n第二行")
        note = self.service.get_note()
        self.assertEqual(note.content, "今天要记的一段话\n第二行")
        self.assertTrue(note.updated_at)

    def test_note_overwrite(self):
        self.service.save_note("第一次")
        self.service.save_note("第二次")
        self.assertEqual(self.service.get_note().content, "第二次")


class RepositoryPersistenceTestCase(unittest.TestCase):
    def test_persistence_file(self):
        tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp_db")
        shutil.rmtree(tmp, ignore_errors=True)
        os.makedirs(tmp, exist_ok=True)
        try:
            db = os.path.join(tmp, "sub", "todo.db")
            repo = TaskRepository(db)
            svc = TodoService(repo)
            svc.add(time_text="明天", place_text="超市", content_text="买猫粮")
            svc.save_note("便签内容")
            repo.close()

            repo2 = TaskRepository(db)
            svc2 = TodoService(repo2)
            todos = svc2.list()
            self.assertEqual(len(todos), 1)
            self.assertEqual(todos[0].content_text, "买猫粮")
            self.assertEqual(svc2.get_note().content, "便签内容")
            repo2.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
