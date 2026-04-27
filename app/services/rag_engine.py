import json
import numpy as np
from pathlib import Path

EMBED_FILE = Path("embedded_chunks.json")

_chunks = []
_matrix = None


def load_rag():
    global _chunks, _matrix

    if not EMBED_FILE.exists():
        return

    _chunks = json.loads(EMBED_FILE.read_text(encoding="utf-8"))

    if not _chunks:
        return

    _matrix = np.array([c["embedding"] for c in _chunks], dtype="float32")

    norms = np.linalg.norm(_matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1
    _matrix /= norms


def search(query_vec, top_k=2):
    if _matrix is None:
        return []

    scores = _matrix @ query_vec
    idx = np.argsort(scores)[::-1][:top_k]

    return [_chunks[i] for i in idx]


def build_context(chunks):
    return "\n\n".join(
        f"{c.get('title','')}\n{c.get('content','')[:300]}"
        for c in chunks
    )


load_rag()