import asyncio
from typing import Dict, Set, Optional
from fastapi import WebSocket
from app.core.config import settings
from app.services.emoji_recommender import emoji_recommender
import time

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.processing_tasks: Dict[str, asyncio.Task] = {}
        self.face_detector = None  # Will be initialized later
        self.device_states: Dict[str, Dict] = {}  # Device state tracking
        self.last_frame_times: Dict[str, float] = {}  # Last frame processing times
        self.target_fps = 30  # Target frames per second
        self.min_frame_interval = 1.0 / self.target_fps  # Minimum interval between frames

    async def connect(self, websocket: WebSocket, device_id: str):
        """Connect a new WebSocket client"""
        await websocket.accept()
        if device_id not in self.active_connections:
            self.active_connections[device_id] = set()
            self.device_states[device_id] = {
                "last_expression": None,
                "confidence_threshold": 0.8,
                "frame_counter": 0,
                "last_frame_time": time.time()
            }
        self.active_connections[device_id].add(websocket)

    def disconnect(self, websocket: WebSocket, device_id: str):
        """Disconnect a WebSocket client"""
        if device_id in self.active_connections:
            self.active_connections[device_id].remove(websocket)
            if not self.active_connections[device_id]:
                del self.active_connections[device_id]
                del self.device_states[device_id]
                del self.last_frame_times[device_id]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to a single client"""
        await websocket.send_json(message)

    async def broadcast(self, message: dict, device_id: str):
        """Broadcast message to all clients for a device"""
        if device_id in self.active_connections:
            for connection in self.active_connections[device_id]:
                await connection.send_json(message)

    async def process_frame(self, device_id: str, frame_data: bytes, frame_info: dict):
        """Process a single frame and send results"""
        try:
            # Get device state
            device_state = self.device_states.get(device_id, {})
            
            # Check frame rate
            current_time = time.time()
            if current_time - device_state.get("last_frame_time", 0) < self.min_frame_interval:
                return
                
            # Process frame with face detector
            detection_result = self.face_detector.detect_faces(frame_data)
            
            # Get recommendations
            recommendations = emoji_recommender.recommend_emojis(frame_data)
            
            # Send result to all connected clients
            await self.broadcast({
                "type": "processing_result",
                "data": {
                    "frame_id": frame_info.get("frame_id"),
                    "timestamp": frame_info.get("timestamp"),
                    "detection": detection_result,
                    "recommendations": recommendations,
                    "processing_time_ms": int((time.time() - current_time) * 1000)
                }
            }, device_id)
            
            # Update device state
            device_state["last_frame_time"] = current_time
            device_state["last_expression"] = recommendations.get("expression")
            device_state["frame_counter"] += 1
            self.device_states[device_id] = device_state
            
        except Exception as e:
            await self.broadcast({
                "type": "error",
                "data": str(e)
            }, device_id)

    async def process_frames(self, device_id: str, websocket: WebSocket):
        """Process frames in real-time with adaptive frame rate"""
        try:
            while True:
                data = await websocket.receive_json()
                
                # Validate frame data
                if "frame" not in data or "frame_id" not in data:
                    await self.broadcast({
                        "type": "error",
                        "data": "Missing required frame data"
                    }, device_id)
                    continue
                    
                frame_data = base64.b64decode(data["frame"])
                frame_info = {
                    "frame_id": data["frame_id"],
                    "timestamp": data.get("timestamp", time.time())
                }
                
                # Process frame with adaptive frame rate
                asyncio.create_task(self.process_frame(device_id, frame_data, frame_info))
                
        except Exception as e:
            await self.broadcast({
                "type": "error",
                "data": str(e)
            }, device_id)

# Initialize WebSocket manager
websocket_manager = WebSocketManager()
