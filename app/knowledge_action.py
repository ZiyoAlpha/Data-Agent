"""Chat-authorized knowledge drafting and persistence orchestration."""

from __future__ import annotations

from typing import List

from .knowledge_intent import find_knowledge_path, is_explicit_overwrite
from .knowledge_writer import KnowledgeWriteError, LocalKnowledgeWriter
from .llm import OpenAILLM


class KnowledgeActionService:
    def __init__(self, llm: OpenAILLM, writer: LocalKnowledgeWriter):
        self.llm = llm
        self.writer = writer

    def handle(self, question: str, history: List[dict]) -> dict:
        generated = self.llm.create_knowledge_draft(question, history)
        draft = generated.draft
        base = {
            "ok": True,
            "model": generated.model,
            "usage": generated.usage,
            "sources": [],
        }

        if not draft.ready:
            missing = draft.missing_information.strip() or "缺少可复用的知识正文"
            return {
                **base,
                "answer": f"还没有写入知识库：{missing}。请补充后再说“帮我沉淀”。",
                "knowledgeWrite": {
                    "status": "needs_input",
                    "message": missing,
                },
            }

        section = draft.section
        slug = draft.slug
        overwrite = is_explicit_overwrite(question)
        if overwrite:
            confirmed_target = find_knowledge_path(question, history)
            if confirmed_target is None:
                return {
                    **base,
                    "answer": "尚未覆盖：请明确要覆盖的知识库相对路径，例如 `metrics/example-rate.md`。",
                    "knowledgeWrite": {
                        "status": "needs_path",
                        "message": "Explicit overwrite target is required",
                    },
                }
            section, slug = confirmed_target

        relative_path = f"{section}/{slug}.md"
        try:
            result = self.writer.write_markdown(
                section=section,
                slug=slug,
                title=draft.title,
                summary=draft.summary,
                body=draft.body,
                source_ref=draft.source_ref,
                confidence=draft.confidence,
                overwrite=overwrite,
            )
        except KnowledgeWriteError as error:
            if error.code == "already_exists":
                return {
                    **base,
                    "answer": (
                        f"尚未覆盖：知识文档 `{relative_path}` 已存在。"
                        f"如需替换，请回复“确认覆盖知识库文档 {relative_path}”。"
                    ),
                    "knowledgeWrite": {
                        "status": "confirmation_required",
                        "path": relative_path,
                    },
                }
            return {
                **base,
                "answer": f"知识没有写入：{error}。",
                "knowledgeWrite": {
                    "status": "rejected",
                    "message": str(error),
                },
            }

        index_note = "索引已同步" if result.indexed else "文件已写入，但索引同步失败"
        action_text = "已更新" if result.action == "replaced" else "已沉淀"
        return {
            **base,
            "answer": f"{action_text}知识库文档 `{result.path}`，{index_note}。",
            "knowledgeWrite": {
                "status": result.action,
                "path": result.path,
                "indexed": result.indexed,
                "bytes": result.bytes,
            },
        }
