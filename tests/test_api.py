import unittest
from unittest.mock import patch
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.knowledge_base import LocalKnowledgeBase
from app.knowledge_writer import LocalKnowledgeWriter, SECTION_DESCRIPTIONS
from app.llm import KnowledgeDraft, KnowledgeDraftResult


class FakeChatWriteLLM:
    def create_knowledge_draft(self, question, history):
        return KnowledgeDraftResult(
            draft=KnowledgeDraft(
                ready=True,
                section="rules",
                slug="example-api-rule",
                title="示例接口规则",
                summary="完全虚构的聊天写入示例",
                body="收到示例任务后，先验证输入是否完整。",
                source_ref="",
                confidence="draft",
                missing_information="",
            ),
            model="test-model",
            usage={"inputTokens": 10, "outputTokens": 6, "cachedTokens": 0},
        )


class ApiTest(unittest.TestCase):
    def test_status_and_empty_search(self):
        with TestClient(app) as client:
            status = client.get("/api/status")
            search = client.post("/api/search", json={"query": "nothing", "topK": 3})

        self.assertEqual(status.status_code, 200)
        self.assertTrue(status.json()["ok"])
        self.assertNotIn("apiKey", status.json())
        self.assertEqual(search.status_code, 200)
        self.assertEqual(search.json()["results"], [])

    def test_home_page(self):
        with TestClient(app) as client:
            response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Database DataAgent Lite", response.text)

    def test_write_endpoint_uses_safe_writer_and_updates_index(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for section in SECTION_DESCRIPTIONS:
                (root / section).mkdir(parents=True, exist_ok=True)
            index = LocalKnowledgeBase(root)
            writer = LocalKnowledgeWriter(root, index)
            payload = {
                "section": "metrics",
                "slug": "example-success-rate",
                "title": "示例成功率",
                "summary": "完全虚构的接口测试指标",
                "body": "成功的示例任务数除以全部示例任务数。",
                "confidence": "draft",
            }

            with patch("app.main.knowledge_writer", writer), TestClient(app) as client:
                response = client.post("/api/knowledge/documents", json=payload)

            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.json()["path"], "metrics/example-success-rate.md")
            self.assertTrue(response.json()["indexed"])
            self.assertEqual(index.search("示例成功率")[0].path, response.json()["path"])

    def test_chat_can_persist_only_after_explicit_user_request(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for section in SECTION_DESCRIPTIONS:
                (root / section).mkdir(parents=True, exist_ok=True)
            index = LocalKnowledgeBase(root)
            writer = LocalKnowledgeWriter(root, index)

            with (
                patch("app.main.llm", FakeChatWriteLLM()),
                patch("app.main.knowledge_writer", writer),
                TestClient(app) as client,
            ):
                response = client.post(
                    "/api/chat",
                    json={
                        "question": "帮我把刚才的规则沉淀到知识库",
                        "history": [
                            {"role": "user", "content": "请先验证示例输入。"}
                        ],
                    },
                )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["knowledgeWrite"]["status"], "created")
            self.assertTrue((root / "rules/example-api-rule.md").is_file())


if __name__ == "__main__":
    unittest.main()
