import json
import httpx
from pathlib import Path
from collections import defaultdict

CHAT_LOG_FILE = "app/data/chat_logs.json"
OUTPUT_FAQ_FILE = "app/data/faq_ai.json"

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3"

MIN_CLUSTER_SIZE = 2


# -----------------------------
# LOAD CHAT LOGS
# -----------------------------

def load_logs():
    path = Path(CHAT_LOG_FILE)

    if not path.exists():
        return []

    return json.loads(path.read_text(encoding="utf-8"))


# -----------------------------
# BASIC CLUSTERING (LIGHTWEIGHT)
# -----------------------------

def cluster_questions(logs):
    clusters = defaultdict(list)

    for entry in logs:
        q = entry.get("user", "").lower().strip()

        if len(q) < 5:
            continue

        # simple grouping key (first 3 words)
        key = " ".join(q.split()[:3])

        clusters[key].append(q)

    return clusters


# -----------------------------
# AI ANSWER GENERATION
# -----------------------------

async def generate_answer(question_group):
    prompt = f"""
You are an NHS Scotland careers expert.

Create a clear FAQ answer based on these similar user questions:

Questions:
{question_group}

Rules:
- Keep answer under 5 sentences
- Be accurate and general (no hallucination)
- Focus on NHS Scotland careers
"""

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "stream": False
            }
        )

    resp.raise_for_status()

    data = resp.json()
    return data["message"]["content"]


# -----------------------------
# BUILD FAQ
# -----------------------------

async def build_faq(clusters):
    faq_list = []

    for key, questions in clusters.items():

        if len(questions) < MIN_CLUSTER_SIZE:
            continue

        try:
            answer = await generate_answer("\n".join(questions))

            faq_list.append({
                "id": f"ai_{abs(hash(key)) % 100000}",
                "question": key,
                "keywords": key.split(),
                "answer": answer
            })

        except Exception as e:
            print("[AI FAQ ERROR]", repr(e))

    return faq_list


# -----------------------------
# SAVE OUTPUT
# -----------------------------

def save_faq(data):
    path = Path(OUTPUT_FAQ_FILE)

    path.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8"
    )

    print(f"[AI FAQ] Saved {len(data)} entries → {OUTPUT_FAQ_FILE}")


# -----------------------------
# MAIN
# -----------------------------

async def run():
    logs = load_logs()

    if not logs:
        print("[AI FAQ] No logs found")
        return

    clusters = cluster_questions(logs)

    faq = await build_faq(clusters)

    save_faq(faq)


if __name__ == "__main__":
    import asyncio
    asyncio.run(run())