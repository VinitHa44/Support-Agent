import base64
import logging
from email.mime.text import MIMEText

from system.gmail.interfaces.interfaces import DraftCreatorInterface, AuthInterface

logger = logging.getLogger(__name__)


class DraftCreator(DraftCreatorInterface):
    """Creates draft emails in Gmail"""
    
    def __init__(self, auth: AuthInterface):
        self.auth = auth
        self.gmail_service = None
    
    def initialize(self) -> bool:
        """Initialize Gmail service for draft creation"""
        try:
            self.gmail_service = self.auth.get_service()
            return True
        except Exception as e:
            logger.error(f"Failed to initialize draft creator: {e}")
            return False

    def create_draft(
        self,
        to_email: str,
        body: str,
        in_reply_to: str = None,
        thread_id: str = None,
    ) -> bool:
        """Create a draft email"""
        try:
            if not self.gmail_service:
                if not self.initialize():
                    return False

            # Prepare email message
            message = {
                "raw": self._create_message_raw(
                    to_email, body, in_reply_to
                )
            }

            # Create draft
            draft_body = {"message": message}

            if thread_id:
                draft_body["message"]["threadId"] = thread_id

            draft = (
                self.gmail_service.users()
                .drafts()
                .create(userId="me", body=draft_body)
                .execute()
            )

            logger.info(f"Draft created successfully: {draft['id']}")
            return True

        except Exception as e:
            logger.error(f"Error creating draft: {e}")
            return False

    def _create_message_raw(
        self, to_email: str, body: str, in_reply_to: str = None
    ) -> str:
        """Create raw email message"""
        message = MIMEText(body)
        message["to"] = to_email
        if in_reply_to:
            message["In-Reply-To"] = in_reply_to
            message["References"] = in_reply_to

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode(
            "utf-8"
        )
        return raw_message 