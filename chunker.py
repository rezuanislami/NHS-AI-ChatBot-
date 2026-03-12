import os
import json

INPUT_FOLDER = "cleaned_pages"
OUTPUT_FOLDER = "chunked_pages"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

CHUNK_SIZE = 400
OVERLAP = 50

def chunk_text(text, chunk_size, overlap):
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = words[start:end]
        chunks.append(" ".join(chunk))
        start += chunk_size - overlap

    return chunks

for file_name in os.listdir(INPUT_FOLDER):
    if file_name.endswith(".json"):
        with open(os.path.join(INPUT_FOLDER, file_name), "r", encoding="utf-8") as f:
            data = json.load(f)

        chunks = chunk_text(data["content"], CHUNK_SIZE, OVERLAP)

        chunked_data = []

        for i, chunk in enumerate(chunks):
            chunked_data.append({
                "chunk_id": f"{file_name.replace('.json','')}_chunk_{i}",
                "url": data["url"],
                "title": data["title"],
                "content": chunk
            })

        with open(os.path.join(OUTPUT_FOLDER, file_name), "w", encoding="utf-8") as f:
            json.dump(chunked_data, f, indent=4)

        print(f"Chunked: {file_name}")