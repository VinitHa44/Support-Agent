"""
Gmail 24x7 Polling Service

Continuously polls Gmail for new emails and creates draft replies.
Non-blocking approach: polling and email processing are separate.
"""

import asyncio
import logging
import signal
import sys
from typing import Dict
import time
from email_service import EmailService
from config import POLL_INTERVAL_SECONDS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
email_service = EmailService()
running = True
# Track background tasks to prevent them from being garbage collected
background_tasks = set()


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global running
    logger.info("Shutdown signal received. Stopping...")
    running = False


async def process_email_async(email: Dict):
    """Process a single email asynchronously (background task)"""
    try:
        logger.info(f"[BACKGROUND] Processing email from {email['sender']} - {email['subject']}")
        
        # Log attachment info
        if email['attachments']:
            logger.info(f"[BACKGROUND] Email has {len(email['attachments'])} attachments")
            for att in email['attachments']:
                logger.info(f"[BACKGROUND]   - {att['filename']} ({att['mime_type']}) {'[IMAGE]' if att['is_image'] else ''}")
        
        # Prepare request for external service
        email_data = {
            'id': email['id'],
            'subject': email['subject'],
            'sender': email['sender'],
            'body': email['body'],
            'date': email['date'],
            'thread_id': email['thread_id'],
            'attachments': email['attachments'],
            'has_images': email['has_images']
        }
        
        # Call external service to generate reply (non-blocking)
        response = await call_external_service(email_data)
        
        if response:
            # Extract sender email
            sender_email = extract_email_address(email['sender'])
            
            # Create draft
            success = email_service.create_draft(
                to_email=sender_email,
                body=response['body'],
                in_reply_to=email['message_id'],
                thread_id=email['thread_id']
            )
            
            if success:
                logger.info(f"[BACKGROUND] Draft created for email {email['id']}")
            else:
                logger.error(f"[BACKGROUND] Failed to create draft for email {email['id']}")
        else:
            logger.warning(f"[BACKGROUND] No response from external service for email {email['id']}")
    
    except Exception as e:
        logger.error(f"[BACKGROUND] Error processing email {email.get('id', 'unknown')}: {e}")

async def call_external_service(email_data: Dict) -> Dict:
    """Generate dummy draft reply for the given email"""
    try:
        logger.info(f"Generating dummy draft for email: {email_data.get('subject', 'No subject')}")
        
        # Extract email details
        subject = email_data.get('subject', '')
        sender = email_data.get('sender', '')
        body = email_data.get('body', '')
        has_images = email_data.get('has_images', False)
        attachments = email_data.get('attachments', [])
        
        # Count image attachments
        image_count = len([att for att in attachments if att.get('is_image', False)])
        
        # Create a personalized dummy response
        reply_body = f"""Thank you for your email regarding "{subject}".

I have received your message and will review it carefully."""
        
        if has_images and image_count > 0:
            reply_body += f"""

I noticed you included {image_count} image(s) in your email. I will review the visual content as well."""
        
        if len(attachments) > image_count:
            doc_count = len(attachments) - image_count
            reply_body += f"""

I also see you've attached {doc_count} document(s). I will examine these materials."""
        
        reply_body += """

I will get back to you within 24 hours with a detailed response.

Best regards"""
        
        response = {
            "body": reply_body
        }
        
        logger.info(f"Generated dummy draft reply: {subject}")
        
        await asyncio.sleep(60)
        return response
        
    except Exception as e:
        logger.error(f"Error generating dummy response: {e}")
        return None

def extract_email_address(from_header: str) -> str:
    """Extract email address from 'From' header"""
    import re
    
    email_pattern = r'<([^>]+)>|([^\s<>]+@[^\s<>]+)'
    matches = re.findall(email_pattern, from_header)
    
    if matches:
        for match in matches:
            for group in match:
                if group and '@' in group:
                    return group.strip()
    
    return from_header.strip()

async def main():
    """Main polling loop - non-blocking approach"""
    global running, background_tasks
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting Gmail 24x7 polling service (NON-BLOCKING MODE)...")
    
    # Initialize Gmail service
    if not email_service.initialize():
        logger.error("Failed to initialize Gmail service")
        sys.exit(1)
    
    logger.info("Gmail service initialized. Starting continuous polling...")
    
    while running:
        try:
            # Get new emails (this is fast - just fetching email list)
            new_emails = email_service.get_new_emails()
            
            if new_emails:
                logger.info(f"[POLLING] Found {len(new_emails)} new emails - creating background tasks")
                
                # Create background tasks for each email (NON-BLOCKING)
                for email in new_emails:
                    if not running:
                        break
                    
                    # Create background task - doesn't block polling
                    task = asyncio.create_task(process_email_async(email))
                    background_tasks.add(task)
                    
                    # Clean up completed tasks to prevent memory leaks
                    task.add_done_callback(background_tasks.discard)
                
                logger.info(f"[POLLING] Background tasks created. Active tasks: {len(background_tasks)}")
            
            # Continue to next poll immediately (doesn't wait for email processing)
            logger.info(f"[POLLING] Continuing to next poll cycle. Active background tasks: {len(background_tasks)}")
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
            
        except Exception as e:
            logger.error(f"[POLLING] Error in polling loop: {e}")
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
    
    # Wait for remaining background tasks to complete on shutdown
    if background_tasks:
        logger.info(f"Waiting for {len(background_tasks)} background tasks to complete...")
        await asyncio.gather(*background_tasks, return_exceptions=True)
    
    logger.info("Gmail polling service stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Service error: {e}")
        sys.exit(1) 