from fastapi import Request
from fastapi.responses import Response
import logging
import time
from typing import Callable, Awaitable

class RequestLoggingMiddleware:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def __call__(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        start_time = time.time()
        
        # Log request
        self.logger.info(
            f"Request: {request.method} {request.url.path}"
            f" from {request.client.host}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        self.logger.info(
            f"Response: {request.method} {request.url.path}"
            f" {response.status_code} in {process_time:.2f}s"
        )
        
        return response
