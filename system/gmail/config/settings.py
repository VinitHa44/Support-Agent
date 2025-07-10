from pathlib import Path
from typing import List

from pydantic import BaseModel

CONFIG_DIR = Path(__file__).parent
PROJECT_ROOT = CONFIG_DIR.parent.parent.parent


class Settings(BaseModel):
    GMAIL_SCOPES: List[str] = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.compose",
    ]
    CREDENTIALS_FILE: str = str(
        PROJECT_ROOT / "session-data" / "tokens" / "credentials.json"
    )
    TOKEN_FILE: str = str(
        PROJECT_ROOT / "session-data" / "tokens" / "gmail_tokens.json"
    )
    HISTORY_FILE: str = str(PROJECT_ROOT / "session-data" / "history.json")
    POLL_INTERVAL_SECONDS: int = 25
    EXTERNAL_SERVICE_URL: str = "http://localhost:8000/api/v1/generate-drafts"


settings = Settings()
