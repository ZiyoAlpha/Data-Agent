import unittest

from app.prompts import SYSTEM_PROMPT, build_grounded_request


class PromptTest(unittest.TestCase):
    def test_static_prompt_contains_no_request_interpolation(self):
        self.assertNotIn("{question}", SYSTEM_PROMPT)
        self.assertNotIn("{context}", SYSTEM_PROMPT)
        self.assertNotIn("OPENAI_API_KEY=", SYSTEM_PROMPT)

    def test_dynamic_content_is_appended_in_data_blocks(self):
        request = build_grounded_request("问题", "[guide.md] 内容")
        self.assertLess(request.index("<knowledge_context>"), request.index("<question>"))
        self.assertIn("[guide.md] 内容", request)


if __name__ == "__main__":
    unittest.main()
