from fastapi import FastAPI, HTTPException
from uuid import UUID
from app.schemas import (
    CreateConversationResponse,
    MessageRequest,
    MessageResponse
)
from app.models import (
    create_conversation,
    add_message,
    get_messages
)
from app.services.blackbox_service import call_blackbox

app = FastAPI(title="NHS Chatbot API", version="1.0.0")


@app.get("/healthz")
def health_check():
    return {"status": "ok"}


@app.post("/v1/conversations", response_model=CreateConversationResponse)
def start_conversation():
    conversation_id = create_conversation()
    return {"conversation_id": conversation_id}


@app.post("/v1/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(conversation_id: UUID, request: MessageRequest):

    messages = get_messages(conversation_id)

    if messages is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Add user message
    add_message(conversation_id, "user", request.message)

    try:
        assistant_reply = await call_blackbox(messages)
    except Exception:
        raise HTTPException(status_code=502, detail="AI service unavailable")

    # Store assistant reply
    add_message(conversation_id, "assistant", assistant_reply)

    return {
        "conversation_id": conversation_id,
        "assistant_reply": assistant_reply
    }