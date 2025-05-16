import asyncio
from typing import Dict, Set
from fastapi import WebSocket
from app.core.config import settings

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.processing_tasks: Dict[str, asyncio.Task] = {}
        self.face_detector = None  # Will be initialized later

    async def connect(self, websocket: WebSocket, device_id: str):
        """Connect a new WebSocket client"""
        await websocket.accept()
        if device_id not in self.active_connections:
            self.active_connections[device_id] = set()
        self.active_connections[device_id].add(websocket)

    def disconnect(self, websocket: WebSocket, device_id: str):
        """Disconnect a WebSocket client"""
        if device_id in self.active_connections:
            self.active_connections[device_id].remove(websocket)
            if not self.active_connections[device_id]:
                del self.active_connections[device_id]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to a single client"""
        await websocket.send_json(message)

    async def broadcast(self, message: dict, device_id: str):
        """Broadcast message to all clients for a device"""
        if device_id in self.active_connections:
            for connection in self.active_connections[device_id]:
                await connection.send_json(message)

    async def process_frame(self, device_id: str, frame_data: bytes):
        """Process a single frame and send results"""
        try:
            # Process frame with face detector
            result = self.face_detector.detect_faces(frame_data)
            
            # Send result to all connected clients
            await self.broadcast({
                "type": "face_detection",
                "data": result
            }, device_id)
            
        except Exception as e:
            await self.broadcast({
                "type": "error",
                "data": str(e)
            }, device_id)

    async def process_frames(self, device_id: str, websocket: WebSocket):
        """Process frames in real-time"""
        try:
            while True:
                data = await websocket.receive_json()
                if "frame" in data:
                    frame_data = base64.b64decode(data["frame"])
                    asyncio.create_task(self.process_frame(device_id, frame_data))
                
        except Exception as e:
            await self.broadcast({
                "type": "error",
                "data": str(e)
            }, device_id)

# Initialize WebSocket manager
websocket_manager = WebSocketManager()
