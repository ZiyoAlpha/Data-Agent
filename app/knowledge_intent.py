"""Deterministic gates for user-authorized knowledge writes."""

from __future__ import annotations

import re
from typing import Iterable, Optional, Tuple

from .knowledge_writer import SECTION_DESCRIPTIONS


NEGATED_WRITE_RE = re.compile(
    r"(?:不要|不用|别|无需).{0,8}(?:沉淀|写入|保存|记录|入库)",
    re.IGNORECASE,
)
WRITE_PATTERNS = (
    re.compile(
        r"(?:帮我|请|麻烦)?\s*(?:把|将)?[\s\S]{0,80}?"
        r"(?:沉淀|写入|存入|记入|保存到|加入)[\s\S]{0,30}?"
        r"(?:知识库|知识)",
        re.IGNORECASE,
    ),
    re.compile(r"(?:帮我|请|麻烦).{0,8}(?:沉淀|入库)", re.IGNORECASE),
    re.compile(
        r"(?:save|write|add|persist)[\s\S]{0,50}?(?:knowledge\s*base|knowledge)",
        re.IGNORECASE,
    ),
)
OVERWRITE_RE = re.compile(
    r"(?:确认|允许|同意)?\s*(?:覆盖|替换)(?:知识库|知识|文档)?|"
    r"(?:confirm|allow)\s+(?:overwrite|replace)",
    re.IGNORECASE,
)

_SECTION_PATTERN = "|".join(
    sorted((re.escape(section) for section in SECTION_DESCRIPTIONS), key=len, reverse=True)
)
KNOWLEDGE_PATH_RE = re.compile(
    rf"({_SECTION_PATTERN})/([a-z0-9]+(?:-[a-z0-9]+)*)\.md",
    re.IGNORECASE,
)


def is_explicit_knowledge_write(text: str) -> bool:
    normalized = text.strip()
    if not normalized or NEGATED_WRITE_RE.search(normalized):
        return False
    if is_explicit_overwrite(normalized) and re.search(
        r"(?:知识库|知识|knowledge)", normalized, re.IGNORECASE
    ):
        return True
    return any(pattern.search(normalized) for pattern in WRITE_PATTERNS)


def is_explicit_overwrite(text: str) -> bool:
    return bool(OVERWRITE_RE.search(text.strip()))


def find_knowledge_path(
    text: str,
    history: Iterable[dict] = (),
) -> Optional[Tuple[str, str]]:
    match = KNOWLEDGE_PATH_RE.search(text)
    if match:
        return match.group(1).lower(), match.group(2).lower()
    for message in reversed(list(history)):
        if message.get("role") != "assistant":
            continue
        match = KNOWLEDGE_PATH_RE.search(str(message.get("content", "")))
        if match:
            return match.group(1).lower(), match.group(2).lower()
    return None
