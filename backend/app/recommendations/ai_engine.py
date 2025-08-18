"""
AI-powered recommendation engine using LangChain
"""

import os
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
import hashlib
import json

# Try to import LangChain components (may not be installed yet)
try:
    from langchain.schema import BaseMessage, HumanMessage, SystemMessage
    from langchain.callbacks.base import BaseCallbackHandler
    from langchain.schema.output_parser import StrOutputParser
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("LangChain not available - using mock implementation")

from app.models.course import StudentProfile, Course, Recommendation
from app.models.database import SessionLocal
from app.scraping.data_manager import CourseDataManager

logger = logging.getLogger(__name__)

@dataclass
class RecommendationRequest:
    """Request for course recommendations"""
    student_profile: StudentProfile
    max_recommendations: int = 5
    include_reasoning: bool = True
    filter_by_prerequisites: bool = True

@dataclass
class RecommendationResponse:
    """Response from recommendation engine"""
    recommendations: List[Recommendation]
    total_courses_considered: int
    processing_time_ms: int
    cache_hit: bool = False

class CompassCallbackHandler(BaseCallbackHandler):
    """Custom callback handler for LangChain"""
    
    def __init__(self):
        self.tokens_used = 0
        self.api_calls = 0
    
    def on_llm_start(self, serialized, prompts, **kwargs):
        self.api_calls += 1
        logger.debug(f"LLM call #{self.api_calls} started")
    
    def on_llm_end(self, response, **kwargs):
        # Estimate tokens (rough approximation)
        if hasattr(response, 'generations'):
            for gen_list in response.generations:
                for gen in gen_list:
                    self.tokens_used += len(gen.text.split()) * 1.3  # Rough token estimation
        logger.debug(f"LLM call completed. Estimated tokens: {self.tokens_used}")

class MockAIEngine:
    """Mock AI engine for when LangChain isn't available"""
    
    def __init__(self):
        self.course_manager = CourseDataManager()
    
    def generate_recommendations(self, request: RecommendationRequest) -> RecommendationResponse:
        """Generate mock recommendations based on simple rules"""
        import time
        start_time = time.time()
        
        profile = request.student_profile
        recommendations = []
        
        # Simple rule-based recommendations
        with SessionLocal() as db:
            # Get courses from related departments
            related_depts = self._get_related_departments(profile.program)
            all_courses = []
            
            for dept in related_depts[:3]:  # Limit to avoid too many
                courses = self.course_manager.get_courses_by_department(dept, db)
                all_courses.extend(courses[:10])  # Limit per department
            
            # Filter by level appropriate for student year
            appropriate_level = self._get_appropriate_level(profile.year)
            filtered_courses = [c for c in all_courses if c.level == appropriate_level]
            
            # Create mock recommendations
            for i, course in enumerate(filtered_courses[:request.max_recommendations]):
                recommendation = Recommendation(
                    course=course,
                    confidence=0.8 - (i * 0.1),  # Decreasing confidence
                    reasoning=f"Recommended for {profile.program} year {profile.year} students. "
                             f"This {course.level}-level {course.department} course aligns with your program."
                )
                recommendations.append(recommendation)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return RecommendationResponse(
            recommendations=recommendations,
            total_courses_considered=len(all_courses),
            processing_time_ms=processing_time,
            cache_hit=False
        )
    
    def _get_related_departments(self, program: str) -> List[str]:
        """Get departments related to a program"""
        program_lower = program.lower()
        
        dept_mappings = {
            'computer': ['CS', 'ECE', 'SE', 'MATH', 'STAT'],
            'electrical': ['ECE', 'PHYS', 'MATH', 'CS'],
            'engineering': ['ECE', 'ME', 'CIVE', 'CHE', 'SYDE'],
            'math': ['MATH', 'PMATH', 'AMATH', 'STAT', 'CS'],
            'business': ['AFM', 'BET', 'ENBUS', 'ECON', 'MGMT'],
            'arts': ['ENGL', 'HIST', 'PHIL', 'FINE', 'MUSIC'],
            'science': ['BIOL', 'CHEM', 'PHYS', 'EARTH', 'ENVS']
        }
        
        for keyword, depts in dept_mappings.items():
            if keyword in program_lower:
                return depts
        
        # Default recommendations
        return ['CS', 'MATH', 'ENGL', 'ENVS', 'BET']
    
    def _get_appropriate_level(self, year: int) -> int:
        """Get appropriate course level for student year"""
        level_mapping = {1: 100, 2: 200, 3: 300, 4: 400}
        return level_mapping.get(year, 200)

class LangChainAIEngine:
    """Real AI engine using LangChain"""
    
    def __init__(self, api_provider: str = "openai"):
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain is not available. Install with: pip install langchain")
        
        self.api_provider = api_provider
        self.course_manager = CourseDataManager()
        self.callback_handler = CompassCallbackHandler()
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the LLM based on provider"""
        if self.api_provider == "openai":
            try:
                from langchain_openai import ChatOpenAI
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY environment variable not set")
                
                return ChatOpenAI(
                    model="gpt-4",
                    temperature=0.7,
                    api_key=api_key,
                    callbacks=[self.callback_handler]
                )
            except ImportError:
                logger.error("OpenAI LangChain package not available")
                raise
        
        elif self.api_provider == "anthropic":
            try:
                from langchain_anthropic import ChatAnthropic
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY environment variable not set")
                
                return ChatAnthropic(
                    model="claude-3-sonnet-20240229",
                    temperature=0.7,
                    api_key=api_key,
                    callbacks=[self.callback_handler]
                )
            except ImportError:
                logger.error("Anthropic LangChain package not available")
                raise
        
        else:
            raise ValueError(f"Unsupported API provider: {self.api_provider}")
    
    def generate_recommendations(self, request: RecommendationRequest) -> RecommendationResponse:
        """Generate AI-powered course recommendations"""
        import time
        start_time = time.time()
        
        # Check cache first
        cache_key = self._generate_cache_key(request.student_profile)
        cached_result = self._get_cached_recommendations(cache_key)
        if cached_result:
            return cached_result
        
        # Get relevant courses from database
        relevant_courses = self._get_relevant_courses(request.student_profile)
        
        # Create prompt for AI
        prompt = self._create_recommendation_prompt(request.student_profile, relevant_courses)
        
        # Get AI recommendations
        try:
            messages = [
                SystemMessage(content="You are Compass, an AI course recommendation system for University of Waterloo students. You provide personalized, helpful course recommendations with clear reasoning."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            recommendations = self._parse_ai_response(response.content, relevant_courses)
            
        except Exception as e:
            logger.error(f"AI recommendation failed: {e}")
            # Fallback to mock recommendations
            mock_engine = MockAIEngine()
            return mock_engine.generate_recommendations(request)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        result = RecommendationResponse(
            recommendations=recommendations[:request.max_recommendations],
            total_courses_considered=len(relevant_courses),
            processing_time_ms=processing_time,
            cache_hit=False
        )
        
        # Cache the result
        self._cache_recommendations(cache_key, result)
        
        return result
    
    def _get_relevant_courses(self, profile: StudentProfile) -> List[Course]:
        """Get courses relevant to the student profile"""
        with SessionLocal() as db:
            # Get courses from related departments
            related_depts = MockAIEngine()._get_related_departments(profile.program)
            all_courses = []
            
            for dept in related_depts:
                courses = self.course_manager.get_courses_by_department(dept, db)
                all_courses.extend(courses)
            
            # Filter by appropriate level
            appropriate_levels = self._get_appropriate_levels(profile.year)
            filtered_courses = [c for c in all_courses if c.level in appropriate_levels]
            
            # Remove already completed courses
            if profile.completed_courses:
                filtered_courses = [c for c in filtered_courses if c.code not in profile.completed_courses]
            
            return filtered_courses[:50]  # Limit to avoid token limits
    
    def _get_appropriate_levels(self, year: int) -> List[int]:
        """Get appropriate course levels for student year"""
        level_mapping = {
            1: [100, 200],
            2: [200, 300],
            3: [300, 400],
            4: [300, 400]
        }
        return level_mapping.get(year, [200, 300])
    
    def _create_recommendation_prompt(self, profile: StudentProfile, courses: List[Course]) -> str:
        """Create prompt for AI recommendations"""
        course_list = "\n".join([
            f"- {course.code}: {course.title} ({course.credits} credits)\n"
            f"  Description: {course.description[:200]}...\n"
            f"  Prerequisites: {course.prerequisites or 'None'}\n"
            for course in courses[:20]  # Limit to avoid token limits
        ])
        
        return f"""
Please recommend 5 courses for this University of Waterloo student:

STUDENT PROFILE:
- Program: {profile.program}
- Year: {profile.year}
- Completed Courses: {', '.join(profile.completed_courses) if profile.completed_courses else 'None listed'}
- Current Courses: {', '.join(profile.current_courses) if profile.current_courses else 'None listed'}
- Interests: {', '.join(profile.interests) if profile.interests else 'Not specified'}
- Preferred Terms: {', '.join(profile.preferred_terms) if profile.preferred_terms else 'Any term'}

AVAILABLE COURSES:
{course_list}

Please provide exactly 5 course recommendations in this format:

RECOMMENDATION 1:
Course: [COURSE_CODE]
Confidence: [0.0-1.0]
Reasoning: [Why this course is recommended for this student]

RECOMMENDATION 2:
Course: [COURSE_CODE]
Confidence: [0.0-1.0]
Reasoning: [Why this course is recommended for this student]

[Continue for all 5 recommendations]

Consider:
- Student's program requirements and year level
- Prerequisites they've likely met
- Their stated interests
- Career relevance and skill development
- Course diversity and balance
"""
    
    def _parse_ai_response(self, response: str, available_courses: List[Course]) -> List[Recommendation]:
        """Parse AI response into Recommendation objects"""
        recommendations = []
        course_dict = {course.code: course for course in available_courses}
        
        # Simple parsing - look for RECOMMENDATION patterns
        import re
        pattern = r'RECOMMENDATION \d+:.*?Course: ([A-Z]+ \d+[A-Z]?).*?Confidence: ([\d.]+).*?Reasoning: ([^R]+?)(?=RECOMMENDATION|\Z)'
        matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
        
        for course_code, confidence_str, reasoning in matches:
            course_code = course_code.strip()
            if course_code in course_dict:
                try:
                    confidence = float(confidence_str)
                    recommendation = Recommendation(
                        course=course_dict[course_code],
                        confidence=min(max(confidence, 0.0), 1.0),  # Clamp to 0-1
                        reasoning=reasoning.strip()
                    )
                    recommendations.append(recommendation)
                except ValueError:
                    logger.warning(f"Invalid confidence value: {confidence_str}")
                    continue
        
        return recommendations
    
    def _generate_cache_key(self, profile: StudentProfile) -> str:
        """Generate cache key for student profile"""
        profile_str = f"{profile.program}|{profile.year}|{','.join(sorted(profile.completed_courses))}|{','.join(sorted(profile.interests))}"
        return hashlib.sha256(profile_str.encode()).hexdigest()
    
    def _get_cached_recommendations(self, cache_key: str) -> Optional[RecommendationResponse]:
        """Get cached recommendations"""
        # TODO: Implement caching with database
        return None
    
    def _cache_recommendations(self, cache_key: str, result: RecommendationResponse):
        """Cache recommendations"""
        # TODO: Implement caching with database
        pass

class RecommendationEngine:
    """Main recommendation engine - automatically chooses implementation"""
    
    def __init__(self, prefer_ai: bool = True):
        self.prefer_ai = prefer_ai
        self.engine = self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize the appropriate engine"""
        if self.prefer_ai and LANGCHAIN_AVAILABLE:
            # Try to use AI engine
            try:
                # Check for API keys
                if os.getenv("OPENAI_API_KEY"):
                    logger.info("Using OpenAI-powered recommendation engine")
                    return LangChainAIEngine("openai")
                elif os.getenv("ANTHROPIC_API_KEY"):
                    logger.info("Using Anthropic-powered recommendation engine") 
                    return LangChainAIEngine("anthropic")
                else:
                    logger.warning("No AI API keys found, using mock engine")
                    return MockAIEngine()
            except Exception as e:
                logger.error(f"Failed to initialize AI engine: {e}")
                return MockAIEngine()
        else:
            logger.info("Using mock recommendation engine")
            return MockAIEngine()
    
    def get_recommendations(self, request: RecommendationRequest) -> RecommendationResponse:
        """Get course recommendations"""
        return self.engine.generate_recommendations(request)

# Test function
def test_recommendation_engine():
    """Test the recommendation engine"""
    print("🤖 Testing recommendation engine...")
    
    # Create test student profile
    test_profile = StudentProfile(
        program="Computer Engineering",
        year=2,
        completed_courses=["CS 135", "ECE 140"],
        interests=["machine learning", "circuits"],
        preferred_terms=["Fall", "Winter"]
    )
    
    # Create recommendation request
    request = RecommendationRequest(
        student_profile=test_profile,
        max_recommendations=3
    )
    
    # Test engine
    engine = RecommendationEngine(prefer_ai=True)
    response = engine.get_recommendations(request)
    
    print(f"\n📊 Recommendation Results:")
    print(f"  Engine: {type(engine.engine).__name__}")
    print(f"  Courses considered: {response.total_courses_considered}")
    print(f"  Processing time: {response.processing_time_ms}ms")
    print(f"  Cache hit: {response.cache_hit}")
    
    print(f"\n🎯 Recommendations:")
    for i, rec in enumerate(response.recommendations, 1):
        print(f"  {i}. {rec.course.code}: {rec.course.title}")
        print(f"     Confidence: {rec.confidence:.2f}")
        print(f"     Reasoning: {rec.reasoning}")
        print()

if __name__ == "__main__":
    test_recommendation_engine()