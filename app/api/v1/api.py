from fastapi import APIRouter, HTTPException, File, UploadFile, Query, Body
from fastapi.responses import StreamingResponse
from app.services.face_processor import process_face, detect_faces
import io

api_router = APIRouter()

@api_router.post("/process")
async def process_image(
    file: UploadFile = File(...),
    emoji_config: dict = Body(..., description="Emoji configuration")
):
    """
    Process an image with face emoji effects
    
    Args:
        file: Image file to process
        emoji_config: Configuration for emoji effect (emoji_type, size, opacity, offsets)
        
    Returns:
        Processed image
    """
    try:
        # Read the uploaded file
        image_data = await file.read()
        
        # Process the image with Celery task
        result = process_face.delay(image_data, emoji_config)
        
        # Wait for the result with a timeout
        processed_image = result.get(timeout=30)  # Wait for 30 seconds
        
        # Return the processed image
        return StreamingResponse(
            io.BytesIO(processed_image),
            media_type="image/jpeg"
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}"
        )

@api_router.post("/detect")
async def detect_faces_in_image(
    file: UploadFile = File(...)
):
    """
    Detect faces in an image
    
    Args:
        file: Image file to analyze
        
    Returns:
        Face detection results
    """
    try:
        # Read the file data
        image_data = await file.read()
        
        # Process the image
        results = await detect_faces(image_data)
        return results
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error detecting faces: {str(e)}"
        )
