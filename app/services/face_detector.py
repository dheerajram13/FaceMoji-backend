import cv2
import dlib
import numpy as np
from typing import List, Dict, Tuple
import base64
import io
from PIL import Image
import time
from app.core.config import settings

class FaceDetector:
    def __init__(self):
        self.face_detector = dlib.get_frontal_face_detector()
        self.landmark_predictor = dlib.shape_predictor(
            settings.LANDMARK_PREDICTOR_PATH
        )
        self.expression_classifier = None  # Will be implemented later

    def detect_faces(self, image_data: bytes) -> List[Dict]:
        """Detect faces in the image"""
        start_time = time.time()
        
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_detector(gray)
        
        # Process each face
        results = []
        for face in faces:
            landmarks = self._get_landmarks(gray, face)
            expression = self._get_expression(gray, face)
            
            results.append({
                'landmarks': landmarks,
                'expression': expression,
                'bounding_box': self._get_bounding_box(face)
            })
        
        return {
            'faces': results,
            'processing_time_ms': int((time.time() - start_time) * 1000)
        }

    def _get_landmarks(self, gray: np.ndarray, face: dlib.rectangle) -> Dict:
        """Get facial landmarks for a face"""
        shape = self.landmark_predictor(gray, face)
        landmarks = {}
        
        # Extract specific landmarks
        landmarks['left_eye'] = self._get_point(shape, 36)
        landmarks['right_eye'] = self._get_point(shape, 45)
        landmarks['nose'] = self._get_point(shape, 30)
        landmarks['mouth_center'] = self._get_point(shape, 51)
        
        return landmarks

    def _get_expression(self, gray: np.ndarray, face: dlib.rectangle) -> Dict:
        """Get expression analysis for a face"""
        # TODO: Implement expression classifier
        return {
            'primary': 'neutral',
            'confidence': 0.8,
            'secondary': None,
            'secondary_confidence': None
        }

    def _get_bounding_box(self, face: dlib.rectangle) -> Dict:
        """Get bounding box coordinates"""
        return {
            'top': face.top(),
            'right': face.right(),
            'bottom': face.bottom(),
            'left': face.left()
        }

    def _get_point(self, shape: dlib.full_object_detection, index: int) -> List[int]:
        """Get coordinates of a specific landmark point"""
        point = shape.part(index)
        return [point.x, point.y]

# Initialize detector
face_detector = FaceDetector()
