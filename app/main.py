from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import ChatRequest, ChatResponse
from app.services.blackbox_service import call_blackbox

app = FastAPI(
    title="NHS Scotland Careers Chat API",
    version="1.0.0"
)

# Allow frontend connection (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to NHS domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def health_check():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):

    try:
        reply = await call_blackbox(request.message)
    except Exception:
        raise HTTPException(status_code=502, detail="AI service unavailable")

    return {"reply": reply}