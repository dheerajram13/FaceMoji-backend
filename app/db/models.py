from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    face_images = relationship("FaceImage", back_populates="user")


class FaceImage(Base):
    __tablename__ = "face_images"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_image_path = Column(String, nullable=False)
    processed_image_path = Column(String, nullable=True)
    emoji_type = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="face_images")
    face_detections = relationship("FaceDetection", back_populates="face_image")


class FaceDetection(Base):
    __tablename__ = "face_detections"

    id = Column(Integer, primary_key=True, index=True)
    face_image_id = Column(Integer, ForeignKey("face_images.id"), nullable=False)
    face_id = Column(String, nullable=False)  # Unique identifier for each detected face
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    face_image = relationship("FaceImage", back_populates="face_detections")
