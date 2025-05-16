import numpy as np
from typing import Dict, List, Tuple
from app.core.config import settings
import cv2
import dlib
import os
from PIL import Image
import base64
import io

class EmojiRecommender:
    def __init__(self):
        self.face_detector = dlib.get_frontal_face_detector()
        self.landmark_predictor = dlib.shape_predictor(
            settings.LANDMARK_PREDICTOR_PATH
        )
        self.expression_classifier = None  # Will be implemented later
        self.emoji_database = self._load_emoji_database()
        
    def _load_emoji_database(self) -> Dict:
        """Load emoji database with features"""
        # TODO: Implement actual database loading
        return {
            "happy": {
                "features": [0.8, 0.2, 0.1],
                "emojis": ["emoji_happy_001", "emoji_happy_002"]
            },
            "sad": {
                "features": [0.2, 0.8, 0.1],
                "emojis": ["emoji_sad_001", "emoji_sad_002"]
            },
            "surprised": {
                "features": [0.1, 0.1, 0.8],
                "emojis": ["emoji_surprised_001", "emoji_surprised_002"]
            }
        }

    def _extract_features(self, face_landmarks: Dict) -> List[float]:
        """Extract features from face landmarks"""
        # TODO: Implement actual feature extraction
        return [
            abs(face_landmarks['left_eye'][1] - face_landmarks['right_eye'][1]),
            abs(face_landmarks['mouth_center'][1] - face_landmarks['nose'][1]),
            abs(face_landmarks['left_eye'][0] - face_landmarks['right_eye'][0])
        ]

    def _calculate_similarity(self, features1: List[float], features2: List[float]) -> float:
        """Calculate similarity between two feature vectors"""
        return np.dot(features1, features2) / (np.linalg.norm(features1) * np.linalg.norm(features2))

    def recommend_emojis(self, image_data: bytes) -> Dict:
        """Recommend emojis based on face expression"""
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_detector(gray)
            
            if not faces:
                return {
                    "status": "error",
                    "message": "No faces detected"
                }
            
            # Process first face
            face = faces[0]
            landmarks = self._get_landmarks(gray, face)
            
            # Extract features
            features = self._extract_features(landmarks)
            
            # Find best matching emoji
            best_match = None
            best_similarity = 0
            
            for emotion, data in self.emoji_database.items():
                similarity = self._calculate_similarity(features, data['features'])
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = emotion
            
            return {
                "status": "success",
                "recommended_emoji_id": self.emoji_database[best_match]['emojis'][0],
                "alternative_emoji_ids": self.emoji_database[best_match]['emojis'][1:],
                "confidence": best_similarity,
                "expression": best_match
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error processing image: {str(e)}"
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

    def _get_point(self, shape: dlib.full_object_detection, index: int) -> List[int]:
        """Get coordinates of a specific landmark point"""
        point = shape.part(index)
        return [point.x, point.y]

# Initialize recommender
emoji_recommender = EmojiRecommender()
