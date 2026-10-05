"""HTTP surface for the transcript RAG service."""

import json
import re
from collections.abc import AsyncIterator
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from youtube_transcript_api import YouTubeTranscriptApi

from core import chunk_text, get_settings, search, upsert_chunks
from graph import APP, query
from guardrails import sanitise

api = FastAPI(title="youtube transcript rag", version="1.0.0")

VIDEO_ID_RE = re.compile(r"(?:v=|youtu\.be/|shorts/|embed/)([A-Za-z0-9_-]{11})")


class IngestRequest(BaseModel):
    url: str | None = None
    video_id: str | None = None


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    video_id: str | None = None


class IngestResponse(BaseModel):
    video_id: str
    chunks: int


def extract_video_id(url: str) -> str:
    match = VIDEO_ID_RE.search(url)
    if not match:
        raise ValueError("no 11-character video id found in the url")
    return match.group(1)


@api.get("/health")
def health() -> dict[str, Any]:
    s = get_settings()
    return {
        "status": "ok",
        "llm_model": s.llm_model,
        "embed_model": s.embed_model,
        "collection": s.qdrant_collection,
    }


@api.post("/ingest", response_model=IngestResponse)
def ingest(req: IngestRequest) -> IngestResponse:
    try:
        video_id = req.video_id or extract_video_id(req.url or "")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        fetched = YouTubeTranscriptApi().fetch(video_id)
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"transcript fetch failed: {type(exc).__name__}"
        ) from exc

    text = " ".join(snippet.text for snippet in fetched)
    chunks = chunk_text(text)
    if not chunks:
        return IngestResponse(video_id=video_id, chunks=0)

    payloads = [
        {"video_id": video_id, "chunk_index": i, "source": "youtube-transcript"}
        for i in range(len(chunks))
    ]
    return IngestResponse(video_id=video_id, chunks=upsert_chunks(chunks, payloads))


@api.post("/query")
def query_endpoint(req: QueryRequest) -> dict[str, Any]:
    result = query(sanitise(req.question), req.video_id)
    return {
        "answer": result.get("answer", ""),
        "grounded": result.get("grounded", False),
        "citations": result.get("citations", []),
    }


@api.post("/query/stream")
async def query_stream(req: QueryRequest) -> StreamingResponse:
    async def events() -> AsyncIterator[str]:
        state: dict[str, Any] = {"question": req.question, "video_id": req.video_id}
        for step in APP.stream(state):
            for node, update in step.items():
                payload = json.dumps({"node": node, "update": _safe(update)})
                yield f"event: node\ndata: {payload}\n\n"
                state.update(update)
        yield f"event: done\ndata: {json.dumps(_safe(state))}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


def _safe(d: dict[str, Any]) -> dict[str, Any]:
    out = dict(d)
    if "chunks" in out:
        out["chunks"] = [c.get("text", "")[:160] for c in out["chunks"]]
    return out


@api.get("/search")
def quick_search(q: str, video_id: str | None = None) -> dict[str, Any]:
    return {"hits": search(q, video_id)}
