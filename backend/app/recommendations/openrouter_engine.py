"""
OpenRouter AI engine for course recommendations
"""

import os
import logging
import json
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from openai import OpenAI
from dotenv import load_dotenv

# Import prerequisite validation
from ..validation.prerequisite_validator import PrerequisiteValidator, ValidationResult

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class CourseInfo:
    """Simple course info for AI processing"""
    code: str
    title: str
    description: str
    credits: float
    prerequisites: Optional[str] = None
    department: str = ""
    level: int = 0

@dataclass
class StudentProfile:
    """Student profile for recommendations"""
    program: str
    year: int
    completed_courses: List[str] = None
    current_courses: List[str] = None
    interests: List[str] = None
    preferred_terms: List[str] = None

    def __post_init__(self):
        if self.completed_courses is None:
            self.completed_courses = []
        if self.current_courses is None:
            self.current_courses = []
        if self.interests is None:
            self.interests = []
        if self.preferred_terms is None:
            self.preferred_terms = []

@dataclass
class CourseRecommendation:
    """AI course recommendation"""
    course_code: str
    confidence: float
    reasoning: str
    prerequisite_status: str = "unknown"  # "satisfied", "missing", "unknown"
    missing_prereqs: List[str] = None
    difficulty_score: float = 0.0
    
    # UWFlow data
    uwflow_rating: Optional[float] = None
    uwflow_difficulty: Optional[float] = None
    uwflow_workload: Optional[float] = None
    uwflow_usefulness: Optional[float] = None
    uwflow_reviews: int = 0
    
    def __post_init__(self):
        if self.missing_prereqs is None:
            self.missing_prereqs = []

class OpenRouterAI:
    """OpenRouter AI client for course recommendations"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.model = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat-v3-0324:free")
        self.site_url = os.getenv("OPENROUTER_SITE_URL", "https://github.com/DukeofWaterloo/Compass")
        self.site_name = os.getenv("OPENROUTER_SITE_NAME", "Compass")
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
        
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )
        
        # Initialize prerequisite validator
        self.prereq_validator = PrerequisiteValidator()
        
        # Initialize UWFlow data manager
        try:
            from ..scraping.uwflow_data_manager import UWFlowDataManager
            self.uwflow_manager = UWFlowDataManager()
            logger.info("UWFlow data manager initialized")
        except Exception as e:
            self.uwflow_manager = None
            logger.warning(f"UWFlow data manager not available: {e}")
        
        logger.info(f"Initialized OpenRouter AI with model: {self.model}")
    
    def get_course_recommendations(
        self, 
        student_profile: StudentProfile, 
        available_courses: List[CourseInfo],
        max_recommendations: int = 5,
        include_courses_with_missing_prereqs: bool = False
    ) -> Tuple[List[CourseRecommendation], dict]:
        """Get AI-powered course recommendations with prerequisite validation"""
        
        start_time = time.time()
        
        # Step 1: Filter courses by prerequisites (if requested)
        eligible_courses = available_courses
        
        if not include_courses_with_missing_prereqs:
            eligible_courses = self._filter_courses_by_prerequisites(
                available_courses, 
                student_profile
            )
        
        # Step 2: Create the AI prompt
        prompt = self._create_recommendation_prompt(student_profile, eligible_courses, max_recommendations)
        
        try:
            # Step 3: Call OpenRouter API
            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": self.site_url,
                    "X-Title": self.site_name,
                },
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are Compass, an AI course recommendation system for University of Waterloo students. You provide personalized, helpful course recommendations with clear reasoning. Always respond with valid JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Step 4: Parse the response
            response_content = completion.choices[0].message.content
            recommendations = self._parse_ai_response(response_content)
            
            # Step 5: Enhance recommendations with prerequisite validation and UWFlow data
            enhanced_recommendations = self._enhance_recommendations_with_validation(
                recommendations,
                available_courses,
                student_profile
            )
            
            # Calculate stats
            processing_time = time.time() - start_time
            stats = {
                "processing_time_ms": int(processing_time * 1000),
                "model_used": self.model,
                "courses_considered": len(available_courses),
                "eligible_courses": len(eligible_courses),
                "recommendations_generated": len(enhanced_recommendations),
                "prereq_filtering_enabled": not include_courses_with_missing_prereqs
            }
            
            logger.info(f"Generated {len(enhanced_recommendations)} recommendations in {stats['processing_time_ms']}ms")
            
            return enhanced_recommendations, stats
            
        except Exception as e:
            logger.error(f"OpenRouter API call failed: {e}")
            # Return fallback recommendations
            fallback_recs = self._generate_fallback_recommendations(student_profile, eligible_courses, max_recommendations)
            enhanced_fallback = self._enhance_recommendations_with_validation(
                fallback_recs,
                available_courses, 
                student_profile
            )
            stats = {
                "processing_time_ms": int((time.time() - start_time) * 1000),
                "model_used": "fallback",
                "courses_considered": len(available_courses),
                "eligible_courses": len(eligible_courses),
                "recommendations_generated": len(enhanced_fallback),
                "prereq_filtering_enabled": not include_courses_with_missing_prereqs,
                "error": str(e)
            }
            return enhanced_fallback, stats
    
    def _create_recommendation_prompt(self, profile: StudentProfile, courses: List[CourseInfo], max_recs: int) -> str:
        """Create AI prompt for course recommendations"""
        
        # Limit courses to avoid token limits
        limited_courses = courses[:30]
        
        courses_json = []
        for course in limited_courses:
            courses_json.append({
                "code": course.code,
                "title": course.title,
                "description": course.description[:150] + "..." if len(course.description) > 150 else course.description,
                "credits": course.credits,
                "prerequisites": course.prerequisites,
                "department": course.department,
                "level": course.level
            })
        
        prompt = f"""
Recommend {max_recs} courses for this University of Waterloo student:

STUDENT PROFILE:
- Program: {profile.program}
- Year: {profile.year}
- Completed Courses: {', '.join(profile.completed_courses) if profile.completed_courses else 'None listed'}
- Current Courses: {', '.join(profile.current_courses) if profile.current_courses else 'None listed'}
- Interests: {', '.join(profile.interests) if profile.interests else 'Not specified'}
- Preferred Terms: {', '.join(profile.preferred_terms) if profile.preferred_terms else 'Any term'}

AVAILABLE COURSES:
{json.dumps(courses_json, indent=2)}

Please analyze the student's profile and recommend the best {max_recs} courses. Consider:
- Program requirements and year level appropriateness
- Prerequisites they've likely completed
- Their stated interests and career goals
- Course diversity and skill development
- Practical value and learning outcomes

Respond with ONLY a valid JSON array in this exact format:
[
  {{
    "course_code": "CS 240",
    "confidence": 0.85,
    "reasoning": "Excellent data structures course that builds on CS 135. Essential for software engineering and aligns with your Computer Engineering program."
  }},
  {{
    "course_code": "STAT 230", 
    "confidence": 0.78,
    "reasoning": "Strong foundation in probability for machine learning applications. Fits well with your technical interests."
  }}
]

Ensure confidence is between 0.0 and 1.0, and reasoning explains WHY this course is specifically good for THIS student.
"""
        
        return prompt
    
    def _parse_ai_response(self, response_content: str) -> List[CourseRecommendation]:
        """Parse AI response into CourseRecommendation objects"""
        try:
            # Try to extract JSON from response
            response_content = response_content.strip()
            
            # Look for JSON array in response
            import re
            json_match = re.search(r'\[.*\]', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                recommendations_data = json.loads(json_str)
                
                recommendations = []
                for item in recommendations_data:
                    if all(key in item for key in ["course_code", "confidence", "reasoning"]):
                        rec = CourseRecommendation(
                            course_code=item["course_code"],
                            confidence=float(item["confidence"]),
                            reasoning=item["reasoning"]
                        )
                        recommendations.append(rec)
                
                return recommendations
            else:
                logger.warning("No JSON array found in AI response")
                return []
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"Response content: {response_content}")
            return []
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return []
    
    def _filter_courses_by_prerequisites(self, courses: List[CourseInfo], student_profile: StudentProfile) -> List[CourseInfo]:
        """Filter courses by prerequisite requirements"""
        eligible_courses = []
        
        for course in courses:
            validation = self.prereq_validator.validate_prerequisites(
                course_prereqs=course.prerequisites or "",
                completed_courses=student_profile.completed_courses,
                student_year=student_profile.year,
                student_program=student_profile.program
            )
            
            if validation.is_satisfied:
                eligible_courses.append(course)
        
        logger.info(f"Filtered {len(courses)} courses to {len(eligible_courses)} eligible courses")
        return eligible_courses
    
    def _enhance_recommendations_with_validation(self, 
                                               recommendations: List[CourseRecommendation],
                                               all_courses: List[CourseInfo],
                                               student_profile: StudentProfile) -> List[CourseRecommendation]:
        """Enhance recommendations with prerequisite validation, difficulty scoring, and UWFlow data"""
        
        # Create course lookup
        course_lookup = {course.code: course for course in all_courses}
        
        # Get UWFlow data for all recommended courses
        course_codes = [rec.course_code for rec in recommendations]
        uwflow_data = {}
        
        if self.uwflow_manager:
            try:
                uwflow_data = self.uwflow_manager.get_multiple_uwflow_data(course_codes)
                logger.debug(f"Retrieved UWFlow data for {len(uwflow_data)}/{len(course_codes)} courses")
            except Exception as e:
                logger.warning(f"Failed to get UWFlow data: {e}")
        
        enhanced_recommendations = []
        
        for rec in recommendations:
            course = course_lookup.get(rec.course_code)
            if not course:
                # Keep recommendation but mark as unknown
                enhanced_recommendations.append(rec)
                continue
            
            # Validate prerequisites
            validation = self.prereq_validator.validate_prerequisites(
                course_prereqs=course.prerequisites or "",
                completed_courses=student_profile.completed_courses,
                student_year=student_profile.year,
                student_program=student_profile.program
            )
            
            # Calculate difficulty score
            difficulty_score = self.prereq_validator.get_course_difficulty_score(
                course.code, 
                course.prerequisites or ""
            )
            
            # Get UWFlow data for this course
            uwflow_course_data = uwflow_data.get(rec.course_code, {})
            
            # Create enhanced recommendation
            enhanced_rec = CourseRecommendation(
                course_code=rec.course_code,
                confidence=rec.confidence,
                reasoning=rec.reasoning,
                prerequisite_status="satisfied" if validation.is_satisfied else "missing",
                missing_prereqs=validation.missing_prereqs,
                difficulty_score=difficulty_score,
                # UWFlow data
                uwflow_rating=uwflow_course_data.get('rating'),
                uwflow_difficulty=uwflow_course_data.get('difficulty'),
                uwflow_workload=uwflow_course_data.get('workload'),
                uwflow_usefulness=uwflow_course_data.get('usefulness'),
                uwflow_reviews=uwflow_course_data.get('review_count', 0)
            )
            
            enhanced_recommendations.append(enhanced_rec)
        
        return enhanced_recommendations
    
    def _generate_fallback_recommendations(self, profile: StudentProfile, courses: List[CourseInfo], max_recs: int) -> List[CourseRecommendation]:
        """Generate simple rule-based recommendations as fallback"""
        recommendations = []
        
        # Simple scoring based on program and level
        for course in courses[:max_recs]:
            confidence = 0.6  # Base confidence for fallback
            
            # Boost confidence for program-related courses
            if profile.program.lower() in course.description.lower():
                confidence += 0.2
            
            # Boost for appropriate level
            expected_level = profile.year * 100
            if abs(course.level - expected_level) <= 100:
                confidence += 0.1
            
            # Boost for interests
            for interest in profile.interests:
                if interest.lower() in course.description.lower():
                    confidence += 0.1
                    break
            
            confidence = min(confidence, 1.0)  # Cap at 1.0
            
            reasoning = f"Recommended based on your {profile.program} program (Year {profile.year}). "
            if course.level == profile.year * 100:
                reasoning += f"Appropriate {course.level}-level course. "
            reasoning += f"This {course.department} course provides valuable skills for your academic progression."
            
            rec = CourseRecommendation(
                course_code=course.code,
                confidence=confidence,
                reasoning=reasoning
            )
            recommendations.append(rec)
        
        return recommendations

# Test function
def test_openrouter_ai():
    """Test OpenRouter AI engine"""
    print("🤖 Testing OpenRouter AI engine...")
    
    # Test courses
    test_courses = [
        CourseInfo(
            code="CS 240",
            title="Data Structures and Data Management",
            description="Introduction to widely used and effective methods of data organization, focusing on data structures, their algorithms, and the performance of these algorithms.",
            credits=0.5,
            prerequisites="CS 136",
            department="CS",
            level=200
        ),
        CourseInfo(
            code="STAT 230", 
            title="Probability",
            description="Probability models for sample spaces, events, conditional probability and independence. Random variables, distribution functions, expectation and variance.",
            credits=0.5,
            prerequisites="MATH 128 or 138",
            department="STAT",
            level=200
        ),
        CourseInfo(
            code="ECE 240",
            title="Electronic Circuits 1", 
            description="Introduction to electronic signal processing; second-order circuits; operational amplifier circuits; diode device and circuits.",
            credits=0.5,
            prerequisites="ECE 106, 140, MATH 119",
            department="ECE",
            level=200
        )
    ]
    
    # Test student
    test_student = StudentProfile(
        program="Computer Engineering",
        year=2,
        completed_courses=["CS 135", "ECE 140"],
        interests=["machine learning", "circuits"],
        preferred_terms=["Fall", "Winter"]
    )
    
    try:
        # Initialize AI engine
        ai = OpenRouterAI()
        
        # Get recommendations
        recommendations, stats = ai.get_course_recommendations(test_student, test_courses, max_recommendations=3)
        
        print(f"\n📊 Results:")
        print(f"  Model: {stats['model_used']}")
        print(f"  Processing time: {stats['processing_time_ms']}ms")
        print(f"  Courses considered: {stats['courses_considered']}")
        print(f"  Recommendations: {stats['recommendations_generated']}")
        
        print(f"\n🎯 Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec.course_code} (confidence: {rec.confidence:.2f})")
            print(f"     {rec.reasoning}")
            print()
        
        if "error" in stats:
            print(f"⚠️  Error occurred: {stats['error']}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_openrouter_ai()