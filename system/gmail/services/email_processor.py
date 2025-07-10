import re
import logging
from typing import Dict, Optional

import httpx

from system.gmail.interfaces.interfaces import EmailProcessorInterface, DraftCreatorInterface
from system.gmail.config.settings import settings

logger = logging.getLogger(__name__)


class EmailProcessor(EmailProcessorInterface):
    """Processes emails and handles business logic"""
    
    def __init__(self, draft_creator: DraftCreatorInterface):
        self.draft_creator = draft_creator
        self.settings = settings

    async def process_email(self, email: Dict) -> Optional[Dict]:
        """Process a single email and create a draft response"""
        try:
            logger.info(f"[PROCESSOR] Processing email from {email['sender']}")

            # Check if email should be skipped
            if self._is_image_only_email(email):
                logger.info(f"[PROCESSOR] Skipping image-only email {email.get('id', 'unknown')}")
                return None

            # Prepare request for external service
            email_data = {
                "id": email["id"],
                "subject": email["subject"],
                "sender": email["sender"],
                "body": email["body"],
                "attachments": email["attachments"] if email["attachments"] else [],
            }

            # Call external service to generate reply
            response = await self._call_external_service(email_data)

            logger.info(f"[PROCESSOR] Response: {response}")

            if response:
                # Check if the response should be skipped
                is_skip = response.get("is_skip", False)
                
                if is_skip:
                    logger.info(f"[PROCESSOR] Skipping draft creation for email {email['id']} due to is_skip=True")
                    return {"status": "skipped", "message": "Draft creation skipped based on external service response"}
                
                # Extract sender email
                sender_email = self._extract_email_address(email["sender"])

                # Create draft using the body field
                success = self.draft_creator.create_draft(
                    to_email=sender_email,
                    body=response["body"],
                    in_reply_to=email["message_id"],
                    thread_id=email["thread_id"],
                )

                if success:
                    logger.info(f"[PROCESSOR] Draft created for email {email['id']}")
                    return {"status": "success", "draft_created": True}
                else:
                    logger.error(f"[PROCESSOR] Failed to create draft for email {email['id']}")
                    return {"status": "error", "message": "Failed to create draft"}
            else:
                logger.warning(f"[PROCESSOR] No response from external service for email {email['id']}")
                return {"status": "error", "message": "No response from external service"}

        except Exception as e:
            logger.error(f"[PROCESSOR] Error processing email {email.get('id', 'unknown')}: {e}")
            return {"status": "error", "message": str(e)}

    def _is_image_only_email(self, email: Dict) -> bool:
        """
        Check if an email should be skipped based on content.
        
        Logic:
        - Only text -> process (return False)
        - Only image -> skip (return True)  
        - Both text and image -> process (return False)
        - Neither text nor image -> skip (return True)
        """
        # Check if email body has meaningful text content
        body = email.get("body", "").strip()
        has_text = bool(body)
        
        # Check if email has image attachments
        attachments = email.get("attachments", [])
        has_images = any(att.get("is_image", False) for att in attachments)
        
        # Skip if no text content (regardless of whether it has images or not)
        should_skip = not has_text
        
        if should_skip:
            if has_images:
                image_count = len([att for att in attachments if att.get("is_image", False)])
                logger.info(
                    f"Email {email.get('id', 'unknown')} from {email.get('sender', 'unknown')} "
                    f"contains only images ({image_count} images, no text). Skipping processing."
                )
            else:
                logger.info(
                    f"Email {email.get('id', 'unknown')} from {email.get('sender', 'unknown')} "
                    f"has no text content or images. Skipping processing."
                )
        
        return should_skip

    async def _call_external_service(self, email_data: Dict) -> Optional[Dict]:
        """Generate draft reply using external service"""
        try:
            logger.info(f"Generating draft for email: {email_data.get('id', 'no id')}")

            # Prepare payload for the API
            payload = {
                "subject": email_data.get("subject", "No subject"),
                "sender": email_data.get("sender", "no sender email"),
                "body": email_data.get("body", "No body"),
                "attachments": email_data.get("attachments", []),
            }

            headers = {"Content-Type": "application/json"}

            async with httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=30.0, read=1600.0, write=600.0, pool=30.0
                )
            ) as client:
                api_response = await client.post(
                    self.settings.EXTERNAL_SERVICE_URL, json=payload, headers=headers
                )
                api_response.raise_for_status()
                response_data = api_response.json()

            logger.info(f"Successfully generated draft reply for: {email_data.get('id', 'no id')}")
            return response_data["data"]

        except Exception as e:
            logger.error(f"Error generating draft response: {e}")
            return None

    def _extract_email_address(self, from_header: str) -> str:
        """Extract email address from 'From' header"""
        email_pattern = r"<([^>]+)>|([^\s<>]+@[^\s<>]+)"
        matches = re.findall(email_pattern, from_header)

        if matches:
            for match in matches:
                for group in match:
                    if group and "@" in group:
                        return group.strip()

        return from_header.strip() 