"""Validated, local-only writer for the structured common knowledge base."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Dict

from .knowledge_base import LocalKnowledgeBase


SECTION_DESCRIPTIONS: Dict[str, str] = {
    "metrics": "confirmed metric definitions and calculation semantics",
    "tables": "entity schemas, grain, fields, time semantics, and relationships",
    "patterns": "reusable query, transformation, and analysis patterns",
    "contracts": "human-readable explanations of machine-enforceable constraints",
    "queries": "single-task query requirements and reusable query templates",
    "cases": "end-to-end examples, decisions, validation, and retrospective notes",
    "rules": "shared mandatory rules and conventions",
    "skills": "task procedures, checkpoints, and expected outputs",
    "precedents/fields": "historical evidence about field meaning, type, or enumeration",
    "precedents/schema-changes": "historical entity or field structure changes",
    "precedents/decisions": "reusable decisions that are not yet mandatory rules",
}
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SECRET_PATTERNS = {
    "OpenAI-style API key": re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    "GitHub token": re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{16,}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}
MAX_DOCUMENT_CHARS = 100_000


class KnowledgeWriteError(ValueError):
    """A safe, user-facing knowledge write validation error."""


@dataclass(frozen=True)
class KnowledgeWriteResult:
    path: str
    action: str
    indexed: bool
    bytes: int

    def public_dict(self) -> dict:
        return asdict(self)


class LocalKnowledgeWriter:
    def __init__(self, root: Path, index: LocalKnowledgeBase):
        self.root = root.resolve()
        self.index = index

    def write_markdown(
        self,
        *,
        section: str,
        slug: str,
        title: str,
        summary: str,
        body: str,
        source_ref: str = "",
        confidence: str = "draft",
        overwrite: bool = False,
    ) -> KnowledgeWriteResult:
        section = section.strip()
        slug = slug.strip()
        title = title.strip()
        summary = summary.strip()
        body = body.strip()
        source_ref = source_ref.strip()

        if section not in SECTION_DESCRIPTIONS:
            raise KnowledgeWriteError("Unknown common knowledge section")
        if not SLUG_RE.fullmatch(slug):
            raise KnowledgeWriteError("slug must use lowercase letters, numbers, and single hyphens")
        if not title or len(title) > 160:
            raise KnowledgeWriteError("title must contain 1 to 160 characters")
        if not summary or len(summary) > 500:
            raise KnowledgeWriteError("summary must contain 1 to 500 characters")
        if not body or len(body) > MAX_DOCUMENT_CHARS:
            raise KnowledgeWriteError(
                f"body must contain 1 to {MAX_DOCUMENT_CHARS} characters"
            )
        if confidence not in {"draft", "verified", "deprecated"}:
            raise KnowledgeWriteError("confidence must be draft, verified, or deprecated")

        combined = "\n".join((title, summary, body, source_ref))
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(combined):
                raise KnowledgeWriteError(f"Potential secret detected: {label}")

        raw_target_dir = self.root / section
        if raw_target_dir.is_symlink():
            raise KnowledgeWriteError("Target section is missing or unsafe")
        target_dir = raw_target_dir.resolve()
        try:
            target_dir.relative_to(self.root)
        except ValueError as error:
            raise KnowledgeWriteError("Target section escapes the knowledge base") from error
        if not target_dir.is_dir():
            raise KnowledgeWriteError("Target section is missing or unsafe")

        target = target_dir / f"{slug}.md"
        if target.exists() and target.is_dir():
            raise KnowledgeWriteError("Target path is a directory")
        if target.exists() and not overwrite:
            raise KnowledgeWriteError("Document already exists; set overwrite=true to replace it")

        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        document = self._render_document(
            section=section,
            title=title,
            summary=summary,
            body=body,
            source_ref=source_ref,
            confidence=confidence,
            timestamp=now,
        )
        self._write_atomically(target, document, overwrite)
        relative_path = target.relative_to(self.root).as_posix()
        indexed = self.index.index_document(relative_path)
        return KnowledgeWriteResult(
            path=relative_path,
            action="replaced" if overwrite else "created",
            indexed=indexed,
            bytes=len(document.encode("utf-8")),
        )

    @staticmethod
    def _render_document(
        *,
        section: str,
        title: str,
        summary: str,
        body: str,
        source_ref: str,
        confidence: str,
        timestamp: str,
    ) -> str:
        metadata = {
            "title": title,
            "section": section,
            "status": confidence,
            "summary": summary,
            "source_ref": source_ref,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        frontmatter = "\n".join(
            f"{key}: {json.dumps(value, ensure_ascii=False)}"
            for key, value in metadata.items()
        )
        return f"---\n{frontmatter}\n---\n\n# {title}\n\n{body}\n"

    @staticmethod
    def _write_atomically(target: Path, content: str, overwrite: bool) -> None:
        if not overwrite:
            try:
                descriptor = os.open(
                    str(target),
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0o644,
                )
            except FileExistsError as error:
                raise KnowledgeWriteError(
                    "Document already exists; set overwrite=true to replace it"
                ) from error
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                    handle.write(content)
            except Exception:
                target.unlink(missing_ok=True)
                raise
            return

        descriptor, temp_name = tempfile.mkstemp(
            dir=str(target.parent),
            prefix=f".{target.name}.",
            suffix=".tmp",
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(content)
            os.replace(temp_name, target)
        except Exception:
            Path(temp_name).unlink(missing_ok=True)
            raise
