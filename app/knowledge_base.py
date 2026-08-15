"""Local FTS5 knowledge-base index inspired by a document-first RAG flow."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path
import re
import sqlite3
import time
from typing import Iterable, List


CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
WORD_RE = re.compile(r"[\w\u3400-\u4dbf\u4e00-\u9fff-]+", re.UNICODE)
SUPPORTED_SUFFIXES = {".md", ".txt"}
IGNORED_DIRS = {".dataagent", ".git", "node_modules", "__pycache__"}
MAX_FILE_BYTES = 1_000_000


def cjk_bigram(text: str) -> List[str]:
    """Expand Chinese terms into bigrams, single characters and the original term."""
    tokens: List[str] = []
    for word in WORD_RE.findall(text.lower()):
        if CJK_RE.search(word) and len(word) > 1:
            chars = list(word)
            tokens.extend(chars[index] + chars[index + 1] for index in range(len(chars) - 1))
            tokens.extend(chars)
            tokens.append(word)
        else:
            tokens.append(word)
    return list(dict.fromkeys(token for token in tokens if token))


@dataclass(frozen=True)
class SearchResult:
    path: str
    name: str
    excerpt: str
    content: str
    score: float

    def public_dict(self, include_content: bool = False) -> dict:
        payload = asdict(self)
        if not include_content:
            payload.pop("content")
        return payload


class LocalKnowledgeBase:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.index_dir = self.root / ".dataagent"
        self.db_path = self.index_dir / "index.db"

    def _connect(self) -> sqlite3.Connection:
        self.index_dir.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(str(self.db_path))
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                path TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                size INTEGER NOT NULL,
                modified_at REAL NOT NULL,
                indexed_at REAL NOT NULL
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                doc_id UNINDEXED,
                doc_path,
                doc_name,
                content,
                tokenize='porter unicode61'
            );

            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        return connection

    def _iter_documents(self) -> Iterable[Path]:
        if not self.root.exists():
            return
        for path in sorted(self.root.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            relative = path.relative_to(self.root)
            if any(part in IGNORED_DIRS or part.startswith(".") for part in relative.parts[:-1]):
                continue
            if path.name.lower() == "readme.md":
                continue
            if path.suffix.lower() not in SUPPORTED_SUFFIXES:
                continue
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
            yield path

    def rebuild(self) -> dict:
        self.root.mkdir(parents=True, exist_ok=True)
        indexed = 0
        skipped = 0
        now = time.time()
        with self._connect() as connection:
            connection.execute("DELETE FROM documents_fts")
            connection.execute("DELETE FROM documents")
            for path in self._iter_documents():
                try:
                    content = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    skipped += 1
                    continue
                relative = path.relative_to(self.root).as_posix()
                stat = path.stat()
                doc_id = hashlib.sha256(relative.encode("utf-8")).hexdigest()[:24]
                searchable = " ".join(cjk_bigram(content))
                connection.execute(
                    "INSERT INTO documents(id, path, name, size, modified_at, indexed_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (doc_id, relative, path.stem, stat.st_size, stat.st_mtime, now),
                )
                connection.execute(
                    "INSERT INTO documents_fts(doc_id, doc_path, doc_name, content) VALUES (?, ?, ?, ?)",
                    (doc_id, relative, path.stem, searchable),
                )
                indexed += 1
            connection.execute(
                "INSERT OR REPLACE INTO metadata(key, value) VALUES ('last_indexed_at', ?)",
                (str(now),),
            )
        return {"indexed": indexed, "skipped": skipped, "lastIndexedAt": now}

    def index_document(self, relative_path: str) -> bool:
        """Incrementally add or replace one safe local document in the FTS5 index."""
        raw_candidate = self.root / relative_path
        if raw_candidate.is_symlink():
            return False
        candidate = raw_candidate.resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError:
            return False
        if (
            not candidate.is_file()
            or candidate.is_symlink()
            or candidate.suffix.lower() not in SUPPORTED_SUFFIXES
            or candidate.stat().st_size > MAX_FILE_BYTES
        ):
            return False
        try:
            content = candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return False

        relative = candidate.relative_to(self.root).as_posix()
        now = time.time()
        doc_id = hashlib.sha256(relative.encode("utf-8")).hexdigest()[:24]
        stat = candidate.stat()
        searchable = " ".join(cjk_bigram(content))
        with self._connect() as connection:
            connection.execute("DELETE FROM documents_fts WHERE doc_id = ?", (doc_id,))
            connection.execute(
                """
                INSERT OR REPLACE INTO documents(id, path, name, size, modified_at, indexed_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (doc_id, relative, candidate.stem, stat.st_size, stat.st_mtime, now),
            )
            connection.execute(
                "INSERT INTO documents_fts(doc_id, doc_path, doc_name, content) VALUES (?, ?, ?, ?)",
                (doc_id, relative, candidate.stem, searchable),
            )
            connection.execute(
                "INSERT OR REPLACE INTO metadata(key, value) VALUES ('last_indexed_at', ?)",
                (str(now),),
            )
        return True

    def stats(self) -> dict:
        if not self.db_path.exists():
            return {"documentCount": 0, "lastIndexedAt": None, "indexBytes": 0}
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM documents").fetchone()
            indexed = connection.execute(
                "SELECT value FROM metadata WHERE key = 'last_indexed_at'"
            ).fetchone()
        return {
            "documentCount": int(row["count"]),
            "lastIndexedAt": float(indexed["value"]) if indexed else None,
            "indexBytes": self.db_path.stat().st_size,
        }

    def search(self, query: str, top_k: int = 3, max_chars_per_doc: int = 3000) -> List[SearchResult]:
        terms = cjk_bigram(query.strip())
        if not terms or not self.db_path.exists():
            return []
        fts_query = " OR ".join(f'"{term.replace(chr(34), chr(34) * 2)}"' for term in terms)
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT doc_path, doc_name,
                       snippet(documents_fts, 3, '[', ']', ' … ', 48) AS excerpt,
                       rank * -1 AS score
                FROM documents_fts
                WHERE documents_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (fts_query, max(1, min(top_k, 10))),
            ).fetchall()

        results: List[SearchResult] = []
        max_score = float(rows[0]["score"]) if rows and rows[0]["score"] else 0.0
        for row in rows:
            relative = row["doc_path"]
            full_path = (self.root / relative).resolve()
            try:
                full_path.relative_to(self.root)
                content = full_path.read_text(encoding="utf-8")
            except (ValueError, OSError, UnicodeDecodeError):
                content = ""
            if max_chars_per_doc > 0 and len(content) > max_chars_per_doc:
                content = content[:max_chars_per_doc].rstrip() + "\n[内容已截断]"
            raw_score = float(row["score"] or 0.0)
            normalized = raw_score / max_score if max_score > 0 else 0.0
            results.append(
                SearchResult(
                    path=relative,
                    name=row["doc_name"],
                    excerpt=row["excerpt"] or "",
                    content=content,
                    score=round(normalized, 4),
                )
            )
        return results

    @staticmethod
    def format_context(results: List[SearchResult], max_chars: int) -> str:
        parts: List[str] = []
        used = 0
        for index, result in enumerate(results, start=1):
            block = f"Source {index}: [{result.path}]\n{result.content.strip()}"
            remaining = max_chars - used
            if remaining <= 0:
                break
            parts.append(block[:remaining])
            used += min(len(block), remaining)
        return "\n\n---\n\n".join(parts)
