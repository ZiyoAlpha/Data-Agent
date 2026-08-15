import tempfile
from pathlib import Path
import unittest

from app.knowledge_action import KnowledgeActionService
from app.knowledge_base import LocalKnowledgeBase
from app.knowledge_writer import LocalKnowledgeWriter, SECTION_DESCRIPTIONS
from app.llm import KnowledgeDraft, KnowledgeDraftResult


class FakeDraftLLM:
    def __init__(self, draft: KnowledgeDraft):
        self.draft = draft

    def create_knowledge_draft(self, question, history):
        return KnowledgeDraftResult(
            draft=self.draft,
            model="test-model",
            usage={"inputTokens": 12, "outputTokens": 8, "cachedTokens": 0},
        )


def make_draft(**updates) -> KnowledgeDraft:
    values = {
        "ready": True,
        "section": "rules",
        "slug": "example-review-rule",
        "title": "示例复核规则",
        "summary": "完全虚构的复核流程规则",
        "body": "示例任务完成后，应由另一位示例成员复核结果。",
        "source_ref": "",
        "confidence": "draft",
        "missing_information": "",
    }
    values.update(updates)
    return KnowledgeDraft(**values)


class KnowledgeActionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for section in SECTION_DESCRIPTIONS:
            (self.root / section).mkdir(parents=True, exist_ok=True)
        self.index = LocalKnowledgeBase(self.root)
        self.writer = LocalKnowledgeWriter(self.root, self.index)

    def tearDown(self):
        self.temp.cleanup()

    def service(self, draft: KnowledgeDraft) -> KnowledgeActionService:
        return KnowledgeActionService(FakeDraftLLM(draft), self.writer)

    def test_explicit_request_creates_and_indexes_document(self):
        response = self.service(make_draft()).handle(
            "帮我把刚才的规则沉淀到知识库",
            [{"role": "user", "content": "所有示例任务都需要复核。"}],
        )

        self.assertEqual(response["knowledgeWrite"]["status"], "created")
        self.assertEqual(response["knowledgeWrite"]["path"], "rules/example-review-rule.md")
        self.assertTrue(response["knowledgeWrite"]["indexed"])
        self.assertTrue((self.root / "rules/example-review-rule.md").is_file())
        self.assertEqual(self.index.search("复核规则")[0].path, "rules/example-review-rule.md")

    def test_existing_document_requires_a_separate_confirmation(self):
        service = self.service(make_draft())
        service.handle("帮我沉淀到知识库", [])

        response = service.handle("帮我再次沉淀到知识库", [])

        self.assertEqual(
            response["knowledgeWrite"]["status"],
            "confirmation_required",
        )
        self.assertIn("确认覆盖知识库文档 rules/example-review-rule.md", response["answer"])

    def test_explicit_confirmation_replaces_only_the_named_document(self):
        self.service(make_draft(body="旧的虚构规则。")).handle(
            "帮我沉淀到知识库",
            [],
        )
        replacement = make_draft(
            section="metrics",
            slug="ignored-model-target",
            title="更新后的示例复核规则",
            body="新的虚构规则。",
        )

        response = self.service(replacement).handle(
            "确认覆盖知识库文档 rules/example-review-rule.md",
            [],
        )

        self.assertEqual(response["knowledgeWrite"]["status"], "replaced")
        self.assertEqual(response["knowledgeWrite"]["path"], "rules/example-review-rule.md")
        content = (self.root / "rules/example-review-rule.md").read_text(encoding="utf-8")
        self.assertIn("新的虚构规则", content)
        self.assertFalse((self.root / "metrics/ignored-model-target.md").exists())

    def test_incomplete_draft_does_not_create_a_file(self):
        draft = make_draft(
            ready=False,
            missing_information="缺少规则适用范围",
            title="",
            summary="",
            body="",
        )

        response = self.service(draft).handle("帮我沉淀到知识库", [])

        self.assertEqual(response["knowledgeWrite"]["status"], "needs_input")
        self.assertIn("缺少规则适用范围", response["answer"])
        self.assertFalse(any(self.root.rglob("*.md")))


if __name__ == "__main__":
    unittest.main()
