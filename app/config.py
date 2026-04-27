import os
from dotenv import load_dotenv

load_dotenv()


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    # ---- Ollama ----
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")

    # ---- RAG ----
    EMBEDDINGS_FILE: str = os.getenv("EMBEDDINGS_FILE", "embedded_chunks.json")
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "3"))

    # ---- JIRA Cloud ----
    # Leave blank to disable the /api/jira-ticket endpoint. If any of the
    # four required fields are missing the backend will return a clear
    # 503 error instead of crashing.
    JIRA_BASE_URL: str = os.getenv("JIRA_BASE_URL", "").rstrip("/")
    JIRA_EMAIL: str = os.getenv("JIRA_EMAIL", "")
    JIRA_API_TOKEN: str = os.getenv("JIRA_API_TOKEN", "")
    JIRA_PROJECT_KEY: str = os.getenv("JIRA_PROJECT_KEY", "")
    JIRA_DEFAULT_ISSUE_TYPE: str = os.getenv("JIRA_DEFAULT_ISSUE_TYPE", "Task")

    @property
    def JIRA_CONFIGURED(self) -> bool:
        return all([
            self.JIRA_BASE_URL,
            self.JIRA_EMAIL,
            self.JIRA_API_TOKEN,
            self.JIRA_PROJECT_KEY,
        ])


settings = Settings()
