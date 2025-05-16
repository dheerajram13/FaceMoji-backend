from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class FacialLandmark(BaseModel):
    type: str
    position: List[int] = Field(..., min_items=2, max_items=2)

class ExpressionAnalysis(BaseModel):
    primary: str
    confidence: float = Field(..., ge=0, le=1)
    secondary: Optional[str]
    secondary_confidence: Optional[float] = Field(None, ge=0, le=1)

class FaceDetectionResponse(BaseModel):
    status: str
    processing_time_ms: int
    facial_landmarks: FacialLandmark
    expression: ExpressionAnalysis
    recommended_emoji_id: str
    alternative_emoji_ids: List[str]

class FaceDetectionRequest(BaseModel):
    image: str  # Base64 encoded image
    device_id: str
    image_format: str = "jpeg"
    resolution: dict
    optimization_level: str = Field(..., regex="^(low|medium|high)$")
