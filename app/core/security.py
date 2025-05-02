from datetime import timedelta

from app.core.config import settings

ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
ALGORITHM: str = "HS256"
SECRET_KEY: str = settings.SECRET_KEY
