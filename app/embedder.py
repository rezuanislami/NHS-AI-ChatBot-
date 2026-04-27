import os
import json
<<<<<<< HEAD
import httpx
=======
from sentence_transformers import SentenceTransformer
>>>>>>> 3a73f07fd3e0eef72da0d5eac0838f05f6089486

INPUT_FOLDER = "chunked_pages"
OUTPUT_FILE = "embedded_chunks.json"

<<<<<<< HEAD
OLLAMA_BASE_URL = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"


def embed_text(text: str):
    """Call Ollama embedding model"""
    resp = httpx.post(
        f"{OLLAMA_BASE_URL}/api/embeddings",
        json={
            "model": EMBED_MODEL,
            "prompt": text
        },
        timeout=60
    )
    resp.raise_for_status()
    return resp.json()["embedding"]


def normalize_chunks(data):
    """
    Handles ALL JSON shapes:
    - list of chunks (normal case)
    - single dict chunk
    - raw string fallback
    """
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        return [data]

    if isinstance(data, str):
        return [{"content": data}]

    return []


def safe_get_text(chunk):
    """Extract text safely from any chunk format"""
    if isinstance(chunk, dict):
        return chunk.get("content", "") or ""
    if isinstance(chunk, str):
        return chunk
    return ""

=======
model = SentenceTransformer("all-MiniLM-L6-v2")
>>>>>>> 3a73f07fd3e0eef72da0d5eac0838f05f6089486

all_embeddings = []

for file_name in os.listdir(INPUT_FOLDER):
<<<<<<< HEAD
    if not file_name.endswith(".json"):
        continue

    file_path = os.path.join(INPUT_FOLDER, file_name)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

    except Exception as e:
        print(f"[SKIP] {file_name} failed to load: {e}")
        continue

    chunks = normalize_chunks(raw_data)

    if not chunks:
        print(f"[SKIP] {file_name} empty after normalization")
        continue

    embedded_count = 0

    for chunk in chunks:
        text = safe_get_text(chunk)

        if not text or len(text.strip()) < 5:
            continue

        try:
            embedding = embed_text(text)
        except Exception as e:
            print(f"[EMBED ERROR] {file_name}: {e}")
            continue

        all_embeddings.append({
            "chunk_id": chunk.get("chunk_id") if isinstance(chunk, dict) else None,
            "url": chunk.get("url") if isinstance(chunk, dict) else None,
            "title": chunk.get("title") if isinstance(chunk, dict) else file_name.replace(".json", ""),
            "content": text,
            "embedding": embedding
        })

        embedded_count += 1

    print(f"Embedded: {file_name} ({embedded_count} chunks)")

=======
    if file_name.endswith(".json"):
        with open(os.path.join(INPUT_FOLDER, file_name), "r", encoding="utf-8") as f:
            chunks = json.load(f)

        for chunk in chunks:
            embedding = model.encode(chunk["content"]).tolist()

            all_embeddings.append({
                "chunk_id": chunk["chunk_id"],
                "url": chunk["url"],
                "title": chunk["title"],
                "content": chunk["content"],
                "embedding": embedding
            })

        print(f"Embedded: {file_name}")
>>>>>>> 3a73f07fd3e0eef72da0d5eac0838f05f6089486

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(all_embeddings, f)

<<<<<<< HEAD
print(f"\nAll embeddings saved successfully. Total: {len(all_embeddings)}")
=======
print("All embeddings saved successfully.")
>>>>>>> 3a73f07fd3e0eef72da0d5eac0838f05f6089486
