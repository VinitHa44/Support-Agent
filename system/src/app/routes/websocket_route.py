import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from system.src.app.services.websocket_service import websocket_manager
from system.src.app.utils.logging_utils import loggers
router = APIRouter()


@router.websocket("/ws/drafts")
async def websocket_endpoint(websocket: WebSocket, user_id: str = Query(...)):
    """
    WebSocket endpoint for draft review communication

    :param websocket: WebSocket connection
    :param user_id: User identifier for the connection
    """
    await websocket_manager.connect(websocket, user_id)
    try:
        while True:
            # Wait for messages from the frontend
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
            except json.JSONDecodeError as e:
                loggers["websocket"].error(
                    f"Invalid JSON received from user {user_id}: {e}"
                )
                await websocket_manager.send_message(
                    user_id,
                    {
                        "type": "error",
                        "data": {"message": "Invalid JSON format"},
                    },
                )
                continue
            except Exception as e:
                loggers["websocket"].error(
                    f"Error receiving message from user {user_id}: {e}"
                )
                break

            # Handle different message types
            message_type = message.get("type")

            if message_type == "draft_response":
                # Handle draft response from frontend
                response_data = message.get("data", {})
                await websocket_manager.handle_draft_response(
                    user_id, response_data
                )

            elif message_type == "ping":
                # Handle ping/pong for keeping connection alive
                await websocket_manager.send_message(user_id, {"type": "pong"})

            elif message_type == "connection_test_response":
                # Handle connection test response - no action needed
                pass

            elif message_type == "status":
                # Handle status updates
                await websocket_manager.send_message(
                    user_id,
                    {
                        "type": "status_response",
                        "data": {
                            "user_id": user_id,
                            "connected": True,
                            "pending_drafts": user_id
                            in websocket_manager.pending_drafts,
                        },
                    },
                )

            else:
                # Handle unknown message types
                await websocket_manager.send_message(
                    user_id,
                    {
                        "type": "error",
                        "data": {
                            "message": f"Unknown message type: {message_type}"
                        },
                    },
                )

    except WebSocketDisconnect:
        loggers["websocket"].error(f"WebSocket disconnected for user: {user_id}")
    except Exception as e:
        loggers["websocket"].error(f"WebSocket error for user {user_id}: {str(e)}")
    finally:
        websocket_manager.disconnect(user_id)
