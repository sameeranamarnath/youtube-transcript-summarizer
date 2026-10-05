# Transcript RAG service

Replaces the in-process HNSWLib index with a proper retrieval service: ingest a
video's transcript into Qdrant, then answer questions with a LangGraph pipeline
that grades its own context before answering.

## Graph

```
START -> retrieve -> grade_context -+-> answer  -> END
                                    |
                                    +-> decline -> END
```

| Node | What it does |
| --- | --- |
| `retrieve` | Qdrant vector search, filtered to one `video_id` |
| `grade_context` | asks the model whether the retrieved chunks actually contain the answer |
| `answer` | answers from the chunks only, and returns the chunks as citations |
| `decline` | says the transcript does not cover the question, instead of guessing |

Grading before generating is the point - it is what stops the model from
answering a video-specific question out of general knowledge.

## Stack

- LangGraph for orchestration
- vLLM serving `Qwen/Qwen3-32B` (chat) and `BAAI/bge-m3` (embeddings)
- Qdrant for transcript retrieval
- `youtube-transcript-api` for ingestion
- FastAPI + SSE

## Run

```
docker compose -f ../docker-compose.ai.yml up
```

Then ingest and query:

```
curl -X POST localhost:8080/ingest -H 'content-type: application/json' \
  -d '{"url": "https://www.youtube.com/watch?v=<id>"}'

curl -X POST localhost:8080/query -H 'content-type: application/json' \
  -d '{"question": "what does the video say about pricing?", "video_id": "<id>"}'
```

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | liveness and resolved model names |
| `POST` | `/ingest` | fetch a transcript by URL, chunk it, embed it into Qdrant |
| `POST` | `/query` | answer a question, with citations |
| `POST` | `/query/stream` | same, as SSE per graph node |
| `GET` | `/search?q=` | retrieval-only debug view |

## Note

Captions are required - a video without them has nothing to index. vLLM wants a
GPU; point `LLM_BASE_URL` at a hosted endpoint for CPU-only deployments.
