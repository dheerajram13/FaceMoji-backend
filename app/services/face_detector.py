# app/services/face_detector.py - Complete Implementation
import cv2
import dlib
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class FaceDetector:
    def __init__(self, model_path: str = "shape_predictor_68_face_landmarks.dat"):
        """Initialize face detector with dlib models"""
        self.detector = dlib.get_frontal_face_detector()
        try:
            self.predictor = dlib.shape_predictor(model_path)
        except Exception as e:
            logger.error(f"Failed to load face landmark model: {e}")
            raise
    
    def detect_faces(self, image_data: bytes) -> Dict:
        """
        Detect faces and analyze expressions
        
        Returns:
            Dict with faces, landmarks, expressions, and processing time
        """
        start_time = time.time()
        
        try:
            # Convert bytes to image
            image = self._bytes_to_image(image_data)
            if image is None:
                return {"error": "Invalid image data", "faces": []}
            
            # Convert to grayscale for detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.detector(gray)
            
            results = []
            for face in faces:
                # Get facial landmarks
                landmarks = self.predictor(gray, face)
                landmark_points = [(landmarks.part(i).x, landmarks.part(i).y) 
                                 for i in range(68)]
                
                # Analyze expression
                expression = self._analyze_expression(landmark_points)
                
                # Get face bounding box
                bbox = {
                    "x": face.left(),
                    "y": face.top(),
                    "width": face.width(),
                    "height": face.height()
                }
                
                results.append({
                    "bbox": bbox,
                    "landmarks": landmark_points,
                    "expression": expression,
                    "confidence": 0.95  # Placeholder confidence
                })
            
            processing_time = (time.time() - start_time) * 1000
            
            return {
                "faces": results,
                "processing_time_ms": round(processing_time, 2),
                "image_size": {"width": image.shape[1], "height": image.shape[0]}
            }
            
        except Exception as e:
            logger.error(f"Face detection error: {e}")
            return {"error": str(e), "faces": []}
    
    def _bytes_to_image(self, image_data: bytes) -> Optional[np.ndarray]:
        """Convert bytes to OpenCV image"""
        try:
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return image
        except Exception as e:
            logger.error(f"Image conversion error: {e}")
            return None
    
    def _analyze_expression(self, landmarks: List[Tuple[int, int]]) -> Dict:
        """
        Analyze facial expression from landmarks
        
        Basic expression detection based on facial geometry
        """
        try:
            # Key landmark indices (68-point model)
            left_eye = landmarks[36:42]
            right_eye = landmarks[42:48]
            mouth = landmarks[48:68]
            eyebrows = landmarks[17:27]
            
            # Calculate features
            mouth_height = self._calculate_mouth_openness(mouth)
            mouth_width = self._calculate_mouth_width(mouth)
            eye_openness = self._calculate_eye_openness(left_eye, right_eye)
            eyebrow_height = self._calculate_eyebrow_height(eyebrows, left_eye, right_eye)
            
            # Classify expression
            expression = self._classify_expression(
                mouth_height, mouth_width, eye_openness, eyebrow_height
            )
            
            return {
                "primary": expression["primary"],
                "confidence": expression["confidence"],
                "features": {
                    "mouth_openness": mouth_height,
                    "mouth_width": mouth_width,
                    "eye_openness": eye_openness,
                    "eyebrow_height": eyebrow_height
                }
            }
            
        except Exception as e:
            logger.error(f"Expression analysis error: {e}")
            return {"primary": "neutral", "confidence": 0.5}
    
    def _calculate_mouth_openness(self, mouth_points: List[Tuple[int, int]]) -> float:
        """Calculate how open the mouth is"""
        # Top and bottom lip center points
        top_lip = np.mean([mouth_points[13], mouth_points[14], mouth_points[15]], axis=0)
        bottom_lip = np.mean([mouth_points[19], mouth_points[18], mouth_points[17]], axis=0)
        
        # Mouth corners
        left_corner = mouth_points[0]
        right_corner = mouth_points[6]
        mouth_width = np.linalg.norm(np.array(right_corner) - np.array(left_corner))
        
        # Vertical distance between lips
        mouth_height = abs(top_lip[1] - bottom_lip[1])
        
        # Normalize by mouth width
        return mouth_height / max(mouth_width, 1)
    
    def _calculate_mouth_width(self, mouth_points: List[Tuple[int, int]]) -> float:
        """Calculate mouth width ratio"""
        left_corner = mouth_points[0]
        right_corner = mouth_points[6]
        return np.linalg.norm(np.array(right_corner) - np.array(left_corner))
    
    def _calculate_eye_openness(self, left_eye: List, right_eye: List) -> float:
        """Calculate average eye openness"""
        def eye_aspect_ratio(eye_points):
            # Vertical distances
            A = np.linalg.norm(np.array(eye_points[1]) - np.array(eye_points[5]))
            B = np.linalg.norm(np.array(eye_points[2]) - np.array(eye_points[4]))
            # Horizontal distance
            C = np.linalg.norm(np.array(eye_points[0]) - np.array(eye_points[3]))
            return (A + B) / (2.0 * C)
        
        left_ear = eye_aspect_ratio(left_eye)
        right_ear = eye_aspect_ratio(right_eye)
        return (left_ear + right_ear) / 2.0
    
    def _calculate_eyebrow_height(self, eyebrows: List, left_eye: List, right_eye: List) -> float:
        """Calculate eyebrow elevation"""
        # Average eyebrow height
        left_brow = np.mean([eyebrows[0], eyebrows[1], eyebrows[2]], axis=0)
        right_brow = np.mean([eyebrows[5], eyebrows[6], eyebrows[7]], axis=0)
        
        # Average eye height
        left_eye_avg = np.mean(left_eye, axis=0)
        right_eye_avg = np.mean(right_eye, axis=0)
        
        # Distance between eyebrows and eyes
        left_dist = abs(left_brow[1] - left_eye_avg[1])
        right_dist = abs(right_brow[1] - right_eye_avg[1])
        
        return (left_dist + right_dist) / 2.0
    
    def _classify_expression(self, mouth_height: float, mouth_width: float, 
                           eye_openness: float, eyebrow_height: float) -> Dict:
        """Classify expression based on facial features"""
        
        # Thresholds (these would be tuned with training data)
        mouth_open_threshold = 0.3
        mouth_wide_threshold = 60
        eye_open_threshold = 0.25
        eyebrow_raised_threshold = 20
        
        # Simple rule-based classification
        if mouth_height > mouth_open_threshold:
            if eye_openness > eye_open_threshold:
                return {"primary": "surprised", "confidence": 0.8}
            else:
                return {"primary": "laughing", "confidence": 0.7}
        
        elif mouth_width > mouth_wide_threshold:
            return {"primary": "happy", "confidence": 0.85}
        
        elif eyebrow_height > eyebrow_raised_threshold:
            if eye_openness < eye_open_threshold:
                return {"primary": "angry", "confidence": 0.7}
            else:
                return {"primary": "surprised", "confidence": 0.6}
        
        elif eye_openness < 0.2:
            return {"primary": "sleepy", "confidence": 0.6}
        
        else:
            return {"primary": "neutral", "confidence": 0.5}

# Global instance
face_detector = FaceDetector()