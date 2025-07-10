import json
import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class EmojiRecommender:
    def __init__(self):
        """Initialize emoji recommender with expression mappings"""
        self.emoji_database = self._load_emoji_database()
        self.expression_mappings = self._create_expression_mappings()
    
    def _load_emoji_database(self) -> Dict:
        """Load emoji database with metadata"""
        # This would typically load from a database or JSON file
        return {
            "happy_001": {
                "id": "happy_001",
                "emoji": "😀",
                "expression": "happy",
                "confidence_threshold": 0.7,
                "url": "https://cdn.emojiswap.com/assets/happy_001.webp",
                "anchor_points": {
                    "left_eye": [80, 95],
                    "right_eye": [176, 95],
                    "mouth_center": [128, 180]
                }
            },
            "happy_002": {
                "id": "happy_002",
                "emoji": "😍",
                "expression": "happy",
                "confidence_threshold": 0.8,
                "url": "https://cdn.emojiswap.com/assets/happy_002.webp",
                "anchor_points": {
                    "left_eye": [80, 95],
                    "right_eye": [176, 95],
                    "mouth_center": [128, 180]
                }
            },
            "surprised_001": {
                "id": "surprised_001",
                "emoji": "😲",
                "expression": "surprised",
                "confidence_threshold": 0.6,
                "url": "https://cdn.emojiswap.com/assets/surprised_001.webp",
                "anchor_points": {
                    "left_eye": [80, 85],
                    "right_eye": [176, 85],
                    "mouth_center": [128, 190]
                }
            },
            "laughing_001": {
                "id": "laughing_001",
                "emoji": "🤣",
                "expression": "laughing",
                "confidence_threshold": 0.7,
                "url": "https://cdn.emojiswap.com/assets/laughing_001.webp",
                "anchor_points": {
                    "left_eye": [80, 90],
                    "right_eye": [176, 90],
                    "mouth_center": [128, 185]
                }
            },
            "angry_001": {
                "id": "angry_001",
                "emoji": "😠",
                "expression": "angry",
                "confidence_threshold": 0.6,
                "url": "https://cdn.emojiswap.com/assets/angry_001.webp",
                "anchor_points": {
                    "left_eye": [80, 100],
                    "right_eye": [176, 100],
                    "mouth_center": [128, 175]
                }
            },
            "neutral_001": {
                "id": "neutral_001",
                "emoji": "😐",
                "expression": "neutral",
                "confidence_threshold": 0.4,
                "url": "https://cdn.emojiswap.com/assets/neutral_001.webp",
                "anchor_points": {
                    "left_eye": [80, 95],
                    "right_eye": [176, 95],
                    "mouth_center": [128, 180]
                }
            },
            "sleepy_001": {
                "id": "sleepy_001",
                "emoji": "😴",
                "expression": "sleepy",
                "confidence_threshold": 0.5,
                "url": "https://cdn.emojiswap.com/assets/sleepy_001.webp",
                "anchor_points": {
                    "left_eye": [80, 98],
                    "right_eye": [176, 98],
                    "mouth_center": [128, 180]
                }
            }
        }
    
    def _create_expression_mappings(self) -> Dict:
        """Create mappings between expressions and emojis"""
        mappings = {}
        for emoji_id, emoji_data in self.emoji_database.items():
            expression = emoji_data["expression"]
            if expression not in mappings:
                mappings[expression] = []
            mappings[expression].append(emoji_id)
        return mappings
    
    def recommend_emoji(self, face_data: Dict) -> Dict:
        """
        Recommend emoji based on detected expression
        
        Args:
            face_data: Face detection results with expression analysis
            
        Returns:
            Recommendation with primary and alternative emojis
        """
        try:
            expression = face_data.get("expression", {})
            primary_expression = expression.get("primary", "neutral")
            confidence = expression.get("confidence", 0.5)
            
            # Get emoji candidates for this expression
            candidates = self.expression_mappings.get(primary_expression, [])
            
            if not candidates:
                # Fallback to neutral if no matches
                candidates = self.expression_mappings.get("neutral", ["neutral_001"])
            
            # Score and rank candidates
            scored_candidates = []
            for emoji_id in candidates:
                emoji_data = self.emoji_database[emoji_id]
                score = self._calculate_emoji_score(
                    expression, emoji_data, face_data
                )
                scored_candidates.append((emoji_id, score))
            
            # Sort by score (highest first)
            scored_candidates.sort(key=lambda x: x[1], reverse=True)
            
            # Get top recommendation
            primary_emoji_id = scored_candidates[0][0]
            primary_emoji = self.emoji_database[primary_emoji_id]
            
            # Get alternatives
            alternatives = [
                {
                    "id": emoji_id,
                    "emoji": self.emoji_database[emoji_id]["emoji"],
                    "score": score
                }
                for emoji_id, score in scored_candidates[1:4]  # Top 3 alternatives
            ]
            
            return {
                "primary": {
                    "id": primary_emoji_id,
                    "emoji": primary_emoji["emoji"],
                    "url": primary_emoji["url"],
                    "anchor_points": primary_emoji["anchor_points"],
                    "score": scored_candidates[0][1]
                },
                "alternatives": alternatives,
                "expression_matched": primary_expression,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Emoji recommendation error: {e}")
            # Return default neutral emoji
            return self._get_default_recommendation()
    
    def _calculate_emoji_score(self, expression: Dict, emoji_data: Dict, 
                             face_data: Dict) -> float:
        """Calculate compatibility score between expression and emoji"""
        base_score = expression.get("confidence", 0.5)
        
        # Boost score if confidence is above emoji threshold
        threshold = emoji_data.get("confidence_threshold", 0.5)
        if base_score >= threshold:
            base_score *= 1.2
        
        # Additional scoring factors could include:
        # - Face orientation compatibility
        # - Lighting conditions
        # - Previous user preferences
        
        return min(base_score, 1.0)  # Cap at 1.0
    
    def _get_default_recommendation(self) -> Dict:
        """Return default neutral emoji recommendation"""
        default_emoji = self.emoji_database["neutral_001"]
        return {
            "primary": {
                "id": "neutral_001",
                "emoji": default_emoji["emoji"],
                "url": default_emoji["url"],
                "anchor_points": default_emoji["anchor_points"],
                "score": 0.5
            },
            "alternatives": [],
            "expression_matched": "neutral",
            "confidence": 0.5
        }
    
    def get_all_emojis(self) -> List[Dict]:
        """Get all available emojis"""
        return [
            {
                "id": emoji_id,
                "emoji": emoji_data["emoji"],
                "expression": emoji_data["expression"],
                "url": emoji_data["url"]
            }
            for emoji_id, emoji_data in self.emoji_database.items()
        ]
    
    def get_emojis_by_expression(self, expression: str) -> List[Dict]:
        """Get emojis filtered by expression"""
        emoji_ids = self.expression_mappings.get(expression, [])
        return [
            {
                "id": emoji_id,
                "emoji": self.emoji_database[emoji_id]["emoji"],
                "url": self.emoji_database[emoji_id]["url"]
            }
            for emoji_id in emoji_ids
        ]

# Global instance
emoji_recommender = EmojiRecommender()