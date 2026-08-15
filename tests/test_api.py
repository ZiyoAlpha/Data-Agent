import unittest

from fastapi.testclient import TestClient

from app.main import app


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


if __name__ == "__main__":
    unittest.main()
