import cv2
import dlib
import numpy as np
from celery import Celery
import os
from app.core.config import settings
from app.schemas.emoji import EmojiType
from typing import List, Tuple, Dict, Optional
from pydantic import BaseModel
import logging

# Initialize logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize Celery with Redis configuration
app = Celery(
    'facemoji_tasks',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0',
    include=['app.services.face_processor']
)

# Initialize dlib's face detector and shape predictor
face_detector = dlib.get_frontal_face_detector()
shape_predictor_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "shape_predictor_68_face_landmarks.dat")
shape_predictor = dlib.shape_predictor(shape_predictor_path)

vertical_offset: float = 0.0

@app.task
def process_face(image_data: bytes, emoji_config: Dict) -> bytes:
    """
    Process an image to apply face emoji effects
    
    Args:
        image_data: Raw image data
        emoji_config: Configuration for emoji processing
        
    Returns:
        Processed image data
    """
    try:
        # Initialize logger
        logger = logging.getLogger(__name__)
        
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
            
        # Get emoji configuration
        config = EmojiConfig(**emoji_config)
        emoji_type = config.emoji_type
        
        # Get emoji image
        emoji_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "emojis", f"{emoji_type}.png")
        if not os.path.exists(emoji_path):
            raise ValueError(f"Emoji type {emoji_type} not supported")
            
        emoji = cv2.imread(emoji_path, cv2.IMREAD_UNCHANGED)
        if emoji is None:
            raise ValueError(f"Failed to load emoji image: {emoji_type}")
            
        # Process each face
        for face in faces:
            try:
                # Get face landmarks
                landmarks = shape_predictor(gray, face)
                
                # Get face position and size
                face_x = face.left()
                face_y = face.top()
                face_w = face.width()
                face_h = face.height()
                
                # Calculate emoji position based on type and landmarks
                emoji_x, emoji_y = calculate_emoji_position(
                    emoji_type=emoji_type,
                    landmarks=landmarks,
                    face_x=face_x,
                    face_y=face_y,
                    face_w=face_w,
                    face_h=face_h
                )
                
                # Calculate emoji size
                emoji_size = int(face_w * config.size)
                
                # Resize emoji
                emoji_resized = cv2.resize(emoji, (emoji_size, emoji_size))
                
                # Apply offsets
                emoji_x = int(emoji_x + (face_w * config.horizontal_offset))
                emoji_y = int(emoji_y + (face_h * config.vertical_offset))
                
                # Calculate valid overlay region
                overlay_x1 = max(0, emoji_x)
                overlay_y1 = max(0, emoji_y)
                overlay_x2 = min(image.shape[1], emoji_x + emoji_size)
                overlay_y2 = min(image.shape[0], emoji_y + emoji_size)
                
                emoji_x1 = max(0, -emoji_x)
                emoji_y1 = max(0, -emoji_y)
                emoji_x2 = emoji_x1 + overlay_x2 - overlay_x1
                emoji_y2 = emoji_y1 + overlay_y2 - overlay_y1
                
                # Overlay emoji with alpha blending
                alpha = emoji_resized[emoji_y1:emoji_y2, emoji_x1:emoji_x2, 3] / 255.0 * config.opacity
                alpha = alpha[:,:,np.newaxis]
                
                image[overlay_y1:overlay_y2, overlay_x1:overlay_x2] = (
                    alpha * emoji_resized[emoji_y1:emoji_y2, emoji_x1:emoji_x2, :3] +
                    (1 - alpha) * image[overlay_y1:overlay_y2, overlay_x1:overlay_x2]
                ).astype(np.uint8)
                
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

def calculate_emoji_position(
    emoji_type: EmojiType,
    landmarks: dlib.full_object_detection,
    face_x: int,
    face_y: int,
    face_w: int,
    face_h: int
) -> Tuple[int, int]:
    """Calculate the appropriate position for the emoji based on face landmarks"""
    # Get key facial landmarks
    left_eye = (landmarks.part(36).x, landmarks.part(36).y)
    right_eye = (landmarks.part(45).x, landmarks.part(45).y)
    nose_tip = (landmarks.part(30).x, landmarks.part(30).y)
    bottom_lip = (landmarks.part(57).x, landmarks.part(57).y)
    
    # Calculate face center
    face_center_x = face_x + face_w//2
    face_center_y = face_y + face_h//2
    
    # Calculate eye center
    eye_center_x = (left_eye[0] + right_eye[0]) // 2
    eye_center_y = (left_eye[1] + right_eye[1]) // 2
    
    # Calculate eye distance for scaling
    eye_distance = abs(right_eye[0] - left_eye[0])
    
    # Calculate position based on emoji type
    if emoji_type in [EmojiType.CAT_EARS, EmojiType.DOG_EARS, EmojiType.HORNS]:
        # Position above the head
        return face_center_x - eye_distance//2, face_y - eye_distance
    
    elif emoji_type == EmojiType.CROWN:
        # Position above the head
        return face_center_x - eye_distance, face_y - eye_distance*1.5
        
    elif emoji_type == EmojiType.GLASSES:
        # Position between eyes
        return eye_center_x - eye_distance//2, eye_center_y - eye_distance//4
        
    elif emoji_type == EmojiType.MUSTACHE:
        # Position below nose
        return nose_tip[0] - eye_distance//2, nose_tip[1] + eye_distance//4
        
    elif emoji_type == EmojiType.BEARD:
        # Position below mouth
        return bottom_lip[0] - eye_distance, bottom_lip[1] + eye_distance//2
        
    elif emoji_type == EmojiType.HAT:
        # Position above head
        return face_center_x - eye_distance*1.5, face_y - eye_distance*2
        
    # Default position above head
    return face_center_x - eye_distance//2, face_y - eye_distance

async def detect_faces(image_data: bytes) -> dict:
    """
    Detect faces and return facial landmarks
    
    Args:
        image_data: Raw image data
        
    Returns:
        Dictionary containing face detection results
    """
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_data, np.uint8)
        if nparr.size == 0:
            raise ValueError("Invalid image data")
            
        # Try different decoding methods
        image = None
        decode_flags = [
            cv2.IMREAD_COLOR,      # Try color first
            cv2.IMREAD_UNCHANGED,  # Try unchanged
            cv2.IMREAD_GRAYSCALE   # Try grayscale as last resort
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
                logger.error(f"Error processing face: {str(e)}")
                continue
                
        return {"faces": results}
        
    except Exception as e:
        logger.error(f"Error detecting faces: {str(e)}")
        raise
