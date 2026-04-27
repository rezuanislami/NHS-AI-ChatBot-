"""In-memory state for the chat API.

Nothing in this module is persisted to disk. All state lives in the
running Python process and disappears when uvicorn is stopped or
restarted.

  * `conversations` keeps the message history per conversation id, used
    only so the model can answer follow-up questions in the same chat
    session. A conversation is forgotten when the server restarts or
    when its TTL expires.

  * `recent_questions` is a fixed-size ring buffer of the last N user
    questions across all sessions. It exists purely to feed the FAQ
    themes generator (see `app.services.faq_themes`) and never leaves
    memory. The buffer is overwritten as new questions come in.
"""

from collections import deque
from time import time
from uuid import uuid4, UUID
from typing import Deque, Dict, List, Tuple

# ---------- conversation store ----------

# {conversation_id: (last_touched_epoch, [messages])}
_conversations: Dict[UUID, Tuple[float, List[dict]]] = {}

# Drop conversations that have been idle for more than this many seconds.
# 30 minutes is plenty for a single browsing session and keeps memory
# bounded if the server runs for a long time.
_CONVERSATION_TTL_SECONDS = 30 * 60


def _gc():
    """Drop expired conversations. Cheap, runs on every access."""
    cutoff = time() - _CONVERSATION_TTL_SECONDS
    expired = [cid for cid, (touched, _) in _conversations.items() if touched < cutoff]
    for cid in expired:
        _conversations.pop(cid, None)


def create_conversation() -> UUID:
    _gc()
    cid = uuid4()
    _conversations[cid] = (time(), [])
    return cid


def add_message(cid: UUID, role: str, content: str) -> None:
    _gc()
    if cid not in _conversations:
        return
    _, messages = _conversations[cid]
    messages.append({"role": role, "content": content})
    _conversations[cid] = (time(), messages)

    # Mirror user questions into the FAQ-themes ring buffer.
    if role == "user":
        record_user_question(content)


def get_messages(cid: UUID):
    _gc()
    entry = _conversations.get(cid)
    return entry[1] if entry else None


# ---------- recent-questions ring buffer (for FAQ themes) ----------

# A small bounded buffer. When full, the oldest entry is discarded.
_QUESTION_BUFFER_SIZE = 200
recent_questions: Deque[str] = deque(maxlen=_QUESTION_BUFFER_SIZE)


def record_user_question(text: str) -> None:
    text = (text or "").strip()
    if len(text) >= 5:
        recent_questions.append(text)


def snapshot_recent_questions() -> List[str]:
    return list(recent_questions)
