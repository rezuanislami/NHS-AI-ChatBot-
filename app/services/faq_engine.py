import json
from pathlib import Path

FAQ_FILE = Path("app/data/faq.json")


def load_faq():
    if not FAQ_FILE.exists():
        return []
    return json.loads(FAQ_FILE.read_text(encoding="utf-8"))


FAQ_DATA = load_faq()


def get_faq_answer(query: str):
    q = query.lower()

    for item in FAQ_DATA:
        if item["question"] in q or q in item["question"]:
            return item["answer"]

    return None