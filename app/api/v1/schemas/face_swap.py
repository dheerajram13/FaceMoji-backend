from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class FaceSwapRequest(BaseModel):
    image: str  # Base64 encoded image
    emoji_id: str
    landmarks: Optional[Dict[str, List[int]]]
    quality: str = Field(..., regex="^(preview|standard|high)$")
    include_original: bool = False

class FaceSwapResponse(BaseModel):
    status: str
    processing_time_ms: int
    result_image: str  # Base64 encoded result
    adjustment_data: Dict[str, float]
