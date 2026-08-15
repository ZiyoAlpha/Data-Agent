import unittest
from unittest.mock import patch
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.knowledge_base import LocalKnowledgeBase
from app.knowledge_writer import LocalKnowledgeWriter, SECTION_DESCRIPTIONS


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
        self.assertIn("DataAgent Lite", response.text)

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


if __name__ == "__main__":
    unittest.main()
