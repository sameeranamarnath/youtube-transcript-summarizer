"""Config, model clients and Qdrant access for the transcript RAG service."""

from functools import lru_cache
from typing import Any

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic_settings import BaseSettings, SettingsConfigDict
from qdrant_client import QdrantClient, models


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_base_url: str = "http://vllm:8000/v1"
    llm_api_key: str = "local-vllm"
    llm_model: str = "Qwen/Qwen3-32B"

    embed_base_url: str = "http://vllm-embed:8000/v1"
    embed_model: str = "BAAI/bge-m3"
    embed_dim: int = 1024

    qdrant_url: str = "http://qdrant:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "youtube_transcripts"

    # Chunking. Transcripts are dense with filler, so overlap matters more than size.
    chunk_chars: int = 1200
    chunk_overlap: int = 200
    retrieval_top_k: int = 6


@lru_cache
def get_settings() -> Settings:
    return Settings()


def chat_model(temperature: float = 0.0, max_tokens: int = 1500) -> ChatOpenAI:
    s = get_settings()
    return ChatOpenAI(
        model=s.llm_model,
        base_url=s.llm_base_url,
        api_key=s.llm_api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        max_retries=2,
        timeout=120,
    )


def embed_model() -> OpenAIEmbeddings:
    s = get_settings()
    return OpenAIEmbeddings(
        model=s.embed_model,
        base_url=s.embed_base_url,
        api_key=s.llm_api_key,
        check_embedding_ctx_length=False,
    )


def qdrant() -> QdrantClient:
    s = get_settings()
    return QdrantClient(url=s.qdrant_url, api_key=s.qdrant_api_key)


def ensure_collection() -> str:
    s = get_settings()
    c = qdrant()
    if not c.collection_exists(s.qdrant_collection):
        c.create_collection(
            collection_name=s.qdrant_collection,
            vectors_config=models.VectorParams(
                size=s.embed_dim, distance=models.Distance.COSINE
            ),
        )
    return s.qdrant_collection


def chunk_text(text: str, size: int | None = None, overlap: int | None = None) -> list[str]:
    s = get_settings()
    size = size or s.chunk_chars
    overlap = overlap or s.chunk_overlap
    clean = " ".join(text.split())
    if not clean:
        return []
    step = max(1, size - overlap)
    return [clean[i : i + size] for i in range(0, len(clean), step)]


def upsert_chunks(chunks: list[str], payloads: list[dict[str, Any]]) -> int:
    collection = ensure_collection()
    vectors = embed_model().embed_documents(chunks)
    c = qdrant()
    start = c.count(collection_name=collection).count
    points = [
        models.PointStruct(id=start + i, vector=v, payload={"text": t, **p})
        for i, (t, v, p) in enumerate(zip(chunks, vectors, payloads))
    ]
    c.upsert(collection_name=collection, points=points)
    return len(points)


def search(
    query: str, video_id: str | None = None, top_k: int | None = None
) -> list[dict[str, Any]]:
    s = get_settings()
    collection = ensure_collection()
    query_filter = None
    if video_id:
        query_filter = models.Filter(
            must=[models.FieldCondition(key="video_id", match=models.MatchValue(value=video_id))]
        )
    hits = qdrant().search(
        collection_name=collection,
        query_vector=embed_model().embed_query(query),
        query_filter=query_filter,
        limit=top_k or s.retrieval_top_k,
        with_payload=True,
    )
    return [{"score": h.score, **(h.payload or {})} for h in hits]
