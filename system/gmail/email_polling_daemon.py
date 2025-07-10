"""
Gmail 24x7 Polling Service - Refactored with Modular Architecture

Continuously polls Gmail for new emails and creates draft replies.
Non-blocking approach: polling and email processing are separate.
"""

import asyncio
import logging
import signal
import sys
from typing import Set

from system.gmail.auth.oauth_manager import GmailAuth
from system.gmail.config.settings import settings
from system.gmail.services import (
    HistoryManager,
    EmailFetcher,
    DraftCreator,
    EmailProcessor
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global variables
running = True
# Track background tasks to prevent them from being garbage collected
background_tasks: Set[asyncio.Task] = set()


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global running
    logger.info("Shutdown signal received. Stopping...")
    running = False


class GmailPollingService:
    """Main Gmail polling service using modular architecture"""
    
    def __init__(self):
        self._setup_dependencies()
    
    def _setup_dependencies(self):
        """Setup services with direct dependencies"""
        # Initialize services
        self.auth = GmailAuth()
        self.history_manager = HistoryManager()
        self.email_fetcher = EmailFetcher(
            self.auth, 
            self.history_manager
        )
        self.draft_creator = DraftCreator(self.auth)
        self.email_processor = EmailProcessor(self.draft_creator)
        
        logger.info("Dependencies configured successfully")

    async def process_email_async(self, email: dict):
        """Process a single email asynchronously (background task)"""
        try:
            result = await self.email_processor.process_email(email)
            if result:
                logger.info(f"[BACKGROUND] Email processed: {result}")
            
        except Exception as e:
            logger.error(f"[BACKGROUND] Error in email processing: {e}")

    async def start_polling(self):
        """Start the main polling loop"""
        global running, background_tasks

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        logger.info("Starting Gmail 24x7 polling service ...")

        # Initialize Gmail service
        if not self.email_fetcher.initialize():
            logger.error("Failed to initialize Gmail service")
            sys.exit(1)

        logger.info("Gmail service initialized. Starting continuous polling...")

        while running:
            try:
                # Get new emails (this is fast - just fetching email list)
                new_emails = self.email_fetcher.get_new_emails()

                if new_emails:
                    logger.info(
                        f"[POLLING] Found {len(new_emails)} new emails - creating background tasks"
                    )

                    # Create background tasks for each email (NON-BLOCKING)
                    for email in new_emails:
                        if not running:
                            break

                        # Create background task - doesn't block polling
                        task = asyncio.create_task(self.process_email_async(email))
                        background_tasks.add(task)

                        # Clean up completed tasks to prevent memory leaks
                        task.add_done_callback(background_tasks.discard)

                    logger.info(
                        f"[POLLING] Background tasks created. Active tasks: {len(background_tasks)}"
                    )

                # Continue to next poll immediately (doesn't wait for email processing)
                logger.info(
                    f"[POLLING] Continuing to next poll cycle. Active background tasks: {len(background_tasks)}"
                )
                
                # Get poll interval from settings
                await asyncio.sleep(settings.POLL_INTERVAL_SECONDS)

            except Exception as e:
                logger.error(f"[POLLING] Error in polling loop: {e}")
                await asyncio.sleep(settings.POLL_INTERVAL_SECONDS)

        # Wait for remaining background tasks to complete on shutdown
        if background_tasks:
            logger.info(
                f"Waiting for {len(background_tasks)} background tasks to complete..."
            )
            await asyncio.gather(*background_tasks, return_exceptions=True)

        logger.info("Gmail polling service stopped")


async def main():
    """Main entry point"""
    try:
        service = GmailPollingService()
        await service.start_polling()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Service error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 