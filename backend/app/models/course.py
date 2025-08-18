"""
Course data models
"""

from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class TermEnum(str, Enum):
    FALL = "Fall"
    WINTER = "Winter" 
    SPRING = "Spring"

class Course(BaseModel):
    """Course model"""
    code: str
    title: str
    description: str
    credits: float
    prerequisites: Optional[str] = None
    corequisites: Optional[str] = None
    antirequisites: Optional[str] = None
    terms_offered: List[TermEnum] = []
    department: str
    level: int  # 100, 200, 300, 400
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "CS 135",
                "title": "Designing Functional Programs",
                "description": "An introduction to the fundamentals of computer science through the application of elementary programming patterns and the design of algorithms.",
                "credits": 0.5,
                "prerequisites": "None",
                "terms_offered": ["Fall", "Winter"],
                "department": "CS",
                "level": 100
            }
        }

class StudentProfile(BaseModel):
    """Student profile for recommendations"""
    program: str
    year: int
    completed_courses: List[str] = []
    current_courses: List[str] = []
    interests: List[str] = []
    preferred_terms: List[TermEnum] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "program": "Computer Engineering",
                "year": 2,
                "completed_courses": ["CS 135", "ECE 140"],
                "current_courses": ["ECE 240"],
                "interests": ["machine learning", "circuits"],
                "preferred_terms": ["Fall", "Winter"]
            }
        }

class Recommendation(BaseModel):
    """Course recommendation with reasoning"""
    course: Course
    confidence: float  # 0.0 to 1.0
    reasoning: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "course": {
                    "code": "STAT 230",
                    "title": "Probability",
                    "description": "Probability models for sample spaces...",
                    "credits": 0.5,
                    "department": "STAT",
                    "level": 200
                },
                "confidence": 0.85,
                "reasoning": "Essential foundation for machine learning, builds on your math background"
            }
        }