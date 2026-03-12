import os
import json
from sentence_transformers import SentenceTransformer

INPUT_FOLDER = "chunked_pages"
OUTPUT_FILE = "embedded_chunks.json"

model = SentenceTransformer("all-MiniLM-L6-v2")

all_embeddings = []

for file_name in os.listdir(INPUT_FOLDER):
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

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(all_embeddings, f)

print("All embeddings saved successfully.")