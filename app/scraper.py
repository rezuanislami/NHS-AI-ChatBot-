import os
import json
import requests
import numpy as np

OLLAMA_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"

INPUT_FOLDER = "cleaned_pages"
OUTPUT_FILE = "embedded_chunks.json"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


# ===============================
# TEXT CHUNKER
# ===============================

def split_text(text):

    chunks = []

    start = 0

    while start < len(text):

        end = start + CHUNK_SIZE

        chunk = text[start:end]

        chunks.append(chunk)

        start += (
            CHUNK_SIZE - CHUNK_OVERLAP
        )

    return chunks


# ===============================
# EMBEDDING FUNCTION
# ===============================

def embed_text(text):

    response = requests.post(

        OLLAMA_URL,

        json={
            "model": EMBED_MODEL,
            "prompt": text
        },

        timeout=60

    )

    response.raise_for_status()

    return response.json()["embedding"]


# ===============================
# MAIN PROCESS
# ===============================

all_chunks = []

files = os.listdir(INPUT_FOLDER)

for file in files:

    if not file.endswith(".json"):
        continue

    path = os.path.join(
        INPUT_FOLDER,
        file
    )

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        page = json.load(f)

    text = page["content"]

    title = page["title"]

    url = page["url"]

    # SPLIT INTO CHUNKS
    chunks = split_text(text)

    for chunk in chunks:

        try:

            embedding = embed_text(chunk)

            all_chunks.append({

                "title": title,
                "content": chunk,
                "url": url,
                "embedding": embedding

            })

        except Exception as e:

            print(
                "Embedding failed:",
                e
            )


# ===============================
# SAVE OUTPUT
# ===============================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        all_chunks,
        f,
        ensure_ascii=False,
        indent=2
    )

print(
    f"Saved {len(all_chunks)} chunks"
)