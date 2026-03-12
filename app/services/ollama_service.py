import json
import numpy as np
import httpx
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL    = "llama3"          # change to whichever model you have pulled
EMBEDDINGS_FILE = "embedded_chunks.json"
TOP_K           = 3                 # number of chunks to inject as context

SYSTEM_PROMPT = """You are a helpful careers advisor for NHSScotland.
Answer questions about NHS Scotland career paths using the context provided.
If the context does not contain enough information to answer, say so honestly.
Keep answers concise, friendly, and encouraging."""

# ---------------------------------------------------------------------------
# Load embeddings once at import time
# ---------------------------------------------------------------------------

_chunks: list[dict] = []
_matrix: np.ndarray | None = None   # shape (N, D)

def _load_embeddings() -> None:
    global _chunks, _matrix
    path = Path(EMBEDDINGS_FILE)
    if not path.exists():
        print(f"[RAG] WARNING: {EMBEDDINGS_FILE} not found – RAG disabled.")
        return
    with open(path, "r", encoding="utf-8") as f:
        _chunks = json.load(f)
    _matrix = np.array([c["embedding"] for c in _chunks], dtype="float32")
    # Pre-normalise for fast cosine similarity via dot product
    norms = np.linalg.norm(_matrix, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    _matrix /= norms
    print(f"[RAG] Loaded {len(_chunks)} chunks from {EMBEDDINGS_FILE}.")

_load_embeddings()


# ---------------------------------------------------------------------------
# RAG helpers
# ---------------------------------------------------------------------------

def _embed_query(query: str) -> np.ndarray:
    """
    Embed the user query using Ollama's /api/embeddings endpoint.
    Falls back to zero-vector if the call fails.
    """
    try:
        resp = httpx.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={"model": OLLAMA_MODEL, "prompt": query},
            timeout=30,
        )
        resp.raise_for_status()
        vec = np.array(resp.json()["embedding"], dtype="float32")
        norm = np.linalg.norm(vec)
        return vec / norm if norm else vec
    except Exception as exc:
        print(f"[RAG] Embedding failed: {exc}")
        return np.zeros(384, dtype="float32")   # all-MiniLM-L6-v2 dim


def _retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """Return the top-k most relevant chunks for the query."""
    if _matrix is None or len(_chunks) == 0:
        return []
    q_vec = _embed_query(query)
    scores = _matrix @ q_vec          # cosine similarities (pre-normalised)
    idx = np.argsort(scores)[::-1][:top_k]
    return [_chunks[i] for i in idx]


def _build_context(chunks: list[dict]) -> str:
    parts = []
    for c in chunks:
        parts.append(
            f"Source: {c['title']} ({c['url']})\n{c['content']}"
        )
    return "\n\n---\n\n".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def call_ollama(user_message: str | list[dict]) -> str:
    """
    Send a message (or conversation history) to Ollama with RAG context.

    Parameters
    ----------
    user_message : str | list[dict]
        Either a plain string (simple /chat endpoint) or a list of
        {"role": "user"/"assistant", "content": "..."} dicts (conversation API).

    Returns
    -------
    str
        The assistant's reply text.
    """

    # ------------------------------------------------------------------
    # 1. Determine the latest user query for retrieval
    # ------------------------------------------------------------------
    if isinstance(user_message, list):
        # Find the last user turn
        query = next(
            (m["content"] for m in reversed(user_message) if m["role"] == "user"),
            "",
        )
    else:
        query = user_message

    # ------------------------------------------------------------------
    # 2. Retrieve relevant chunks
    # ------------------------------------------------------------------
    relevant_chunks = _retrieve(query)
    context_block   = _build_context(relevant_chunks) if relevant_chunks else ""

    # ------------------------------------------------------------------
    # 3. Build the messages list for Ollama /api/chat
    # ------------------------------------------------------------------
    system_content = SYSTEM_PROMPT
    if context_block:
        system_content += (
            "\n\nUse the following NHS Scotland career information to answer "
            "the user's question:\n\n" + context_block
        )

    messages: list[dict] = [{"role": "system", "content": system_content}]

    if isinstance(user_message, list):
        messages += user_message
    else:
        messages.append({"role": "user", "content": user_message})

    # ------------------------------------------------------------------
    # 4. Call Ollama
    # ------------------------------------------------------------------
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model":    OLLAMA_MODEL,
                "messages": messages,
                "stream":   False,
            },
        )
        resp.raise_for_status()

    data = resp.json()
    return data["message"]["content"]
