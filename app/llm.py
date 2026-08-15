"""OpenAI-only LLM adapter with cache-friendly prompt ordering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal

from openai import OpenAI
from pydantic import BaseModel

from .config import Settings
from .prompts import KNOWLEDGE_DRAFT_PROMPT, SYSTEM_PROMPT, build_grounded_request


@dataclass(frozen=True)
class LLMResult:
    text: str
    model: str
    usage: Dict[str, int]


class KnowledgeDraft(BaseModel):
    ready: bool
    section: Literal[
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
    ]
    slug: str
    title: str
    summary: str
    body: str
    source_ref: str
    confidence: Literal["draft", "verified", "deprecated"]
    missing_information: str


@dataclass(frozen=True)
class KnowledgeDraftResult:
    draft: KnowledgeDraft
    model: str
    usage: Dict[str, int]


class OpenAILLM:
    def __init__(self, config: Settings):
        self.config = config

    def _client(self) -> OpenAI:
        kwargs = {"api_key": self.config.openai_api_key, "timeout": 60.0}
        if self.config.openai_base_url:
            kwargs["base_url"] = self.config.openai_base_url
        return OpenAI(**kwargs)

    @staticmethod
    def _usage(response) -> Dict[str, int]:
        input_details = getattr(getattr(response, "usage", None), "input_tokens_details", None)
        return {
            "inputTokens": int(
                getattr(getattr(response, "usage", None), "input_tokens", 0) or 0
            ),
            "outputTokens": int(
                getattr(getattr(response, "usage", None), "output_tokens", 0) or 0
            ),
            "cachedTokens": int(getattr(input_details, "cached_tokens", 0) or 0),
        }

    @staticmethod
    def _stable_history(history: List[dict]) -> List[dict]:
        stable_history = []
        for message in history[-12:]:
            role = message.get("role")
            content = str(message.get("content", "")).strip()
            if role in {"user", "assistant"} and content:
                stable_history.append({"role": role, "content": content[:8000]})
        return stable_history

    def answer(self, question: str, context: str, history: List[dict]) -> LLMResult:
        if not self.config.llm_ready:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        stable_history = self._stable_history(history)

        # Cache-friendly order: static instructions -> stable chronological history
        # -> request-specific retrieval context and current question.
        request_input = [
            *stable_history,
            {"role": "user", "content": build_grounded_request(question, context)},
        ]
        response = self._client().responses.create(
            model=self.config.openai_model,
            instructions=SYSTEM_PROMPT,
            input=request_input,
            max_output_tokens=self.config.max_output_tokens,
            prompt_cache_key=self.config.prompt_cache_key,
            store=False,
        )

        return LLMResult(
            text=response.output_text,
            model=response.model,
            usage=self._usage(response),
        )

    def create_knowledge_draft(
        self,
        question: str,
        history: List[dict],
    ) -> KnowledgeDraftResult:
        if not self.config.llm_ready:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        request_input = [
            *self._stable_history(history),
            {"role": "user", "content": question.strip()},
        ]
        response = self._client().responses.parse(
            model=self.config.openai_model,
            instructions=KNOWLEDGE_DRAFT_PROMPT,
            input=request_input,
            text_format=KnowledgeDraft,
            max_output_tokens=self.config.max_output_tokens,
            prompt_cache_key=f"{self.config.prompt_cache_key}-knowledge-draft-v1",
            store=False,
        )
        if response.output_parsed is None:
            raise RuntimeError("The model did not return a knowledge draft")
        return KnowledgeDraftResult(
            draft=response.output_parsed,
            model=response.model,
            usage=self._usage(response),
        )
