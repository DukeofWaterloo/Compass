"""
Course data endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.models.course import Course

router = APIRouter(tags=["courses"])

# TODO: Replace with actual database/scraping
MOCK_COURSES = [
    Course(
        code="CS 135",
        title="Designing Functional Programs", 
        description="An introduction to the fundamentals of computer science through the application of elementary programming patterns and the design of algorithms.",
        credits=0.5,
        prerequisites="None",
        terms_offered=["Fall", "Winter"],
        department="CS",
        level=100
    ),
    Course(
        code="ECE 240",
        title="Electronic Circuits 1",
        description="Introduction to electronic signal processing; second-order circuits; operational amplifier circuits.",
        credits=0.5,
        prerequisites="ECE 106, 140, MATH 119",
        terms_offered=["Fall", "Winter"],
        department="ECE", 
        level=200
    )
]

@router.get("/courses", response_model=List[Course])
async def get_courses(
    department: Optional[str] = Query(None, description="Filter by department (e.g., CS, ECE)"),
    level: Optional[int] = Query(None, description="Filter by course level (100, 200, 300, 400)"),
    limit: int = Query(50, description="Maximum number of courses to return")
):
    """Get list of courses with optional filtering"""
    courses = MOCK_COURSES.copy()
    
    if department:
        courses = [c for c in courses if c.department.upper() == department.upper()]
    
    if level:
        courses = [c for c in courses if c.level == level]
    
    return courses[:limit]

@router.get("/courses/{course_code}", response_model=Course)
async def get_course(course_code: str):
    """Get specific course by code"""
    course = next((c for c in MOCK_COURSES if c.code == course_code), None)
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return course

@router.get("/departments")
async def get_departments():
    """Get list of available departments"""
    # TODO: Get from actual course data
    return {
        "departments": [
            {"code": "CS", "name": "Computer Science"},
            {"code": "ECE", "name": "Electrical and Computer Engineering"},
            {"code": "MATH", "name": "Mathematics"},
            {"code": "STAT", "name": "Statistics"},
            {"code": "PHYS", "name": "Physics"}
        ]
    }