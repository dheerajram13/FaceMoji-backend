from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.face import Base
from app.core.config import settings

# Create database engine
engine = create_engine(settings.DATABASE_URL)

# Create all tables
Base.metadata.create_all(bind=engine)

print("Database initialized successfully!")
