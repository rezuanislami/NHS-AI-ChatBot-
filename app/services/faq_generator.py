import json
from pathlib import Path
from collections import Counter

CHAT_LOG_FILE = "app/data/chat_logs.json"
OUTPUT_FAQ_FILE = "app/data/faq_generated.json"

MIN_OCCURRENCES = 2  # question must appear at least twice


# -----------------------------
# LOAD CHAT LOGS
# -----------------------------

def load_logs():
    path = Path(CHAT_LOG_FILE)

    if not path.exists():
        print("[FAQ] No chat logs found")
        return []

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print("[FAQ ERROR]", repr(e))
        return []


# -----------------------------
# EXTRACT QUESTIONS
# -----------------------------

def extract_questions(logs):
    questions = []

    for entry in logs:
        user_msg = entry.get("user", "").strip().lower()

        # basic filtering (ignore very short inputs)
        if len(user_msg) < 5:
            continue

        # ignore greetings
        if user_msg in ["hi", "hello", "hey"]:
            continue

        questions.append(user_msg)

    return questions


# -----------------------------
# BUILD FAQ
# -----------------------------

def build_faq(questions):
    counter = Counter(questions)

    faq_list = []

    for question, count in counter.items():
        if count >= MIN_OCCURRENCES:
            faq_list.append({
                "id": f"auto_{abs(hash(question)) % 100000}",
                "question": question,
                "keywords": question.split(),
                "answer": "Auto-generated placeholder answer. Please refine this manually."
            })

    return faq_list


# -----------------------------
# SAVE FAQ
# -----------------------------

def save_faq(faq_list):
    path = Path(OUTPUT_FAQ_FILE)

    path.write_text(
        json.dumps(faq_list, indent=2),
        encoding="utf-8"
    )

    print(f"[FAQ] Generated {len(faq_list)} FAQ entries → {OUTPUT_FAQ_FILE}")


# -----------------------------
# MAIN
# -----------------------------

def run():
    logs = load_logs()

    if not logs:
        print("[FAQ] No data to process")
        return

    questions = extract_questions(logs)

    faq = build_faq(questions)

    save_faq(faq)


if __name__ == "__main__":
    run()