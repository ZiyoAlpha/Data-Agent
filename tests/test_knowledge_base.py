import tempfile
from pathlib import Path
import unittest

from app.knowledge_base import LocalKnowledgeBase, cjk_bigram


class KnowledgeBaseTest(unittest.TestCase):
    def test_cjk_expansion(self):
        tokens = cjk_bigram("知识库 agent")
        self.assertIn("知识", tokens)
        self.assertIn("识库", tokens)
        self.assertIn("知", tokens)
        self.assertIn("知识库", tokens)
        self.assertIn("agent", tokens)

    def test_rebuild_skips_readme_and_searches_documents(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("说明文件不应进入索引", encoding="utf-8")
            (root / "guide.md").write_text("本地知识库支持中文全文检索。", encoding="utf-8")
            kb = LocalKnowledgeBase(root)

            report = kb.rebuild()
            results = kb.search("知识库")

            self.assertEqual(report["indexed"], 1)
            self.assertEqual(kb.stats()["documentCount"], 1)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].path, "guide.md")
            self.assertEqual(results[0].score, 1.0)

    def test_empty_directory_is_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            kb = LocalKnowledgeBase(Path(directory))
            report = kb.rebuild()
            self.assertEqual(report["indexed"], 0)
            self.assertEqual(kb.search("anything"), [])


if __name__ == "__main__":
    unittest.main()

