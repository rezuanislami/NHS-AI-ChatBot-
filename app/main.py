from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import (
    ChatRequest,
    ChatResponse,
    CreateConversationResponse,
    TicketRequest,
    TicketResponse,
)

from app.models import (
    create_conversation,
    add_message,
    get_messages,
    snapshot_recent_questions,
)

from app.services.ollama_service import call_ollama
from app.services.security import is_malicious
from app.services import faq_themes
from app.services.jira_service import create_jira_ticket

app = FastAPI(
    title="NHS Scotland Careers Chat API",
    version="3.2.0",
)

# ---------------- CORS ----------------
# allow_credentials must be False when using a wildcard origin,
# otherwise browsers will reject the response per the CORS spec.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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
    # Lightweight input validation (length + obvious prompt-injection patterns).
    if is_malicious(request.message):
        raise HTTPException(status_code=400, detail="Invalid input.")

    # Resume an existing conversation, or start a new one if the client did
    # not send an id (or sent one we no longer have in memory).
    cid = request.conversation_id
    if cid is None or get_messages(cid) is None:
        cid = create_conversation()

    # Append the new user turn before calling the model so it is part of
    # the history we send to Ollama. This also records the question into
    # the in-memory FAQ-themes buffer (see app.models.add_message).
    add_message(cid, "user", request.message)

    history = get_messages(cid)

    try:
        result = await call_ollama(history)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Persist the assistant turn (in memory only).
    add_message(cid, "assistant", result["reply"])

    return {
        "reply": result["reply"],
        "sources": result.get("sources", []),
        "conversation_id": cid,
    }


# ---------------- CONVERSATIONS ----------------
@app.post("/v1/conversations", response_model=CreateConversationResponse)
def start_conversation():
    return {"conversation_id": create_conversation()}


# ---------------- FAQ THEMES ----------------
# These endpoints expose the only persistent artefact the application
# produces: app/data/faq_themes.json. Nothing else is written to disk.

@app.get("/admin/faq-themes")
def get_faq_themes():
    """Return the current in-memory themes without touching disk."""
    return {
        "buffer_size": len(snapshot_recent_questions()),
        "themes": faq_themes.build_themes(),
    }


@app.post("/admin/faq-themes/refresh")
def refresh_faq_themes(min_count: int = 2):
    """Cluster the current question buffer and rewrite faq_themes.json."""
    return faq_themes.refresh(min_count=min_count)


# ---------------- SUPPORT TICKETS (JIRA) ----------------
@app.post("/api/jira-ticket", response_model=TicketResponse)
async def submit_jira_ticket(ticket: TicketRequest):
    """Forward the support-ticket form to JIRA Cloud.

    Returns the new issue key on success, or a structured error message
    on failure (missing config, JIRA rejection, network issue). Nothing
    about the ticket is stored locally.
    """
    # Lightweight content check - same filter the chat uses.
    if is_malicious(ticket.subject) or is_malicious(ticket.description):
        raise HTTPException(status_code=400, detail="Invalid input.")

    result = await create_jira_ticket(ticket)

    if not result.success:
        # 503 if JIRA isn't set up; 502 if JIRA refused the request.
        status = 503 if "not configured" in (result.message or "") else 502
        raise HTTPException(status_code=status, detail=result.message)

    return result
