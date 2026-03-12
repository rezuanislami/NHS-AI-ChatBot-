import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Ollama
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str    = os.getenv("OLLAMA_MODEL", "llama3")

    # RAG
    EMBEDDINGS_FILE: str = os.getenv("EMBEDDINGS_FILE", "embedded_chunks.json")
    RAG_TOP_K: int       = int(os.getenv("RAG_TOP_K", "3"))

settings = Settings()
