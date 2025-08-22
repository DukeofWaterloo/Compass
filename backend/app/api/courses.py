"""
Course data endpoints
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import json

from app.models.course import Course as PydanticCourse
from app.models.database import Course as DBCourse, get_db

router = APIRouter(tags=["courses"])

def db_course_to_pydantic(db_course: DBCourse) -> PydanticCourse:
    """Convert database course to Pydantic model"""
    terms_offered = []
    if db_course.terms_offered:
        try:
            terms_offered = json.loads(db_course.terms_offered)
        except (json.JSONDecodeError, TypeError):
            terms_offered = []
    
    return PydanticCourse(
        code=db_course.code,
        title=db_course.title,
        description=db_course.description,
        credits=db_course.credits,
        prerequisites=db_course.prerequisites,
        corequisites=db_course.corequisites,
        antirequisites=db_course.antirequisites,
        terms_offered=terms_offered,
        department=db_course.department,
        level=db_course.level
    )

@router.get("/courses", response_model=List[PydanticCourse])
async def get_courses(
    department: Optional[str] = Query(None, description="Filter by department (e.g., CS, ECE)"),
    level: Optional[int] = Query(None, description="Filter by course level (100, 200, 300, 400)"),
    limit: int = Query(50, description="Maximum number of courses to return"),
    db: Session = Depends(get_db)
):
    """Get list of courses with optional filtering"""
    query = db.query(DBCourse).filter(DBCourse.is_active == True)
    
    if department:
        query = query.filter(DBCourse.department.ilike(f"{department}%"))
    
    if level:
        query = query.filter(DBCourse.level == level)
    
    db_courses = query.limit(limit).all()
    return [db_course_to_pydantic(course) for course in db_courses]

@router.get("/courses/{course_code}", response_model=PydanticCourse)
async def get_course(course_code: str, db: Session = Depends(get_db)):
    """Get specific course by code"""
    db_course = db.query(DBCourse).filter(
        and_(DBCourse.code == course_code, DBCourse.is_active == True)
    ).first()
    
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return db_course_to_pydantic(db_course)

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