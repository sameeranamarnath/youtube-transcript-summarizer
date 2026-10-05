"""LangGraph RAG pipeline over a single video's transcript.

Grading before generating is deliberate: it is what stops the model answering a
video-specific question out of general knowledge.
"""

import json
from typing import Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from core import chat_model, search


class RagState(TypedDict, total=False):
    question: str
    video_id: str | None
    chunks: list[dict[str, Any]]
    grounded: bool
    answer: str
    citations: list[dict[str, Any]]


def _parse_bool(raw: str, key: str) -> bool:
    """Models decorate JSON with prose and fences. Recover the flag or assume not grounded."""
    text = raw.strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            return bool(json.loads(text[start : end + 1]).get(key, False))
        except json.JSONDecodeError:
            return False
    return False


def retrieve(state: RagState) -> dict[str, Any]:
    return {"chunks": search(state["question"], state.get("video_id"))}


def grade_context(state: RagState) -> dict[str, Any]:
    chunks = state.get("chunks", [])
    if not chunks:
        return {"grounded": False}
    context = "\n---\n".join(c.get("text", "")[:800] for c in chunks[:5])
    prompt = (
        "Grade the retrieval. Reply with JSON only, no prose.\n"
        'Schema: {"sufficient": true|false, "reason": "..."}\n'
        "sufficient is true only when the excerpts contain enough to answer.\n\n"
        f"Question: {state['question']}\nExcerpts:\n{context}"
    )
    raw = str(chat_model(max_tokens=200).invoke(prompt).content)
    return {"grounded": _parse_bool(raw, "sufficient")}


def answer(state: RagState) -> dict[str, Any]:
    chunks = state.get("chunks", [])
    numbered = "\n\n".join(f"[{i + 1}] {c.get('text', '')}" for i, c in enumerate(chunks))
    prompt = (
        "Answer using only the numbered excerpts below and cite them as [n]. "
        "If they do not cover the question, say so plainly.\n\n"
        f"Question: {state['question']}\n\nExcerpts:\n{numbered}"
    )
    text = str(chat_model().invoke(prompt).content).strip()
    citations = [
        {
            "index": i + 1,
            "score": round(float(c.get("score", 0.0)), 4),
            "video_id": c.get("video_id"),
            "text": c.get("text", "")[:280],
        }
        for i, c in enumerate(chunks)
    ]
    return {"answer": text, "citations": citations}


def decline(state: RagState) -> dict[str, Any]:
    return {"answer": "The transcript does not appear to cover that.", "citations": []}


def _route(state: RagState) -> Literal["answer", "decline"]:
    return "answer" if state.get("grounded") else "decline"


def build_graph():
    g = StateGraph(RagState)
    g.add_node("retrieve", retrieve)
    g.add_node("grade_context", grade_context)
    g.add_node("answer", answer)
    g.add_node("decline", decline)

    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "grade_context")
    g.add_conditional_edges("grade_context", _route, {"answer": "answer", "decline": "decline"})
    g.add_edge("answer", END)
    g.add_edge("decline", END)
    return g.compile()


APP = build_graph()


def query(question: str, video_id: str | None = None) -> RagState:
    return APP.invoke({"question": question, "video_id": video_id})
