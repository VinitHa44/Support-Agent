import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from system.gmail.config.settings import settings
from system.gmail.interfaces.interfaces import AuthInterface


class GmailAuth(AuthInterface):
    def __init__(self):
        self.creds = None
        self.service = None

    def authenticate(self):
        """Authenticate with Gmail API using OAuth2"""
        if os.path.exists(settings.TOKEN_FILE):
            self.creds = Credentials.from_authorized_user_file(
                settings.TOKEN_FILE, settings.GMAIL_SCOPES
            )

        # If there are no valid credentials, get new ones
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                # Refresh expired token
                self.creds.refresh(Request())
            else:
                # Run OAuth flow
                if not os.path.exists(settings.CREDENTIALS_FILE):
                    raise FileNotFoundError(
                        f"Credentials file not found: {settings.CREDENTIALS_FILE}"
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    settings.CREDENTIALS_FILE, settings.GMAIL_SCOPES
                )
                self.creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            os.makedirs(os.path.dirname(settings.TOKEN_FILE), exist_ok=True)
            with open(settings.TOKEN_FILE, "w") as token:
                token.write(self.creds.to_json())

        # Build Gmail service
        self.service = build("gmail", "v1", credentials=self.creds)
        return self.service

    def get_service(self):
        """Get authenticated Gmail service"""
        if not self.service:
            self.authenticate()
        return self.service
