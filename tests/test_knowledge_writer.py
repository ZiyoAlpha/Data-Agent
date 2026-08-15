import tempfile
from pathlib import Path
import unittest

from app.knowledge_base import LocalKnowledgeBase
from app.knowledge_writer import KnowledgeWriteError, LocalKnowledgeWriter


SECTIONS = {
    "metrics",
    "tables",
    "patterns",
    "contracts",
    "queries",
    "cases",
    "rules",
    "skills",
    "precedents/fields",
    "precedents/schema-changes",
    "precedents/decisions",
}


class KnowledgeWriterTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for section in SECTIONS:
            (self.root / section).mkdir(parents=True, exist_ok=True)
        self.index = LocalKnowledgeBase(self.root)
        self.writer = LocalKnowledgeWriter(self.root, self.index)

    def tearDown(self):
        self.temp.cleanup()

    def test_write_is_atomic_and_incrementally_indexed(self):
        result = self.writer.write_markdown(
            section="metrics",
            slug="example-task-rate",
            title="示例任务完成率",
            summary="完全虚构的演示指标",
            body="完成任务数除以提交任务数，仅用于演示。",
            source_ref="tables/example-tasks.md",
        )

        self.assertEqual(result.path, "metrics/example-task-rate.md")
        self.assertTrue(result.indexed)
        self.assertTrue((self.root / result.path).is_file())
        self.assertEqual(self.index.search("任务完成率")[0].path, result.path)

    def test_existing_document_requires_explicit_overwrite(self):
        payload = {
            "section": "rules",
            "slug": "example-rule",
            "title": "示例规则",
            "summary": "虚构规则",
            "body": "这是不对应任何真实系统的规则。",
        }
        self.writer.write_markdown(**payload)
        with self.assertRaises(KnowledgeWriteError):
            self.writer.write_markdown(**payload)

    def test_rejects_invalid_section_slug_and_secret(self):
        base = {
            "section": "metrics",
            "slug": "safe-name",
            "title": "安全示例",
            "summary": "虚构说明",
            "body": "普通演示正文",
        }
        for update in (
            {"section": "../outside"},
            {"slug": "../outside"},
            {"body": "secret " + "sk-" + "exampleabcdefghijklmnop"},
        ):
            with self.subTest(update=update):
                with self.assertRaises(KnowledgeWriteError):
                    self.writer.write_markdown(**{**base, **update})


if __name__ == "__main__":
    unittest.main()
