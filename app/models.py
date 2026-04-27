from uuid import uuid4, UUID
from typing import Dict, List

conversations: Dict[UUID, List[dict]] = {}


def create_conversation():
    cid = uuid4()
    conversations[cid] = []
    return cid


def add_message(cid: UUID, role: str, content: str):
    conversations[cid].append({
        "role": role,
        "content": content
    })


def get_messages(cid: UUID):
    return conversations.get(cid)