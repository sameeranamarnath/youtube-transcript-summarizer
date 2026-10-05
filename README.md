# youtube-transcript-summarizer

Ask questions about a YouTube video and get answers grounded only in that video's
transcript. Paste a URL, the app pulls the captions, indexes them with HNSWLib,
and answers from the nearest chunks instead of from the model's general knowledge.

## How it works

1. Parse the video id out of the pasted URL and fetch the transcript.
2. Split the transcript, embed it, and persist the vectors with HNSWLib
   (`hnswlib.index` + `docstore.json`).
3. On a question, retrieve the closest chunks and send them plus the question to
   the OpenAI chat model.
4. Stream the answer back in the UI.

## Stack

- Next.js + React, Tailwind CSS
- LangChain (JS) for the retrieval chain
- HNSWLib as the vector store
- OpenAI API for embeddings and chat

## Run it

```
npm install
npm run dev
```

App on `http://localhost:3000`. Create `.env` with:

```
OPENAI_API_KEY=your-key
```

## Known limits

- Short transcripts work well; long ones run into OpenAI request limits.
- No captions on the source video means nothing to retrieve.

## Demo

Screen recording: https://clipchamp.com/watch/w4mao2IgjnT

## Agent service (`ai/`)

The Next.js app keeps the original in-process HNSWLib index. `ai/` is the
service-based version: transcripts are ingested into Qdrant, and questions run
through a LangGraph pipeline that grades its own retrieval before answering.

```
START -> retrieve -> grade_context -+-> answer  -> END
                                    |
                                    +-> decline -> END
```

- **Grade before generate** - if the retrieved chunks do not contain the answer, the graph declines rather than falling back on general knowledge
- **Citations** - the answer comes back with the chunks it used
- **Models** - vLLM (`Qwen/Qwen3-32B` chat, `BAAI/bge-m3` embeddings) behind an OpenAI-compatible API
- **Store** - Qdrant, optionally filtered to one `video_id`

```
docker compose -f docker-compose.ai.yml up
```

`POST /ingest` takes a YouTube URL, `POST /query` returns the answer plus
citations, and `POST /query/stream` streams the graph. See [`ai/README.md`](ai/README.md).
