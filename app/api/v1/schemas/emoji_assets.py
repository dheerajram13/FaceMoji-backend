from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class EmojiAsset(BaseModel):
    id: str
    url: str
    width: int
    height: int
    anchor_points: Dict[str, List[int]]
    animation_data: Optional[Dict[str, List[int]]]

class EmojiAssetsResponse(BaseModel):
    assets: List[EmojiAsset]
    cache_ttl: int  # seconds

class EmojiAssetsRequest(BaseModel):
    ids: List[str]
    style: str = Field(..., regex="^(ios|android|web)$")
    resolution: str = Field(..., regex="^(low|medium|high)$")
