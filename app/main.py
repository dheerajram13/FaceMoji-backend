from fastapi import FastAPI, Request, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.rate_limiter import RateLimiter
from app.core.middleware import RequestLoggingMiddleware
from app.services.websocket_manager import websocket_manager
import logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize rate limiter
rate_limiter = RateLimiter()

app = FastAPI(
    title="FaceMoji API",
    description="API for FaceMoji - AI-powered face manipulation service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081", "https://localhost:8081"],  # Only allow frontend
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "WS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.add_middleware(
    GZipMiddleware,
    minimum_size=1000
)

app.add_middleware(RequestLoggingMiddleware)

# Rate limiting middleware
@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if not await rate_limiter.is_allowed(request):
        raise HTTPException(
            status_code=429,
            detail="Too many requests"
        )
    return await call_next(request)

# WebSocket connection handler
@app.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str):
    """
    WebSocket endpoint handler
    """
    await websocket_manager.connect(websocket, device_id)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket_manager.broadcast({"message": data}, device_id)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        websocket_manager.disconnect(websocket, device_id)

# Error handling
@app.exception_handler(Exception)
def handle_exception(request: Request, exc: Exception):
    logger.error(f"Error processing request: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

app.include_router(api_router, prefix="/api/v1")
