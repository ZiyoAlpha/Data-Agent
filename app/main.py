"""FastAPI server and local web UI."""

from contextlib import asynccontextmanager
import logging
from pathlib import Path
from typing import List, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import PROJECT_ROOT, settings
from .knowledge_base import LocalKnowledgeBase
from .llm import OpenAILLM


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("dataagent-lite")
knowledge_base = LocalKnowledgeBase(settings.knowledge_base_dir)
llm = OpenAILLM(settings)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    topK: int = Field(default=3, ge=1, le=10)


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=12000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=12000)
    history: List[HistoryMessage] = Field(default_factory=list, max_length=20)


@asynccontextmanager
async def lifespan(_: FastAPI):
    stats = knowledge_base.stats()
    if stats["lastIndexedAt"] is None:
        result = knowledge_base.rebuild()
        logger.info("Initialized local knowledge index: %s document(s)", result["indexed"])
    yield


app = FastAPI(
    title="DataAgent Lite",
    description="A local-first, public-safe DataAgent starter.",
    version="0.1.0",
    lifespan=lifespan,
)

static_dir = PROJECT_ROOT / "app" / "static"
app.mount("/assets", StaticFiles(directory=static_dir), name="assets")


@app.get("/", include_in_schema=False)
def index_page() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/api/status")
def status() -> dict:
    return {
        "ok": True,
        "llmReady": settings.llm_ready,
        "model": settings.openai_model,
        "knowledgeBase": knowledge_base.stats(),
    }


@app.post("/api/index")
def rebuild_index() -> dict:
    return {"ok": True, **knowledge_base.rebuild()}


@app.post("/api/search")
def search(request: SearchRequest) -> dict:
    results = knowledge_base.search(request.query, request.topK)
    return {
        "ok": True,
        "results": [result.public_dict(include_content=False) for result in results],
    }


@app.post("/api/chat")
def chat(request: ChatRequest) -> dict:
    results = knowledge_base.search(request.question, settings.top_k)
    context = knowledge_base.format_context(results, settings.max_context_chars)
    try:
        result = llm.answer(
            request.question,
            context,
            [message.model_dump() for message in request.history],
        )
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        logger.warning("OpenAI request failed: %s", error.__class__.__name__)
        raise HTTPException(
            status_code=502,
            detail="OpenAI request failed. Check the local configuration and try again.",
        ) from error
    return {
        "ok": True,
        "answer": result.text,
        "model": result.model,
        "usage": result.usage,
        "sources": [item.public_dict(include_content=False) for item in results],
    }

