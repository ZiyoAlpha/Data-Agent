"""Environment-only application settings."""

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _int_env(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError:
        value = default
    return max(minimum, min(value, maximum))


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "").strip()
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5.6-luna").strip()
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "").strip()
    host: str = os.getenv("HOST", "127.0.0.1").strip()
    port: int = _int_env("PORT", 8000, 1, 65535)
    top_k: int = _int_env("TOP_K", 3, 1, 10)
    max_context_chars: int = _int_env("MAX_CONTEXT_CHARS", 9000, 1000, 30000)
    max_output_tokens: int = _int_env("MAX_OUTPUT_TOKENS", 1200, 128, 8000)
    prompt_cache_key: str = os.getenv(
        "PROMPT_CACHE_KEY", "dataagent-lite-v1"
    ).strip()
    knowledge_base_dir: Path = PROJECT_ROOT / "knowledge_base" / "common"

    @property
    def llm_ready(self) -> bool:
        return bool(self.openai_api_key and self.openai_model)


settings = Settings()
