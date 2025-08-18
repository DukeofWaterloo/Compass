"""
Course recommendation endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
import logging
import json

from app.models.course import StudentProfile, Recommendation, Course
from app.models.database import get_db
from app.recommendations.openrouter_engine import OpenRouterAI, CourseInfo
from app.scraping.data_manager import CourseDataManager

router = APIRouter(tags=["recommendations"])
logger = logging.getLogger(__name__)

# Initialize AI engine and course manager
try:
    ai_engine = OpenRouterAI()
    AI_AVAILABLE = True
    logger.info("AI recommendation engine initialized successfully")
except Exception as e:
    AI_AVAILABLE = False
    logger.warning(f"AI engine unavailable, using fallback: {e}")

course_manager = CourseDataManager()

@router.post("/recommendations", response_model=List[Recommendation])
async def get_recommendations(
    profile: StudentProfile, 
    include_missing_prereqs: bool = False,
    db: Session = Depends(get_db)
):
    """Get AI-powered course recommendations for a student with prerequisite validation"""
    
    try:
        # Get relevant courses from database
        relevant_courses = _get_relevant_courses_for_profile(profile, db)
        
        if not relevant_courses:
            raise HTTPException(status_code=404, detail="No relevant courses found for this profile")
        
        if AI_AVAILABLE:
            # Use AI engine with prerequisite validation
            recommendations = await _get_ai_recommendations(profile, relevant_courses, include_missing_prereqs)
        else:
            # Use fallback recommendations
            recommendations = _get_fallback_recommendations(profile, relevant_courses)
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")

@router.post("/recommendations/explain")
async def explain_recommendation(course_code: str, profile: StudentProfile, db: Session = Depends(get_db)):
    """Get detailed explanation for why a specific course is recommended"""
    
    try:
        # Find the course in database
        course = course_manager.get_course_by_code(course_code, db)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # Generate explanation
        if AI_AVAILABLE:
            explanation = await _get_ai_explanation(course, profile)
        else:
            explanation = _get_fallback_explanation(course, profile)
        
        return explanation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error explaining recommendation: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate explanation")

@router.post("/recommendations/validate-prerequisites")
async def validate_prerequisites(course_code: str, profile: StudentProfile, db: Session = Depends(get_db)):
    """Validate if a student meets prerequisites for a specific course"""
    
    try:
        # Find the course in database
        course = course_manager.get_course_by_code(course_code, db)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # Use the prerequisite validator
        from app.validation.prerequisite_validator import PrerequisiteValidator
        validator = PrerequisiteValidator()
        
        validation_result = validator.validate_prerequisites(
            course_prereqs=course.prerequisites or "",
            completed_courses=profile.completed_courses or [],
            student_year=profile.year,
            student_program=profile.program
        )
        
        difficulty_score = validator.get_course_difficulty_score(course_code, course.prerequisites or "")
        
        # Get prerequisite path if missing
        suggested_path = []
        if not validation_result.is_satisfied:
            suggested_path = validator.suggest_prerequisite_path(
                course_code,
                course.prerequisites or "",
                profile.completed_courses or [],
                []  # Would need all courses for full path analysis
            )
        
        return {
            "course_code": course_code,
            "course_title": course.title,
            "prerequisites": course.prerequisites,
            "is_eligible": validation_result.is_satisfied,
            "missing_prerequisites": validation_result.missing_prereqs,
            "warnings": validation_result.warnings,
            "difficulty_score": difficulty_score,
            "difficulty_label": "Easy" if difficulty_score < 0.3 else "Medium" if difficulty_score < 0.7 else "Hard",
            "suggested_prerequisite_path": suggested_path,
            "student_year": profile.year,
            "student_program": profile.program
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating prerequisites: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate prerequisites")

@router.get("/uwflow-data/{course_code}")
async def get_uwflow_data(course_code: str, db: Session = Depends(get_db)):
    """Get UWFlow rating and review data for a specific course"""
    
    try:
        from app.scraping.uwflow_data_manager import UWFlowDataManager
        uwflow_manager = UWFlowDataManager()
        
        uwflow_data = uwflow_manager.get_or_fetch_uwflow_data(course_code, db)
        
        if not uwflow_data:
            raise HTTPException(status_code=404, detail="UWFlow data not found for this course")
        
        return {
            "course_code": uwflow_data.course_code,
            "rating": uwflow_data.rating,
            "difficulty": uwflow_data.difficulty,
            "workload": uwflow_data.workload,
            "usefulness": uwflow_data.usefulness,
            "num_ratings": uwflow_data.num_ratings,
            "review_count": uwflow_data.review_count,
            "liked_percentage": uwflow_data.liked_percentage,
            "professor_ratings": json.loads(uwflow_data.professor_ratings) if uwflow_data.professor_ratings else [],
            "last_updated": uwflow_data.updated_at.isoformat() if uwflow_data.updated_at else None,
            "data_source": "uwflow_mock" if uwflow_data.rating else "uwflow_real"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting UWFlow data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get UWFlow data")

@router.get("/uwflow-stats")
async def get_uwflow_stats(db: Session = Depends(get_db)):
    """Get statistics about UWFlow data coverage"""
    
    try:
        from app.scraping.uwflow_data_manager import UWFlowDataManager
        uwflow_manager = UWFlowDataManager()
        
        stats = uwflow_manager.get_uwflow_stats(db)
        return stats
        
    except Exception as e:
        logger.error(f"Error getting UWFlow stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get UWFlow statistics")

def _get_relevant_courses_for_profile(profile: StudentProfile, db: Session) -> List[Course]:
    """Get courses relevant to student profile from database"""
    
    # Determine relevant departments based on program
    relevant_departments = _get_relevant_departments(profile.program)
    
    # Get appropriate course levels
    appropriate_levels = _get_appropriate_levels(profile.year)
    
    # Fetch courses from relevant departments
    all_courses = []
    for dept in relevant_departments:
        dept_courses = course_manager.get_courses_by_department(dept, db)
        # Filter by level
        level_filtered = [c for c in dept_courses if c.level in appropriate_levels]
        # Remove completed/current courses
        excluded_courses = (profile.completed_courses or []) + (profile.current_courses or [])
        available_courses = [c for c in level_filtered if c.code not in excluded_courses]
        all_courses.extend(available_courses)
    
    # Limit to reasonable number for AI processing
    return all_courses[:50]

def _get_relevant_departments(program: str) -> List[str]:
    """Get departments relevant to a program"""
    program_lower = program.lower()
    
    dept_mappings = {
        'computer': ['CS', 'ECE', 'SE', 'MATH', 'STAT', 'CO'],
        'electrical': ['ECE', 'PHYS', 'MATH', 'CS', 'SE'],
        'software': ['CS', 'SE', 'ECE', 'MATH', 'STAT'],
        'engineering': ['ECE', 'ME', 'CIVE', 'CHE', 'SYDE', 'MATH'],
        'math': ['MATH', 'PMATH', 'AMATH', 'STAT', 'CS', 'CO'],
        'business': ['AFM', 'BET', 'ENBUS', 'ECON', 'MGMT', 'HRM'],
        'arts': ['ENGL', 'HIST', 'PHIL', 'FINE', 'MUSIC', 'THPERF'],
        'science': ['BIOL', 'CHEM', 'PHYS', 'EARTH', 'ENVS', 'STAT'],
        'environmental': ['ENVS', 'EARTH', 'GEOG', 'BIOL', 'CHEM'],
        'economics': ['ECON', 'AFM', 'STAT', 'MATH', 'PSCI']
    }
    
    # Find matching departments
    for keyword, depts in dept_mappings.items():
        if keyword in program_lower:
            return depts[:8]  # Limit to avoid too many
    
    # Default fallback
    return ['CS', 'MATH', 'ENGL', 'ENVS', 'BET', 'ECON']

def _get_appropriate_levels(year: int) -> List[int]:
    """Get appropriate course levels for student year"""
    level_mapping = {
        1: [100, 200],
        2: [200, 300],
        3: [300, 400],
        4: [300, 400],
        5: [400]  # Graduate
    }
    return level_mapping.get(year, [200, 300])

async def _get_ai_recommendations(profile: StudentProfile, courses: List[Course], include_missing_prereqs: bool = False) -> List[Recommendation]:
    """Get AI-powered recommendations with prerequisite validation"""
    
    # Convert to CourseInfo format
    course_infos = [
        CourseInfo(
            code=c.code,
            title=c.title,
            description=c.description,
            credits=c.credits,
            prerequisites=c.prerequisites,
            department=c.department,
            level=c.level
        ) for c in courses
    ]
    
    # Get AI recommendations with prerequisite validation
    ai_recommendations, stats = ai_engine.get_course_recommendations(
        profile, 
        course_infos, 
        max_recommendations=5,
        include_courses_with_missing_prereqs=include_missing_prereqs
    )
    
    # Convert back to API format
    recommendations = []
    course_dict = {c.code: c for c in courses}
    
    for ai_rec in ai_recommendations:
        if ai_rec.course_code in course_dict:
            course = course_dict[ai_rec.course_code]
            
            # Enhanced reasoning that includes prerequisite info
            enhanced_reasoning = ai_rec.reasoning
            if ai_rec.prerequisite_status == "missing" and ai_rec.missing_prereqs:
                enhanced_reasoning += f" Note: Missing prerequisites: {', '.join(ai_rec.missing_prereqs)}"
            elif ai_rec.prerequisite_status == "satisfied":
                enhanced_reasoning += " ✅ Prerequisites satisfied"
            
            # Add difficulty info
            if ai_rec.difficulty_score > 0:
                difficulty_label = "Easy" if ai_rec.difficulty_score < 0.3 else "Medium" if ai_rec.difficulty_score < 0.7 else "Hard"
                enhanced_reasoning += f" (Difficulty: {difficulty_label})"
            
            # Add UWFlow data if available
            if ai_rec.uwflow_rating:
                enhanced_reasoning += f" | UWFlow: {ai_rec.uwflow_rating:.1f}/5.0"
                if ai_rec.uwflow_reviews > 0:
                    enhanced_reasoning += f" ({ai_rec.uwflow_reviews} reviews)"
            
            recommendation = Recommendation(
                course=course,
                confidence=ai_rec.confidence,
                reasoning=enhanced_reasoning
            )
            recommendations.append(recommendation)
    
    logger.info(f"Generated {len(recommendations)} AI recommendations in {stats['processing_time_ms']}ms")
    logger.info(f"Considered {stats['eligible_courses']}/{stats['courses_considered']} courses after prerequisite filtering")
    
    return recommendations

def _get_fallback_recommendations(profile: StudentProfile, courses: List[Course]) -> List[Recommendation]:
    """Generate fallback recommendations without AI"""
    
    recommendations = []
    
    # Simple scoring based on program alignment and level
    for course in courses[:5]:
        confidence = 0.6  # Base confidence
        
        # Boost for program relevance
        if profile.program.lower() in course.description.lower():
            confidence += 0.2
        
        # Boost for interests
        for interest in (profile.interests or []):
            if interest.lower() in course.description.lower():
                confidence += 0.1
                break
        
        # Boost for appropriate level
        expected_level = profile.year * 100
        if abs(course.level - expected_level) <= 100:
            confidence += 0.1
        
        confidence = min(confidence, 1.0)
        
        reasoning = f"Recommended for {profile.program} year {profile.year} students. "
        reasoning += f"This {course.level}-level {course.department} course provides valuable skills for your academic progression."
        
        recommendation = Recommendation(
            course=course,
            confidence=confidence,
            reasoning=reasoning
        )
        recommendations.append(recommendation)
    
    return recommendations

async def _get_ai_explanation(course: Course, profile: StudentProfile) -> dict:
    """Get AI explanation for a specific course recommendation"""
    
    # TODO: Implement detailed AI explanation
    return {
        "course_code": course.code,
        "explanation": f"This course aligns with your {profile.program} program and academic goals.",
        "fit_score": 0.85,
        "prerequisite_analysis": f"Prerequisites: {course.prerequisites or 'None'}",
        "career_relevance": "High relevance for your chosen field of study."
    }

def _get_fallback_explanation(course: Course, profile: StudentProfile) -> dict:
    """Generate fallback explanation without AI"""
    
    return {
        "course_code": course.code,
        "explanation": f"This course is recommended because it aligns with your {profile.program} program.",
        "fit_score": 0.75,
        "prerequisite_analysis": f"Prerequisites: {course.prerequisites or 'None'}",
        "career_relevance": "Relevant for your academic and career development."
    }