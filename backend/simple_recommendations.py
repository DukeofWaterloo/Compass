#!/usr/bin/env python3
"""
Simple recommendations server for testing
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.dirname(__file__))

from app.models.database import get_db, Course
from app.models.course import StudentProfile
from uwaterloo_programs import is_valid_program, get_program_suggestions, UWATERLOO_PROGRAMS

app = FastAPI(title="Simple Recommendations API")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Simple Recommendations API is running! 🧭"}

@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "service": "simple-recommendations-api"}

@app.get("/api/v1/courses")
async def get_courses():
    db = next(get_db())
    try:
        courses = db.query(Course).limit(50).all()
        return [
            {
                "code": c.code,
                "title": c.title,
                "description": c.description,
                "credits": c.credits,
                "prerequisites": c.prerequisites,
                "corequisites": c.corequisites,
                "antirequisites": c.antirequisites,
                "terms_offered": c.terms_offered,
                "department": c.department,
                "level": c.level
            }
            for c in courses
        ]
    finally:
        db.close()

@app.get("/api/v1/programs")
async def get_programs():
    """Get all available programs"""
    return UWATERLOO_PROGRAMS

@app.get("/api/v1/programs/search")
async def search_programs(q: str = ""):
    """Search for programs"""
    return get_program_suggestions(q)

@app.post("/api/v1/recommendations")
async def get_simple_recommendations(profile: StudentProfile):
    """Get simple course recommendations"""
    # Validate program
    if not profile.program or not profile.program.strip():
        raise HTTPException(status_code=400, detail="Program is required")
    
    if not is_valid_program(profile.program):
        raise HTTPException(
            status_code=400, 
            detail=f"'{profile.program}' is not a valid University of Waterloo program. Please select from the available programs."
        )
    
    db = next(get_db())
    try:
        # Get all available courses
        all_courses = db.query(Course).all()
        
        # Get favorite courses for similarity matching (don't filter them out)
        favorite_codes = [c.upper().replace(" ", " ") for c in (profile.completed_courses or [])]
        available_courses = all_courses  # Include all courses, including favorites
        
        # Filter by appropriate course levels based on student year
        def is_appropriate_level(course_level: int, student_year: int) -> bool:
            if student_year == 1:
                return course_level >= 100 and course_level <= 200  # 1st years: 100-200 level
            elif student_year == 2:
                return course_level >= 200 and course_level <= 300  # 2nd years: 200-300 level  
            elif student_year == 3:
                return course_level >= 300 and course_level <= 400  # 3rd years: 300-400 level
            elif student_year >= 4:
                return course_level >= 400  # 4th+ years: 400+ level only
            else:
                return course_level >= 200  # Default fallback
        
        # Apply level filtering
        level_appropriate_courses = [
            c for c in available_courses 
            if is_appropriate_level(c.level, profile.year)
        ]
        
        # Simple scoring algorithm
        recommendations = []
        
        # If no level-appropriate courses, give helpful error
        if not level_appropriate_courses:
            return {
                "error": f"No courses found at appropriate level for year {profile.year} {profile.program} student",
                "suggestions": f"Year {profile.year} students typically take {400 if profile.year >= 4 else profile.year * 100}-level courses. Consider adding more courses to the database or adjusting your year level."
            }
        
        for course in level_appropriate_courses[:5]:  # Limit to 5 recommendations
            confidence_score = 0.7  # Base score
            reasoning_parts = []
            
            # Boost score for program relevance
            if profile.program.lower() in course.title.lower() or profile.program.lower() in course.description.lower():
                confidence_score += 0.2
                reasoning_parts.append(f"directly relevant to your program")
            
            # Boost score for interests
            for interest in (profile.interests or []):
                if interest.lower() in course.description.lower() or interest.lower() in course.title.lower():
                    confidence_score += 0.1
                    reasoning_parts.append(f"matches your interest in {interest}")
                    break
            
            # Boost score for similarity to favorite courses
            if favorite_codes:
                course_dept = course.code.split()[0] if ' ' in course.code else course.code[:2]
                for fav_code in favorite_codes:
                    fav_dept = fav_code.split()[0] if ' ' in fav_code else fav_code[:2]
                    if course_dept == fav_dept and course.code != fav_code:
                        confidence_score += 0.15
                        reasoning_parts.append(f"similar to {fav_code} which you enjoyed")
                        break
            
            # Boost for year-appropriate level (courses are already filtered by level)
            if profile.year >= 4 and course.level >= 400:
                confidence_score += 0.15
                reasoning_parts.append(f"advanced {course.level}-level course suitable for senior students")
            elif profile.year == 3 and course.level >= 300:
                confidence_score += 0.15  
                reasoning_parts.append(f"upper-year {course.level}-level course")
            elif profile.year == 2 and course.level >= 200:
                confidence_score += 0.15
                reasoning_parts.append(f"intermediate {course.level}-level course")
            elif profile.year == 1 and course.level <= 200:
                confidence_score += 0.15
                reasoning_parts.append(f"foundational {course.level}-level course")
                
            # Ensure confidence doesn't exceed 1.0
            confidence_score = min(confidence_score, 1.0)
            
            # Build reasoning text  
            year_descriptor = ["", "first", "second", "third", "fourth", "fifth"][min(profile.year, 5)]
            base_reasoning = f"Recommended for {year_descriptor}-year {profile.program} students. This {course.department} course is "
            if reasoning_parts:
                base_reasoning += ", ".join(reasoning_parts) + "."
            else:
                base_reasoning += f"relevant to your program."
            
            if course.prerequisites and course.prerequisites != "None":
                base_reasoning += f" Prerequisites: {course.prerequisites}."
            
            recommendation = {
                "course_code": course.code,
                "title": course.title,
                "description": course.description,
                "confidence_score": confidence_score,
                "reasoning": base_reasoning
            }
            
            recommendations.append(recommendation)
        
        # Sort by confidence score (highest first)
        recommendations.sort(key=lambda x: x["confidence_score"], reverse=True)
        
        return recommendations
        
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)