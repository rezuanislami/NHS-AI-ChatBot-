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

EMBEDDINGS_FILE = "embedded_chunks.json"

TOP_K = 3
SIMILARITY_THRESHOLD = 0.25

# ==================================================
# SYSTEM PROMPT
# ==================================================

SYSTEM_PROMPT = """
You are an NHS Scotland Careers Assistant.

RULES:
- Provide clear, structured, helpful answers
- Use 6–10 sentences when needed
- Use bullet points when helpful
- Always stay UK/NHS Scotland focused
- Base answers ONLY on provided context
- If context is limited, use general NHS Scotland knowledge
- Do NOT hallucinate URLs
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

    path = Path(EMBEDDINGS_FILE)

    if not path.exists():
        print("[RAG] embeddings file not found")
        return

    try:

        _chunks = json.loads(
            path.read_text(encoding="utf-8")
        )

        if not _chunks:
            print("[RAG] No chunks found")
            return

        _matrix = np.array(
            [c["embedding"] for c in _chunks],
            dtype="float32"
        )

        # Normalize vectors
        norms = np.linalg.norm(
            _matrix,
            axis=1,
            keepdims=True
        )

        norms[norms == 0] = 1

        _matrix /= norms

        print(
            f"[RAG] Loaded {len(_chunks)} chunks"
        )

    except Exception as e:

        print(
            "[RAG LOAD ERROR]",
            repr(e)
        )


_load_embeddings()

# ==================================================
# EMBEDDING FUNCTION
# ==================================================

def embed_query(text: str):

    try:

        r = httpx.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={
                "model": OLLAMA_EMBED_MODEL,
                "prompt": text
            },
            timeout=30,
        )

        r.raise_for_status()

        v = np.array(
            r.json()["embedding"],
            dtype="float32"
        )

        n = np.linalg.norm(v)

        return v / n if n else v

    except Exception as e:

        print(
            "[EMBED ERROR]",
            repr(e)
        )

        dim = (
            _matrix.shape[1]
            if _matrix is not None
            else 768
        )

        return np.zeros(
            dim,
            dtype="float32"
        )

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

    results = []

    for i in filtered_idx:

        results.append(
            _chunks[i]
        )

    return results

# ==================================================
# BUILD CONTEXT
# ==================================================

def build_context(chunks):

    parts = []

    for c in chunks:

        title = c.get(
            "title",
            ""
        )

        content = c.get(
            "content",
            ""
        )

        text = (
            f"{title}\n{content}"
        )

        parts.append(text)

    return "\n\n".join(parts)

# ==================================================
# CLEAN MODEL OUTPUT
# ==================================================

def clean(text: str):

    bad_words = [

        "http://",
        "https://",
        "learn more",
        "explore"

    ]

    for b in bad_words:

        text = text.replace(
            b,
            ""
        )

    return text.strip()

# ==================================================
# FORMAT SOURCES
# ==================================================

def format_sources(chunks):

    sources = []

    seen = set()

    for c in chunks:

        title = c.get(
            "title",
            "NHS Scotland"
        )

        url = c.get("url")

        if not url:

            url = (
                "https://www.careers.nhs.scot"
            )

        if title not in seen:

            sources.append({

                "title": title,
                "url": url

            })

            seen.add(title)

    return sources

# ==================================================
# MAIN FUNCTION
# ==================================================

async def call_ollama(
    user_message,
    user_id="default"
):

    query = str(
        user_message
    ).strip()

    # -------------------------
    # RETRIEVE CONTEXT
    # -------------------------

    chunks = retrieve(query)

    context = build_context(
        chunks
    )

    prompt = SYSTEM_PROMPT

    if context:

        prompt += (

            "\n\nNHS CONTEXT:\n"
            + context

        )

    prompt += """

INSTRUCTIONS:
1. Start with explanation
2. Give step-by-step guidance
3. Keep structured and professional
"""

    messages = [

        {
            "role": "system",
            "content": prompt
        },

        {
            "role": "user",
            "content": query
        }

    ]

    # -------------------------
    # CALL OLLAMA
    # -------------------------

    try:

        async with httpx.AsyncClient(
            timeout=300.0
        ) as client:

            resp = await client.post(

                f"{OLLAMA_BASE_URL}/api/chat",

                json={

                    "model": OLLAMA_CHAT_MODEL,

                    "messages": messages,

                    "stream": False,

                    "options": {

                        "temperature": 0.4,

                        "num_predict": 500

                    }

                }

            )

        resp.raise_for_status()

        data = resp.json()

        reply = data.get(
            "message",
            {}
        ).get(
            "content",
            ""
        )

        reply = clean(reply)

        if not reply:

            reply = (
                "I couldn’t generate a response. "
                "Please try again."
            )

        return {

            "reply": reply,

            "sources": format_sources(
                chunks
            )

        }

    except Exception as e:

        print(
            "[OLLAMA ERROR]",
            repr(e)
        )

        return {

            "reply":
            "There was a temporary issue contacting the AI system.",

            "sources": []

        }