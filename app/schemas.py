from pydantic import BaseModel, Field
from uuid import UUID
from typing import List, Optional


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class Source(BaseModel):
    title: str
    url: Optional[str] = ""


class ChatResponse(BaseModel):
    reply: str
    sources: List[Source] = []


class CreateConversationResponse(BaseModel):
    conversation_id: UUID


class MessageRequest(BaseModel):
    message: str


class MessageResponse(BaseModel):
    conversation_id: UUID
    assistant_reply: str