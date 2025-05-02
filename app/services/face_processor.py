import cv2
import dlib
import numpy as np
from celery import shared_task
from app.core.config import settings

# Initialize dlib's face detector and shape predictor
face_detector = dlib.get_frontal_face_detector()
shape_predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

@shared_task
async def process_face(image_data: bytes, emoji_type: str) -> bytes:
    """
    Process an image to apply face emoji effects
    
    Args:
        image_data: Raw image data
        emoji_type: Type of emoji to apply
        
    Returns:
        Processed image data
    """
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(image, cv2.IMREAD_GRAYSCALE)
        
        # Detect faces
        faces = face_detector(gray)
        
        for face in faces:
            # Get face landmarks
            landmarks = shape_predictor(gray, face)
            
            # Extract key facial features
            left_eye = (landmarks.part(36).x, landmarks.part(36).y)
            right_eye = (landmarks.part(45).x, landmarks.part(45).y)
            nose = (landmarks.part(30).x, landmarks.part(30).y)
            
            # Apply emoji effect based on type
            if emoji_type == "smile":
                # Example: Add smile effect
                cv2.circle(image, nose, 5, (0, 255, 0), -1)
            elif emoji_type == "surprise":
                # Example: Add surprise effect
                cv2.circle(image, left_eye, 5, (255, 0, 0), -1)
                cv2.circle(image, right_eye, 5, (255, 0, 0), -1)
            
        # Convert processed image back to bytes
        _, buffer = cv2.imencode('.jpg', image)
        return buffer.tobytes()
        
    except Exception as e:
        print(f"Error processing face: {str(e)}")
        raise

async def detect_faces(image_data: bytes) -> dict:
    """
    Detect faces and return facial landmarks
    
    Args:
        image_data: Raw image data
        
    Returns:
        Dictionary containing face detection results
    """
    try:
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(image, cv2.IMREAD_GRAYSCALE)
        
        faces = face_detector(gray)
        results = []
        
        for face in faces:
            landmarks = shape_predictor(gray, face)
            face_data = {
                "bounding_box": {
                    "left": face.left(),
                    "top": face.top(),
                    "right": face.right(),
                    "bottom": face.bottom()
                },
                "landmarks": {
                    "left_eye": (landmarks.part(36).x, landmarks.part(36).y),
                    "right_eye": (landmarks.part(45).x, landmarks.part(45).y),
                    "nose": (landmarks.part(30).x, landmarks.part(30).y),
                    "mouth": (landmarks.part(48).x, landmarks.part(48).y)
                }
            }
            results.append(face_data)
            
        return {"faces": results}
        
    except Exception as e:
        print(f"Error detecting faces: {str(e)}")
        raise
