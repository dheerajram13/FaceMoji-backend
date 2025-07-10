from fastapi import APIRouter, HTTPException, File, UploadFile, Depends
from fastapi.responses import StreamingResponse
from app.services.face_detector import face_detector
from app.services.emoji_recommender import emoji_recommender
from app.services.face_swapper import face_swapper
import io
import time
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/detect-face")
async def detect_face_endpoint(file: UploadFile = File(...)):
    """
    Detect faces and analyze expressions
    """
    try:
        # Validate file
        if not file.content_type.startswith('image/'):
            raise HTTPException(400, "File must be an image")
        
        # Read image data
        image_data = await file.read()
        
        # Detect faces
        detection_result = face_detector.detect_faces(image_data)
        
        if detection_result.get("error"):
            raise HTTPException(400, detection_result["error"])
        
        if not detection_result["faces"]:
            raise HTTPException(404, "No faces detected in image")
        
        # Get primary face (first detected)
        primary_face = detection_result["faces"][0]
        
        # Get emoji recommendation
        recommendation = emoji_recommender.recommend_emoji(primary_face)
        
        return {
            "status": "success",
            "processing_time_ms": detection_result["processing_time_ms"],
            "face_count": len(detection_result["faces"]),
            "primary_face": {
                "bbox": primary_face["bbox"],
                "landmarks": primary_face["landmarks"],
                "expression": primary_face["expression"]
            },
            "emoji_recommendation": recommendation
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Face detection endpoint error: {e}")
        raise HTTPException(500, f"Processing failed: {str(e)}")

@router.post("/process-image")
async def process_image_endpoint(
    file: UploadFile = File(...),
    emoji_id: str = None
):
    """
    Process image with face swap
    """
    try:
        # Validate inputs
        if not file.content_type.startswith('image/'):
            raise HTTPException(400, "File must be an image")
        
        # Read image data
        image_data = await file.read()
        
        # Detect faces first
        detection_result = face_detector.detect_faces(image_data)
        
        if detection_result.get("error"):
            raise HTTPException(400, detection_result["error"])
        
        if not detection_result["faces"]:
            raise HTTPException(404, "No faces detected")
        
        # Get emoji recommendation if not specified
        primary_face = detection_result["faces"][0]
        if not emoji_id:
            recommendation = emoji_recommender.recommend_emoji(primary_face)
            emoji_id = recommendation["primary"]["id"]
        
        # Process face swap
        processed_image = await face_swapper.swap_face(
            image_data, primary_face, emoji_id
        )
        
        # Return processed image
        return StreamingResponse(
            io.BytesIO(processed_image),
            media_type="image/jpeg",
            headers={"Content-Disposition": "attachment; filename=face_swap.jpg"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image processing endpoint error: {e}")
        raise HTTPException(500, f"Processing failed: {str(e)}")

@router.get("/emojis")
async def get_emojis():
    """Get all available emojis"""
    try:
        emojis = emoji_recommender.get_all_emojis()
        return {
            "emojis": emojis,
            "total_count": len(emojis)
        }
    except Exception as e:
        logger.error(f"Get emojis error: {e}")
        raise HTTPException(500, "Failed to retrieve emojis")

@router.get("/emojis/{expression}")
async def get_emojis_by_expression(expression: str):
    """Get emojis filtered by expression"""
    try:
        emojis = emoji_recommender.get_emojis_by_expression(expression)
        return {
            "expression": expression,
            "emojis": emojis,
            "count": len(emojis)
        }
    except Exception as e:
        logger.error(f"Get emojis by expression error: {e}")
        raise HTTPException(500, "Failed to retrieve emojis")
