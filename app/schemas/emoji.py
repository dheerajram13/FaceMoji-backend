from enum import Enum
from pydantic import BaseModel
from typing import Optional

class EmojiType(str, Enum):
    CAT_EARS = "cat_ears"
    DOG_EARS = "dog_ears"
    BUNNY_EARS = "bunny_ears"
    HORNS = "horns"
    CROWN = "crown"
    GLASSES = "glasses"
    MUSTACHE = "mustache"
    BEARD = "beard"
    HAT = "hat"

class EmojiConfig(BaseModel):
    emoji_type: EmojiType
    size: float = 1.0
    opacity: float = 1.0
    horizontal_offset: float = 0.0
    vertical_offset: float = 0.0

class ProcessImageRequest(BaseModel):
    emoji_config: EmojiConfig
    format: Optional[str] = None
