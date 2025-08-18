"""
Database models and configuration for Compass
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./compass.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

class Course(Base):
    """Course database model"""
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    credits = Column(Float, nullable=False)
    course_id = Column(String(10), index=True)  # UWaterloo course ID
    course_type = Column(String(20))  # LEC, LAB, PRJ, etc.
    prerequisites = Column(Text)
    corequisites = Column(Text)
    antirequisites = Column(Text)
    terms_offered = Column(String(100))  # JSON string of terms
    notes = Column(Text)
    department = Column(String(10), index=True, nullable=False)
    level = Column(Integer, index=True, nullable=False)
    url = Column(String(500))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<Course(code='{self.code}', title='{self.title}')>"

class RecommendationCache(Base):
    """Cache for AI recommendations to avoid repeated API calls"""
    __tablename__ = "recommendation_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    profile_hash = Column(String(64), index=True, nullable=False)  # Hash of student profile
    recommendations = Column(Text, nullable=False)  # JSON string of recommendations
    confidence_scores = Column(Text)  # JSON string of confidence scores
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<RecommendationCache(profile_hash='{self.profile_hash}')>"

class UserFeedback(Base):
    """User feedback on recommendations"""
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    course_code = Column(String(20), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    feedback_text = Column(Text)
    user_program = Column(String(100))
    user_year = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<UserFeedback(course_code='{self.course_code}', rating={self.rating})>"

# Database utility functions
def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database"""
    create_tables()
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()