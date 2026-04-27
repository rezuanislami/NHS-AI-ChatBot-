from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from typing import List, Optional


# ---------------- CHAT ----------------

class ChatRequest(BaseModel):
    """A single chat turn from the frontend.

    `conversation_id` is optional. If omitted (or unknown to the server),
    a new in-memory conversation will be started and the new id returned
    in the response, so the client can keep using it for follow-up turns.
    """
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[UUID] = None


class Source(BaseModel):
    title: str
    url: Optional[str] = ""


class ChatResponse(BaseModel):
    reply: str
    sources: List[Source] = []
    conversation_id: UUID


class CreateConversationResponse(BaseModel):
    conversation_id: UUID


# ---------------- SUPPORT TICKETS ----------------

class TicketAttachmentInfo(BaseModel):
    """Metadata about an attached file. The actual bytes are NOT sent
    in the current flow - only the filename is forwarded into the JIRA
    issue description so support staff know to ask the user for it."""
    filename: str = Field(..., max_length=255)
    size: int = Field(default=0, ge=0)
    type: str = Field(default="application/octet-stream", max_length=120)


class TicketRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    issueType: str = Field(..., min_length=1, max_length=100)
    priority: str = Field(default="Medium", max_length=20)
    subject: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=10, max_length=10000)
    source: Optional[str] = Field(default=None, max_length=200)
    attachment: Optional[TicketAttachmentInfo] = None


class TicketResponse(BaseModel):
    success: bool
    ticketKey: Optional[str] = None
    url: Optional[str] = None
    message: Optional[str] = None
