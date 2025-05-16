from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CaptureRequest(BaseModel):
    device_id: str = Field(..., description="Unique device identifier")
    media_type: str = Field(..., description="Media type: 'image' or 'video'")
    content: str = Field(..., description="Base64 encoded media content")
    emoji_id: str = Field(..., description="ID of the emoji used")
    metadata: Optional[dict] = Field(None, description="Additional metadata")

class CaptureResponse(BaseModel):
    status: str
    capture_id: str
    storage_url: str
    share_url: str
    expiry: Optional[datetime] = None

class BatchProcessRequest(BaseModel):
    frames: List[dict] = Field(..., description="List of frames with timestamps")
    emoji_id: str = Field(..., description="ID of the emoji to use")
    processing_options: dict = Field(..., description="Processing options")

class BatchProcessResponse(BaseModel):
    status: str
    job_id: str
    estimated_completion_time: float
    poll_url: str
