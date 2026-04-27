"""Generate `faq_themes.json` from the in-memory recent-questions buffer.

This is the ONLY file the application writes to disk. It contains
clustered themes of what users have been asking about, intended for
the NHS Scotland Careers content team to spot common requests and
improve their published guidance.

The file is rewritten in full on every refresh; nothing is appended.
There is no chat-log file, no per-user data, and no message contents
are stored on disk - only the question text is clustered, and only
short anonymised summaries are written out.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from app.models import snapshot_recent_questions

# Path is resolved relative to this file so the file always lands at
# <project root>/app/data/faq_themes.json regardless of cwd.
FAQ_THEMES_FILE = Path(__file__).resolve().parents[1] / "data" / "faq_themes.json"

# Stop-words filtered out before keyword counting. Kept short on purpose.
_STOPWORDS = {
    "a", "an", "and", "the", "is", "are", "was", "were", "be", "been",
    "being", "to", "of", "in", "on", "for", "with", "by", "as", "at",
    "from", "into", "about", "i", "im", "me", "my", "you", "your", "we",
    "our", "it", "its", "this", "that", "these", "those", "do", "does",
    "did", "can", "could", "would", "should", "will", "shall", "may",
    "might", "have", "has", "had", "what", "which", "who", "whom",
    "whose", "when", "where", "why", "how", "or", "but", "if", "so",
    "than", "then", "there", "here", "any", "some", "no", "not", "yes",
    "also", "more", "less", "most", "least", "very", "just", "please",
    "tell", "give", "show", "want", "need", "looking", "look",
}

_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z\-]+")


def _tokenise(text: str) -> List[str]:
    return [w.lower() for w in _WORD_RE.findall(text)]


def _content_words(text: str) -> List[str]:
    return [w for w in _tokenise(text) if w not in _STOPWORDS and len(w) > 2]


def _cluster_key(question: str) -> str:
    """Group questions by their two strongest content keywords.

    Crude but effective for a small running buffer. We rely on the fact
    that career questions cluster naturally around domain words like
    "nurse", "salary", "apprenticeship", "ambulance", "training" etc.
    """
    words = _content_words(question)
    if not words:
        return question.strip().lower()[:40] or "general"
    top = sorted(set(words), key=words.count, reverse=True)[:2]
    return " + ".join(sorted(top))


def build_themes(min_count: int = 2) -> List[Dict]:
    questions = snapshot_recent_questions()
    if not questions:
        return []

    grouped: Dict[str, List[str]] = {}
    for q in questions:
        grouped.setdefault(_cluster_key(q), []).append(q)

    themes: List[Dict] = []
    for key, items in grouped.items():
        if len(items) < min_count:
            continue
        keyword_counts = Counter()
        for item in items:
            keyword_counts.update(_content_words(item))
        themes.append(
            {
                "theme": key,
                "frequency": len(items),
                "top_keywords": [w for w, _ in keyword_counts.most_common(5)],
                "example_questions": items[:5],
            }
        )

    themes.sort(key=lambda t: t["frequency"], reverse=True)
    return themes


def write_themes(themes: List[Dict]) -> Path:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "buffer_size": len(snapshot_recent_questions()),
        "themes": themes,
    }
    FAQ_THEMES_FILE.parent.mkdir(parents=True, exist_ok=True)
    FAQ_THEMES_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return FAQ_THEMES_FILE


def refresh(min_count: int = 2) -> Dict:
    themes = build_themes(min_count=min_count)
    path = write_themes(themes)
    return {
        "path": str(path),
        "theme_count": len(themes),
        "buffer_size": len(snapshot_recent_questions()),
    }


if __name__ == "__main__":
    summary = refresh()
    print(f"[FAQ THEMES] wrote {summary['theme_count']} themes -> {summary['path']}")
