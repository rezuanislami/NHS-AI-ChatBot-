from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from uuid import UUID

from app.schemas import (
    ChatRequest,
    ChatResponse,
    CreateConversationResponse,
    MessageRequest,
    MessageResponse,
)
from app.models import (
    create_conversation,
    add_message,
    get_messages,
)

# ── swap this import when you rename / move the file ────────────────────────
from app.services.ollama_service import call_ollama
# ────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="NHS Scotland Careers Chat API",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/healthz")
def health_check():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Simple one-shot chat  (no history, RAG enabled)
# ---------------------------------------------------------------------------

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Single-turn chat. Useful for simple frontend widgets."""
    try:
        reply = await call_ollama(request.message)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI service unavailable: {exc}")
    return {"reply": reply}


# ---------------------------------------------------------------------------
# Conversation API  (multi-turn history + RAG)
# ---------------------------------------------------------------------------

@app.post("/v1/conversations", response_model=CreateConversationResponse)
def start_conversation():
    """Create a new conversation session."""
    conversation_id = create_conversation()
    return {"conversation_id": conversation_id}


@app.post(
    "/v1/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
)
async def send_message(conversation_id: UUID, request: MessageRequest):
    """
    Append a user message to an existing conversation, call Ollama
    (with full history + RAG context), and return the assistant reply.
    """
    messages = get_messages(conversation_id)
    if messages is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Persist the new user message first
    add_message(conversation_id, "user", request.message)

    # Fetch the now-updated history (includes the message just added)
    history = get_messages(conversation_id)

    try:
        assistant_reply = await call_ollama(history)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI service unavailable: {exc}")

    # Persist assistant reply
    add_message(conversation_id, "assistant", assistant_reply)

    return {
        "conversation_id": conversation_id,
        "assistant_reply": assistant_reply,
    }
