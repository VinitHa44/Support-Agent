from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class AuthInterface(ABC):
    """Interface for Gmail authentication"""

    @abstractmethod
    def authenticate(self):
        """Authenticate and return Gmail service"""

    @abstractmethod
    def get_service(self):
        """Get authenticated Gmail service"""


class EmailFetcherInterface(ABC):
    """Interface for fetching emails from Gmail"""

    @abstractmethod
    def get_new_emails(self) -> List[Dict]:
        """Get new emails since last check"""

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the email fetcher"""


class DraftCreatorInterface(ABC):
    """Interface for creating draft emails"""

    @abstractmethod
    def create_draft(
        self,
        to_email: str,
        body: str,
        in_reply_to: str = None,
        thread_id: str = None,
    ) -> bool:
        """Create a draft email"""


class EmailProcessorInterface(ABC):
    """Interface for processing emails"""

    @abstractmethod
    async def process_email(self, email: Dict) -> Optional[Dict]:
        """Process an email and return response"""


class HistoryManagerInterface(ABC):
    """Interface for managing email history tracking"""

    @abstractmethod
    def load_history_id(self) -> Optional[str]:
        """Load last history ID"""

    @abstractmethod
    def save_history_id(self, history_id: str):
        """Save history ID"""
