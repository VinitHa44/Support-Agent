from typing import List

from pydantic import BaseModel


class Settings(BaseModel):
    GMAIL_SCOPES: List[str] = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.compose",
    ]
    CREDENTIALS_FILE: str = (
        "/Users/tapankheni/Developer/support-agent/tokens/credentials.json"
    )
    TOKEN_FILE: str = (
        "/Users/tapankheni/Developer/support-agent/tokens/gmail_tokens.json"
    )
    HISTORY_FILE: str = (
        "/Users/tapankheni/Developer/support-agent/tokens/history.json"
    )
    POLL_INTERVAL_SECONDS: int = 25
    EXTERNAL_SERVICE_URL: str = "http://localhost:8000/generate-drafts"


settings = Settings()
