import unittest

from app.knowledge_intent import (
    find_knowledge_path,
    is_explicit_knowledge_write,
    is_explicit_overwrite,
)


class KnowledgeIntentTest(unittest.TestCase):
    def test_only_explicit_requests_trigger_a_write(self):
        for text in (
            "帮我把刚才的结论沉淀到知识库",
            "请将这段规则写入知识库",
            "Please save this to the knowledge base",
        ):
            with self.subTest(text=text):
                self.assertTrue(is_explicit_knowledge_write(text))

    def test_negation_and_general_questions_do_not_trigger_a_write(self):
        for text in (
            "不要帮我沉淀到知识库",
            "不用把这段内容写入知识库",
            "知识库怎么写入？",
            "帮我总结一下刚才的结论",
        ):
            with self.subTest(text=text):
                self.assertFalse(is_explicit_knowledge_write(text))

    def test_explicit_overwrite_is_detected_and_path_is_resolved(self):
        text = "确认覆盖知识库文档 metrics/example-rate.md"
        self.assertTrue(is_explicit_knowledge_write(text))
        self.assertTrue(is_explicit_overwrite(text))
        self.assertEqual(find_knowledge_path(text), ("metrics", "example-rate"))

    def test_overwrite_path_can_come_from_previous_assistant_message(self):
        history = [
            {
                "role": "assistant",
                "content": "如需替换，请确认 rules/example-rule.md。",
            }
        ]
        self.assertEqual(
            find_knowledge_path("确认覆盖这个知识库文档", history),
            ("rules", "example-rule"),
        )


if __name__ == "__main__":
    unittest.main()
