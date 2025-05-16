from redis import Redis
from datetime import datetime, timedelta
from typing import Optional
import os

class RateLimiter:
    def __init__(self):
        self.redis = Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
        self.rate_limit = 100  # requests per minute
        self.window = 60  # seconds

    async def is_allowed(self, request) -> bool:
        """Check if the request is allowed based on rate limiting rules"""
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"
        
        # Get current count
        count = self.redis.get(key)
        
        # If key doesn't exist, create it
        if not count:
            self.redis.set(key, 1, ex=self.window)
            return True
            
        # If count exists, increment and check
        count = int(count)
        if count >= self.rate_limit:
            return False
            
        # Increment count
        self.redis.incr(key)
        return True
