import json
import logging
import os
from datetime import datetime
from typing import Optional

from system.gmail.config.settings import settings
from system.gmail.interfaces.interfaces import HistoryManagerInterface

logger = logging.getLogger(__name__)


class HistoryManager(HistoryManagerInterface):
    """Manages email history tracking for efficient polling"""

    def __init__(self):
        self.settings = settings

    def load_history_id(self) -> Optional[str]:
        """Load last history ID from JSON file"""
        try:
            if os.path.exists(self.settings.HISTORY_FILE):
                with open(self.settings.HISTORY_FILE, "r") as f:
                    data = json.load(f)
                    return data.get("last_history_id")
        except Exception as e:
            logger.error(f"Error loading history ID: {e}")
        return None

    def save_history_id(self, history_id: str):
        """Save history ID to JSON file"""
        try:
            os.makedirs(
                os.path.dirname(self.settings.HISTORY_FILE), exist_ok=True
            )
            data = {
                "last_history_id": history_id,
                "last_updated": datetime.now().isoformat(),
            }
            with open(self.settings.HISTORY_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving history ID: {e}")
