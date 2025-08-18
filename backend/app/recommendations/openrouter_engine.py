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
        
        logger.info(f"Initialized OpenRouter AI with model: {self.model}")
    
    def get_course_recommendations(
        self, 
        student_profile: StudentProfile, 
        available_courses: List[CourseInfo],
        max_recommendations: int = 5
    ) -> Tuple[List[CourseRecommendation], dict]:
        """Get AI-powered course recommendations"""
        
        start_time = time.time()
        
        # Create the AI prompt
        prompt = self._create_recommendation_prompt(student_profile, available_courses, max_recommendations)
        
        try:
            # Call OpenRouter API
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
            
            # Parse the response
            response_content = completion.choices[0].message.content
            recommendations = self._parse_ai_response(response_content)
            
            # Calculate stats
            processing_time = time.time() - start_time
            stats = {
                "processing_time_ms": int(processing_time * 1000),
                "model_used": self.model,
                "courses_considered": len(available_courses),
                "recommendations_generated": len(recommendations)
            }
            
            logger.info(f"Generated {len(recommendations)} recommendations in {stats['processing_time_ms']}ms")
            
            return recommendations, stats
            
        except Exception as e:
            logger.error(f"OpenRouter API call failed: {e}")
            # Return fallback recommendations
            fallback_recs = self._generate_fallback_recommendations(student_profile, available_courses, max_recommendations)
            stats = {
                "processing_time_ms": int((time.time() - start_time) * 1000),
                "model_used": "fallback",
                "courses_considered": len(available_courses),
                "recommendations_generated": len(fallback_recs),
                "error": str(e)
            }
            return fallback_recs, stats
    
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