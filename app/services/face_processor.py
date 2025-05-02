import cv2
import dlib
import numpy as np
from celery import Celery
import os
from app.core.config import settings

# Initialize Celery with Redis configuration
app = Celery(
    'facemoji_tasks',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0',
    include=['app.services.face_processor']
)

# Initialize dlib's face detector and shape predictor
face_detector = dlib.get_frontal_face_detector()
shape_predictor_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../..", "shape_predictor_68_face_landmarks.dat")
shape_predictor = dlib.shape_predictor(shape_predictor_path)

@app.task
def process_face(image_data: bytes, emoji_type: str) -> bytes:
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
        if nparr.size == 0:
            raise ValueError("Invalid image data")
            
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Failed to decode image")
            
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_detector(gray)
        if len(faces) == 0:
            logger.info("No faces detected in the image")
            return image
            
        for face in faces:
            try:
                # Get face landmarks
                landmarks = shape_predictor(gray, face)
                
                # Extract key facial features
                left_eye = (landmarks.part(36).x, landmarks.part(36).y)
                right_eye = (landmarks.part(45).x, landmarks.part(45).y)
                nose = (landmarks.part(30).x, landmarks.part(30).y)
                
                # Get all facial landmarks
                landmarks = [(p.x, p.y) for p in landmarks.parts()]
                
                # Draw emoji effect based on type
                if emoji_type == "smile":
                    # Get mouth corners
                    left_mouth = landmarks[48]
                    right_mouth = landmarks[54]
                    top_mouth = landmarks[51]
                    
                    # Draw curved smile
                    points = np.array([
                        (left_mouth[0], left_mouth[1]),
                        (left_mouth[0] + (right_mouth[0] - left_mouth[0])//2, top_mouth[1] + 10),
                        (right_mouth[0], right_mouth[1])
                    ], np.int32)
                    
                    cv2.polylines(image, [points], False, (0, 255, 0), 2)
                    
                    # Add glow effect
                    cv2.circle(image, left_mouth, 10, (0, 255, 0, 0.3), -1)
                    cv2.circle(image, right_mouth, 10, (0, 255, 0, 0.3), -1)
                    
                elif emoji_type == "surprise":
                    # Get eye corners
                    left_eye = landmarks[36:42]
                    right_eye = landmarks[42:48]
                    
                    # Draw surprised eyes
                    for eye in [left_eye, right_eye]:
                        # Calculate eye center
                        eye_center = (int(np.mean([p[0] for p in eye])), int(np.mean([p[1] for p in eye])))
                        
                        # Draw large white circle
                        cv2.circle(image, eye_center, 15, (255, 255, 255), -1)
                        
                        # Draw black pupil
                        cv2.circle(image, eye_center, 5, (0, 0, 0), -1)
                        
                        # Add glow effect
                        cv2.circle(image, eye_center, 20, (255, 255, 255, 0.3), -1)
                        
                    # Draw open mouth
                    top_lip = landmarks[62]
                    bottom_lip = landmarks[66]
                    
                    # Draw curved mouth
                    points = np.array([
                        (top_lip[0], top_lip[1]),
                        (bottom_lip[0], bottom_lip[1] + 20)
                    ], np.int32)
                    
                    cv2.polylines(image, [points], False, (255, 0, 0), 2)
                    
                    # Add glow effect
                    cv2.circle(image, (bottom_lip[0], bottom_lip[1] + 20), 15, (255, 0, 0, 0.3), -1)
                    
            except Exception as e:
                logger.error(f"Error processing face: {str(e)}")
                continue
                
        # Convert processed image back to bytes
        _, buffer = cv2.imencode('.jpg', image)
        if buffer is None:
            raise ValueError("Failed to encode processed image")
            
        return buffer.tobytes()
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise

async def detect_faces(image_data: bytes, img_format: str = None) -> dict:
    """
    Detect faces and return facial landmarks
    
    Args:
        image_data: Raw image data
        img_format: Optional image format (jpeg, png, webp, etc.)
        
    Returns:
        Dictionary containing face detection results
    """
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_data, np.uint8)
        if nparr.size == 0:
            raise ValueError("Invalid image data")
            
        # Try different decoding methods based on format
        image = None
        if img_format:
            # Try specific format decoding
            if img_format in ['jpg', 'jpeg']:
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            elif img_format in ['png', 'webp', 'bmp']:
                image = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
            elif img_format in ['tiff', 'tif']:
                image = cv2.imdecode(nparr, cv2.IMREAD_ANYCOLOR)
            
        # If specific format decoding failed or not specified, try general decoding
        if image is None:
            # Try different flags in order of preference
            decode_flags = [
                cv2.IMREAD_COLOR,  # Try color first
                cv2.IMREAD_UNCHANGED,  # Try unchanged
                cv2.IMREAD_GRAYSCALE  # Try grayscale as last resort
            ]
            for flag in decode_flags:
                image = cv2.imdecode(nparr, flag)
                if image is not None:
                    break
                    
        if image is None:
            raise ValueError("Failed to decode image")
            
        # Handle different image types
        if len(image.shape) == 3:  # RGB/BGR image
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        elif len(image.shape) == 2:  # Grayscale image
            gray = image
        elif len(image.shape) == 4:  # RGBA image
            # Convert from RGBA to BGR
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            raise ValueError(f"Unsupported image format: {image.shape}")
            
        # Ensure image is 8-bit
        if gray.dtype != np.uint8:
            # Scale to 0-255 range
            gray = np.clip(gray, 0, 255)
            # Convert to uint8
            gray = gray.astype(np.uint8)
            
        # Ensure image has valid dimensions
        if gray.shape[0] == 0 or gray.shape[1] == 0:
            raise ValueError("Image has invalid dimensions")
            
        # Detect faces
        faces = face_detector(gray)
        results = []
        
        for face in faces:
            try:
                # Get face landmarks
                landmarks = shape_predictor(gray, face)
                
                # Extract key facial features
                left_eye = (landmarks.part(36).x, landmarks.part(36).y)
                right_eye = (landmarks.part(45).x, landmarks.part(45).y)
                nose = (landmarks.part(30).x, landmarks.part(30).y)
                mouth = (landmarks.part(48).x, landmarks.part(48).y)
                
                # Get all facial landmarks
                all_landmarks = [(p.x, p.y) for p in landmarks.parts()]
                
                # Add face detection result
                results.append({
                    "bounding_box": {
                        "left": face.left(),
                        "top": face.top(),
                        "width": face.width(),
                        "height": face.height()
                    },
                    "landmarks": {
                        "left_eye": left_eye,
                        "right_eye": right_eye,
                        "nose": nose,
                        "mouth": mouth,
                        "all_landmarks": all_landmarks
                    }
                })
                
            except Exception as e:
                print(f"Error processing face: {str(e)}")
                continue
                
        return {"faces": results}
        
    except Exception as e:
        print(f"Error detecting faces: {str(e)}")
        raise
