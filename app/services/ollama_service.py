import json
import numpy as np
import httpx
from pathlib import Path

# ==================================================
# CONFIG
# ==================================================

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_CHAT_MODEL = "llama3:latest"
OLLAMA_EMBED_MODEL = "nomic-embed-text"

# Resolved relative to this file so the server works from any cwd.
EMBEDDINGS_FILE = Path(__file__).resolve().parents[2] / "embedded_chunks.json"

TOP_K = 3
SIMILARITY_THRESHOLD = 0.25

# Maximum number of past messages (user + assistant) we forward to the model.
# Keeps the context window small and the latency predictable.
MAX_HISTORY_MESSAGES = 10

# ==================================================
# SYSTEM PROMPT
# ==================================================

SYSTEM_PROMPT = """You are the NHS Scotland Careers Assistant.

SCOPE - VERY IMPORTANT
- You only answer questions about NHS Scotland careers (paths, entry
  requirements, applications, training, salary bandings, work experience,
  apprenticeships, graduate schemes).
- All factual claims MUST come from the NHS CONTEXT block below, which is
  retrieved from the official NHS Scotland Careers website
  (careers.nhs.scot). Do not bring in information from any other source.
- If the NHS CONTEXT does not contain the answer, say so plainly and
  recommend the user visit https://www.careers.nhs.scot for the most
  current information. Do not guess or fall back to general knowledge.

OFF-TOPIC HANDLING
- If a question is not about NHS Scotland careers (for example careers
  outside healthcare, medical advice, NHS England/Wales, or unrelated
  topics), politely explain that you can only help with NHS Scotland
  careers and suggest a related topic the user might be interested in.

CONVERSATION
- Use earlier turns of this conversation to answer follow-ups such as
  "tell me more" or "what about the salary".

STYLE
- Be concise and structured. Use 4-8 sentences for substantive questions
  and fewer for simple ones.
- Use short bullet lists only when listing distinct items.
- Never invent URLs. The only URL you may suggest is
  https://www.careers.nhs.scot.
- Stay UK / NHS Scotland focused at all times.
"""

# ==================================================
# GLOBAL STORAGE
# ==================================================

_chunks = []
_matrix = None

# ==================================================
# LOAD EMBEDDINGS
# ==================================================

def _load_embeddings():
    global _chunks, _matrix

    if not EMBEDDINGS_FILE.exists():
        print(f"[RAG] embeddings file not found at {EMBEDDINGS_FILE}")
        return

    try:
        _chunks = json.loads(EMBEDDINGS_FILE.read_text(encoding="utf-8"))

        if not _chunks:
            print("[RAG] No chunks found")
            return

        _matrix = np.array(
            [c["embedding"] for c in _chunks],
            dtype="float32",
        )

        # Normalise vectors so the dot product equals cosine similarity.
        norms = np.linalg.norm(_matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1
        _matrix /= norms

        print(f"[RAG] Loaded {len(_chunks)} chunks")

    except Exception as e:
        print("[RAG LOAD ERROR]", repr(e))


_load_embeddings()

# ==================================================
# EMBEDDING FUNCTION
# ==================================================

def embed_query(text: str):
    try:
        r = httpx.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={"model": OLLAMA_EMBED_MODEL, "prompt": text},
            timeout=30,
        )
        r.raise_for_status()

        v = np.array(r.json()["embedding"], dtype="float32")
        n = np.linalg.norm(v)
        return v / n if n else v

    except Exception as e:
        print("[EMBED ERROR]", repr(e))
        dim = _matrix.shape[1] if _matrix is not None else 768
        return np.zeros(dim, dtype="float32")

# ==================================================
# RETRIEVE CHUNKS
# ==================================================

def retrieve(query: str):
    if _matrix is None or len(_chunks) == 0:
        return []

    q = embed_query(query)
    scores = _matrix @ q
    sorted_idx = np.argsort(scores)[::-1]

    filtered_idx = [
        i for i in sorted_idx
        if scores[i] > SIMILARITY_THRESHOLD
    ][:TOP_K]

    return [_chunks[i] for i in filtered_idx]

# ==================================================
# BUILD CONTEXT
# ==================================================

def build_context(chunks):
    parts = []
    for c in chunks:
        title = c.get("title", "")
        content = c.get("content", "")
        parts.append(f"{title}\n{content}")
    return "\n\n".join(parts)

# ==================================================
# FORMAT SOURCES
# ==================================================

def format_sources(chunks):
    sources = []
    seen = set()

    for c in chunks:
        title = c.get("title", "NHS Scotland")
        url = c.get("url") or "https://www.careers.nhs.scot"

        if title not in seen:
            sources.append({"title": title, "url": url})
            seen.add(title)

    return sources

# ==================================================
# HISTORY HELPERS
# ==================================================

def _normalise_history(history):
    """Accept either a single user string or a list of {role, content} dicts.

    The chat endpoint always passes a list, but accepting a string keeps the
    function usable for ad-hoc tests via curl/Postman.
    """
    if isinstance(history, str):
        return [{"role": "user", "content": history}]

    if not isinstance(history, list):
        return [{"role": "user", "content": str(history)}]

    cleaned = []
    for m in history:
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        content = m.get("content", "")
        if role in ("user", "assistant", "system") and content:
            cleaned.append({"role": role, "content": content})
    return cleaned

# ==================================================
# MAIN FUNCTION
# ==================================================

async def call_ollama(history, user_id: str = "default"):
    messages_in = _normalise_history(history)

    if not messages_in:
        return {
            "reply": "Please ask me a question about NHS Scotland careers.",
            "sources": [],
        }

    # The latest user turn drives RAG retrieval.
    last_user = next(
        (m["content"] for m in reversed(messages_in) if m["role"] == "user"),
        "",
    )

    chunks = retrieve(last_user) if last_user else []
    context = build_context(chunks)

    system_prompt = SYSTEM_PROMPT
    if context:
        system_prompt += f"\n\nNHS CONTEXT:\n{context}"

    # Trim history so we don't blow the context window on long sessions.
    trimmed = messages_in[-MAX_HISTORY_MESSAGES:]
    messages = [{"role": "system", "content": system_prompt}, *trimmed]

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": OLLAMA_CHAT_MODEL,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.4,
                        "num_predict": 500,
                    },
                },
            )

        resp.raise_for_status()
        data = resp.json()
        reply = data.get("message", {}).get("content", "").strip()

        if not reply:
            reply = "I couldn't generate a response. Please try again."

        return {"reply": reply, "sources": format_sources(chunks)}

    except Exception as e:
        print("[OLLAMA ERROR]", repr(e))
        return {
            "reply": "There was a temporary issue contacting the AI system.",
            "sources": [],
        }
