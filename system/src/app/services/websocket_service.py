import asyncio
import json
from typing import Dict, List

from fastapi import WebSocket


class WebSocketManager:
    def __init__(self):
        # Store active connections with user_id as key
        self.active_connections: Dict[str, WebSocket] = {}
        # Store pending drafts for each user
        self.pending_drafts: Dict[str, Dict] = {}
        # Store response futures for each user
        self.response_futures: Dict[str, asyncio.Future] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept a WebSocket connection and store it"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"WebSocket connected for user: {user_id}")

    def disconnect(self, user_id: str):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.pending_drafts:
            del self.pending_drafts[user_id]
        if user_id in self.response_futures:
            # Cancel any pending futures
            if not self.response_futures[user_id].done():
                self.response_futures[user_id].cancel()
            del self.response_futures[user_id]
        print(f"WebSocket disconnected for user: {user_id}")

    async def send_draft_for_review(
        self, user_id: str, draft_data: Dict
    ) -> Dict:
        """
        Send draft data to frontend for review and wait for response

        :param user_id: User identifier
        :param draft_data: Draft data to send for review
        :return: Final draft response from user
        """
        if user_id not in self.active_connections:
            raise Exception(
                f"No active WebSocket connection for user: {user_id}"
            )

        websocket = self.active_connections[user_id]

        # Store the draft data
        self.pending_drafts[user_id] = draft_data

        # Create a future to wait for the response
        future = asyncio.Future()
        self.response_futures[user_id] = future

        try:
            print(f"Sending drafts to frontend for user {user_id}...")

            # Send draft data to frontend
            await websocket.send_text(
                json.dumps({"type": "draft_review", "data": draft_data})
            )

            print(
                f"Drafts sent. API route is now WAITING for user response (max 5 minutes)..."
            )

            # Wait for user response (with timeout) - THIS BLOCKS THE API ROUTE
            response = await asyncio.wait_for(
                future, timeout=300.0
            )  # 5 minutes timeout

            print(f"User response received! API route can now continue...")
            return response

        except asyncio.TimeoutError:
            # Cleanup on timeout
            if user_id in self.response_futures:
                del self.response_futures[user_id]
            if user_id in self.pending_drafts:
                del self.pending_drafts[user_id]
            raise Exception(
                "Draft review timeout - no response received within 5 minutes"
            )

        except Exception as e:
            # Cleanup on error
            if user_id in self.response_futures:
                del self.response_futures[user_id]
            if user_id in self.pending_drafts:
                del self.pending_drafts[user_id]
            raise e

    async def handle_draft_response(self, user_id: str, response_data: Dict):
        """
        Handle the draft response from frontend

        :param user_id: User identifier
        :param response_data: Response data from frontend
        """
        if user_id in self.response_futures:
            future = self.response_futures[user_id]
            if not future.done():
                future.set_result(response_data)

            # Cleanup
            del self.response_futures[user_id]
            if user_id in self.pending_drafts:
                del self.pending_drafts[user_id]

    async def send_message(self, user_id: str, message: Dict):
        """Send a message to a specific user"""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_text(json.dumps(message))

    async def broadcast(self, message: Dict):
        """Broadcast a message to all connected users"""
        for websocket in self.active_connections.values():
            await websocket.send_text(json.dumps(message))

    def get_connected_users(self) -> List[str]:
        """Get list of connected user IDs"""
        return list(self.active_connections.keys())


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
