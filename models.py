from uuid import uuid4, UUID
from typing import Dict, List

# In production replace with a real database
conversations: Dict[UUID, List[dict]] = {}


def create_conversation() -> UUID:
    conversation_id = uuid4()
    conversations[conversation_id] = []
    return conversation_id


def add_message(conversation_id: UUID, role: str, content: str):
    conversations[conversation_id].append({
        "role": role,
        "content": content
    })


def get_messages(conversation_id: UUID):
    return conversations.get(conversation_id)