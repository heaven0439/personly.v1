# backend/app/routers/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import json

router = APIRouter(prefix="/api/ws", tags=["WebSockets"])

class ConnectionManager:
    def __init__(self):
        # Maps a Personly ID (int) to an active WebSocket connection
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, personly_id: int):
        await websocket.accept()
        self.active_connections[personly_id] = websocket
        print(f"User {personly_id} connected. Total active: {len(self.active_connections)}")

    def disconnect(self, personly_id: int):
        if personly_id in self.active_connections:
            del self.active_connections[personly_id]
            print(f"User {personly_id} disconnected. Total active: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, personly_id: int):
        websocket = self.active_connections.get(personly_id)
        if websocket:
            await websocket.send_text(json.dumps(message))
            return True
        return False

manager = ConnectionManager()

@router.websocket("/{personly_id}")
async def websocket_endpoint(websocket: WebSocket, personly_id: int):
    await manager.connect(websocket, personly_id)
    try:
        while True:
            # Wait for messages from the frontend
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # The message must specify who it is meant for (target)
            target_id = message.get("target")
            if target_id:
                # Forward the message instantly to the target user
                success = await manager.send_personal_message(message, int(target_id))
                
                # If target is offline and it's a call request, tell the caller they are offline
                if not success and message.get("type") == "call_request":
                    await websocket.send_text(json.dumps({
                        "type": "call_failed",
                        "reason": "User is currently offline."
                    }))
    except WebSocketDisconnect:
        manager.disconnect(personly_id)