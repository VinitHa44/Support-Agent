import asyncio
import logging
from collections import defaultdict
from typing import Any, Dict, List, Tuple

from fastapi import WebSocket

from system.src.app.exceptions.websocket_exceptions import WebSocketTimeoutError


class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.response_futures: Dict[str, List[asyncio.Future]] = defaultdict(
            list
        )

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logging.info(f"WebSocket connected for user: {user_id}")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.response_futures:
            for future in self.response_futures[user_id]:
                if not future.done():
                    future.cancel()
            del self.response_futures[user_id]
        logging.info(f"WebSocket disconnected for user: {user_id}")

    async def send_message(self, user_id: str, message: Dict[str, Any]):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_json(message)
        else:
            logging.error(f"No active WebSocket connection for user: {user_id}")
            raise ConnectionError(f"No active connection for user {user_id}")

    async def wait_for_connection(
        self, user_id: str, timeout: int = 30
    ) -> WebSocket:
        """
        Waits for a WebSocket connection to be established for a specific user.
        """
        logging.debug(
            f"Waiting for WebSocket connection for user: {user_id} (max {timeout}s)"
        )
        try:
            connection = await asyncio.wait_for(
                self._get_connection(user_id), timeout=timeout
            )
            return connection
        except asyncio.TimeoutError:
            logging.error(
                f"WebSocket connection timeout for user: {user_id} after {timeout}s"
            )
            raise WebSocketTimeoutError(
                f"No WebSocket connection established for user: {user_id} within {timeout} second timeout. "
                "Frontend may not be running or connected."
            )

    async def _get_connection(self, user_id: str) -> WebSocket:
        while user_id not in self.active_connections:
            # Check for connection every 100ms
            await asyncio.sleep(0.1)
        logging.debug(f"WebSocket connection found for user: {user_id}")
        return self.active_connections[user_id]

    async def wait_for_draft_response(
        self, user_id: str, timeout: int = 3600
    ) -> Tuple[Any | None, str]:
        """
        Waits for a response from the client for a specific draft.
        Returns the response and a status ('success', 'timeout', or 'cancelled').
        """
        future = asyncio.Future()
        self.response_futures[user_id].append(future)

        try:
            logging.debug(
                f"API route is now WAITING for user response (max {timeout / 3600} hour(s))..."
            )
            response = await asyncio.wait_for(future, timeout=timeout)
            return response, "success"
        except asyncio.TimeoutError:
            logging.error(
                f"Timeout waiting for draft response from user: {user_id}"
            )
            return None, "timeout"
        except asyncio.CancelledError:
            logging.warning(
                f"Wait for draft response cancelled for user: {user_id}. "
                f"This can happen if the client disconnects."
            )
            return None, "cancelled"
        finally:
            # Clean up the future from the list
            if future in self.response_futures[user_id]:
                self.response_futures[user_id].remove(future)

    def handle_draft_response(self, user_id: str, response_data: Any):
        if user_id in self.response_futures and self.response_futures[user_id]:
            # Resolve the oldest future for this user (FIFO)
            future = self.response_futures[user_id][0]
            if not future.done():
                future.set_result(response_data)
                logging.debug(
                    "User response received! API route can now continue..."
                )
            else:
                logging.warning(
                    f"Received a response for an already resolved future for user {user_id}"
                )
        else:
            logging.warning(
                f"Received a draft response for user {user_id}, but no pending future was found."
            )


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
