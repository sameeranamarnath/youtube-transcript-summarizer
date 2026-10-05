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
