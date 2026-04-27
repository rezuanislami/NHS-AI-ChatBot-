import json
from pathlib import Path
from collections import Counter

LOG_FILE = Path("app/data/chat_logs.json")
OUTPUT_FILE = Path("app/data/faq_suggestions.json")


def load_logs():
    if not LOG_FILE.exists():
        return []

    try:
        return json.loads(LOG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def extract_questions(logs):
    """
    Expecting logs like:
    [{"role": "user", "message": "..."}]
    """

    questions = []

    for entry in logs:
        if entry.get("role") == "user":
            msg = entry.get("message", "").strip().lower()

            if len(msg) > 3:
                questions.append(msg)

    return questions


def generate_faq_suggestions(min_count: int = 2):
    logs = load_logs()
    questions = extract_questions(logs)

    if not questions:
        print("No logs found.")
        return []

    counts = Counter(questions)

    suggestions = []

    for question, count in counts.items():
        if count >= min_count:

            suggestions.append({
                "question": question,
                "suggested_answer": "",
                "frequency": count,
                "status": "pending_review"
            })

    # sort by most asked
    suggestions.sort(key=lambda x: x["frequency"], reverse=True)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT_FILE.write_text(
        json.dumps(suggestions, indent=2),
        encoding="utf-8"
    )

    print(f"[FAQ ANALYZER] Generated {len(suggestions)} suggestions")

    return suggestions


if __name__ == "__main__":
    generate_faq_suggestions()