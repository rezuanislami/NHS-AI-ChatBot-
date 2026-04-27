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

from app.services.ollama_service import call_ollama

app = FastAPI(
    title="NHS Scotland Careers Chat API",
    version="3.0.0",
)

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- HEALTH ----------------
@app.get("/healthz")
def health():
    return {"status": "ok"}

# ---------------- CHAT ----------------
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        result = await call_ollama(request.message)

        return {
            "reply": result["reply"],
            "sources": result.get("sources", [])
        }

    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


# ---------------- CONVERSATIONS ----------------
@app.post("/v1/conversations", response_model=CreateConversationResponse)
def start_conversation():
    return {"conversation_id": create_conversation()}


@app.post("/v1/conversations/{conversation_id}/messages",
          response_model=MessageResponse)
async def send_message(conversation_id: UUID, request: MessageRequest):

    messages = get_messages(conversation_id)
    if messages is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    add_message(conversation_id, "user", request.message)

    history = get_messages(conversation_id)

    result = await call_ollama(history)

    add_message(conversation_id, "assistant", result["reply"])

    return {
        "reply": result["reply"],
        "sources": result.get("sources", [])
    }