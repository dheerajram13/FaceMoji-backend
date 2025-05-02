from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from app.services.face_processor import process_face, detect_faces
import io

api_router = APIRouter()

@api_router.post("/process")
async def process_image(
    file: UploadFile = File(...),
    emoji_type: str = "smile"
):
    """
    Process an image with face emoji effects
    
    Args:
        file: Image file to process
        emoji_type: Type of emoji effect to apply
        
    Returns:
        Processed image
    """
    try:
        # Read the uploaded file
        image_data = await file.read()
        
        # Process the image with Celery task
        result = await process_face.delay(image_data, emoji_type)
        processed_image = await result.get()
        
        # Return the processed image
        return StreamingResponse(
            io.BytesIO(processed_image),
            media_type="image/jpeg"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/detect")
async def detect_faces_in_image(file: UploadFile = File(...)):
    """
    Detect faces in an image
    
    Args:
        file: Image file to analyze
        
    Returns:
        Face detection results
    """
    try:
        image_data = await file.read()
        results = await detect_faces(image_data)
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
