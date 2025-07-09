import base64
import json
import logging
import os
from datetime import datetime
from email.mime.text import MIMEText
from typing import Dict, List, Optional

from system.gmail.oauth_manager import GmailAuth
from config import settings
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.auth = GmailAuth()
        self.service = None
        self.current_message_id = (
            None  # For tracking during attachment processing
        )
        self.is_first_poll_after_startup = (
            True  # Flag to track if this is first poll since startup
        )

    def _load_history_id(self) -> Optional[str]:
        """Load last history ID from JSON file"""
        try:
            if os.path.exists(settings.HISTORY_FILE):
                with open(settings.HISTORY_FILE, "r") as f:
                    data = json.load(f)
                    return data.get("last_history_id")
        except Exception as e:
            logger.error(f"Error loading history ID: {e}")
        return None

    def _save_history_id(self, history_id: str):
        """Save history ID to JSON file"""
        try:
            os.makedirs(os.path.dirname(settings.HISTORY_FILE), exist_ok=True)
            data = {
                "last_history_id": history_id,
                "last_updated": datetime.now().isoformat(),
            }
            with open(settings.HISTORY_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving history ID: {e}")

    def initialize(self):
        """Initialize the Gmail service"""
        try:
            self.service = self.auth.get_service()

            # Load existing history ID or get current one
            last_history_id = self._load_history_id()

            if not last_history_id:
                # Get initial history ID from profile
                profile = self.service.users().getProfile(userId="me").execute()
                last_history_id = profile.get("historyId")
                self._save_history_id(last_history_id)

            logger.info(
                f"Gmail service initialized. History ID: {last_history_id}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Gmail service: {e}")
            return False

    def get_new_emails(self) -> List[Dict]:
        """Get new emails since last check using history API for efficiency"""
        if not self.service:
            if not self.initialize():
                return []

        try:
            new_emails = []

            # MANDATORY: Always fetch most recent unread email on startup, regardless of stored history
            if self.is_first_poll_after_startup:
                logger.info(
                    "STARTUP: Mandatory fetch of most recent unread email (ignoring stored history)"
                )
                new_emails = self._get_recent_unread_emails()

                # After startup poll, get current history ID for future polls
                profile = self.service.users().getProfile(userId="me").execute()
                current_history_id = profile.get("historyId")
                self._save_history_id(current_history_id)

                # Mark that startup is complete
                self.is_first_poll_after_startup = False
                logger.info(
                    f"STARTUP: Complete. Set history ID to {current_history_id} for future polls"
                )

            else:
                # Normal flow after startup: Use history API to get changes since last check
                last_history_id = self._load_history_id()

                if last_history_id:
                    history_response = (
                        self.service.users()
                        .history()
                        .list(
                            userId="me",
                            startHistoryId=last_history_id,
                            historyTypes=["messageAdded"],
                        )
                        .execute()
                    )

                    changes = history_response.get("history", [])
                    if changes:
                        # Update and save history ID
                        new_history_id = history_response.get("historyId")
                        self._save_history_id(new_history_id)

                        # Process new messages
                        for change in changes:
                            messages_added = change.get("messagesAdded", [])
                            for msg_added in messages_added:
                                message_id = msg_added["message"]["id"]
                                email_data = self._get_email_details(message_id)
                                if email_data:
                                    new_emails.append(email_data)
                else:
                    # Fallback: If somehow no history ID exists, get recent unread
                    logger.warning(
                        "No history ID found during normal polling - getting recent unread"
                    )
                    new_emails = self._get_recent_unread_emails()

            logger.info(f"Found {len(new_emails)} new emails")
            return new_emails

        except HttpError as e:
            logger.error(f"Gmail API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting new emails: {e}")
            return []

    def _get_recent_unread_emails(self) -> List[Dict]:
        """Get the most recent unread email (used for startup and fallback)"""
        try:
            logger.info("Getting the most recent unread email from INBOX")

            # Search for unread emails in inbox, get only the most recent one
            results = (
                self.service.users()
                .messages()
                .list(
                    userId="me",
                    q="is:unread in:inbox",  # Ensure we only get inbox unread emails
                    maxResults=2,  # Only get the most recent unread email
                )
                .execute()
            )

            messages = results.get("messages", [])
            emails = []

            if messages:
                # Process only the single most recent unread email
                email_data = self._get_email_details(messages[0]["id"])
                if email_data:
                    emails.append(email_data)
                    logger.info(
                        f"Found most recent unread email from {email_data['sender']} - Subject: {email_data['subject']}"
                    )
                else:
                    logger.info(
                        "Most recent email was filtered out (likely not INBOX+UNREAD)"
                    )
            else:
                logger.info("No unread emails found in INBOX")

            return emails

        except Exception as e:
            logger.error(f"Error getting recent unread email: {e}")
            return []

    def _get_email_details(self, message_id: str) -> Optional[Dict]:
        """Get detailed email information including attachments"""
        try:
            # Store current message ID for attachment processing
            self.current_message_id = message_id

            # Get message details without marking as read
            message = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )

            # Check labels first - only process INBOX + UNREAD emails
            labels = message.get("labelIds", [])

            # Filter: must have both INBOX and UNREAD labels
            if "INBOX" not in labels or "UNREAD" not in labels:
                logger.info(
                    f"Skipping email {message_id} - Labels: {labels} (not INBOX+UNREAD)"
                )
                return None

            logger.info(
                f"Processing email {message_id} - Valid INBOX+UNREAD labels"
            )

            headers = message["payload"].get("headers", [])

            # Extract relevant headers
            subject = self._get_header_value(headers, "Subject")
            sender = self._get_header_value(headers, "From")
            date = self._get_header_value(headers, "Date")
            message_id_header = self._get_header_value(headers, "Message-ID")
            in_reply_to = self._get_header_value(headers, "In-Reply-To")

            # Get email body and attachments (with image data for AI processing)
            body, attachments = self._extract_content_and_attachments(
                message["payload"]
            )

            # Email is confirmed as unread and in inbox
            email_data = {
                "id": message_id,
                "thread_id": message.get("threadId"),
                "subject": subject,
                "sender": sender,
                "date": date,
                "message_id": message_id_header,
                "in_reply_to": in_reply_to,
                "body": body,
                "attachments": attachments,
                "has_images": len(
                    [att for att in attachments if att["is_image"]]
                )
                > 0,
                "is_unread": True,
                "internal_date": message.get("internalDate"),
                "labels": labels,
            }

            return email_data

        except Exception as e:
            logger.error(f"Error getting email details for {message_id}: {e}")
            return None

    def _get_header_value(self, headers: List[Dict], name: str) -> str:
        """Extract header value by name"""
        for header in headers:
            if header["name"].lower() == name.lower():
                return header["value"]
        return ""

    def _extract_content_and_attachments(
        self, payload: Dict
    ) -> tuple[str, List[Dict]]:
        """Extract email body and attachment information from payload"""
        body = ""
        attachments = []

        def process_part(part):
            nonlocal body, attachments

            mime_type = part.get("mimeType", "")
            filename = part.get("filename", "")

            # Handle text content
            if mime_type == "text/plain":
                if "data" in part.get("body", {}):
                    text_data = base64.urlsafe_b64decode(
                        part["body"]["data"]
                    ).decode("utf-8")
                    if text_data.strip():
                        body = text_data

            # Handle attachments (including images)
            elif filename and part.get("body", {}).get("attachmentId"):
                attachment_info = {
                    "filename": filename,
                    "mime_type": mime_type,
                    "size": part.get("body", {}).get("size", 0),
                    "attachment_id": part["body"]["attachmentId"],
                    "is_image": mime_type.startswith("image/"),
                    "is_inline": "inline" in part.get("headers", []),
                    "base64_data": None,
                    "data_uri": None,
                }

                # For images, add base64 data for AI processing
                if attachment_info["is_image"]:
                    try:
                        image_data = self.get_attachment_data(
                            self.current_message_id,
                            part["body"]["attachmentId"],
                        )
                        if image_data:
                            attachment_info["base64_data"] = base64.b64encode(
                                image_data
                            ).decode("utf-8")
                            attachment_info["data_uri"] = (
                                f"data:{mime_type};base64,{attachment_info['base64_data']}"
                            )
                            logger.info(
                                f"Added base64 data for image: {filename}"
                            )
                        else:
                            attachment_info["base64_data"] = None
                            attachment_info["data_uri"] = None
                            logger.warning(
                                f"Failed to download image data for: {filename}"
                            )
                    except Exception as e:
                        logger.error(f"Error processing image {filename}: {e}")
                        attachment_info["base64_data"] = None
                        attachment_info["data_uri"] = None

                attachments.append(attachment_info)
                logger.info(f"Found attachment: {filename} ({mime_type})")

        # Process payload parts
        if "parts" in payload:
            # Multipart message
            for part in payload["parts"]:
                if "parts" in part:
                    # Nested multipart
                    for nested_part in part["parts"]:
                        process_part(nested_part)
                else:
                    process_part(part)
        else:
            # Single part message
            process_part(payload)

        return body, attachments

    def get_attachment_data(
        self, message_id: str, attachment_id: str
    ) -> Optional[bytes]:
        """Download attachment data from Gmail"""
        try:
            attachment = (
                self.service.users()
                .messages()
                .attachments()
                .get(userId="me", messageId=message_id, id=attachment_id)
                .execute()
            )

            # Decode attachment data
            data = base64.urlsafe_b64decode(attachment["data"])
            return data

        except Exception as e:
            logger.error(f"Error downloading attachment {attachment_id}: {e}")
            return None

    def create_draft(
        self,
        to_email: str,
        body: str,
        in_reply_to: str = None,
        thread_id: str = None,
    ) -> bool:
        """Create a draft email"""
        try:
            if not self.service:
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
                self.service.users()
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
