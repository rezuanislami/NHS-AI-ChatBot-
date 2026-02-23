from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


class CreateConversationResponse(BaseModel):
    conversation_id: UUID


class MessageRequest(BaseModel):
    message: str = Field(..., max_length=2000)


class MessageResponse(BaseModel):
    conversation_id: UUID
    assistant_reply: str