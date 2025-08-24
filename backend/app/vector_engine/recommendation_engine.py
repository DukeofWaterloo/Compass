"""
Advanced multi-dimensional recommendation engine
"""

import logging
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import random
from sqlalchemy.orm import Session
from app.models.database import Course, SessionLocal
from app.vector_engine.similarity_search import VectorSimilarityEngine, RecommendationContext, SimilarityResult

logger = logging.getLogger(__name__)

class RecommendationMode(Enum):
    """Different recommendation modes"""
    BASIC = "basic"
    ADVANCED = "advanced" 
    SUPER_ADVANCED = "super_advanced"

@dataclass
class AdvancedRecommendation:
    """Enhanced recommendation with multi-dimensional scoring"""
    course: Course
    overall_score: float
    similarity_score: float
    prerequisite_readiness: float
    academic_progression: float
    serendipity_factor: float
    department_diversity: float
    difficulty_appropriateness: float
    reasoning: str
    confidence: float
    recommendation_sources: List[str]

class MultiDimensionalRecommendationEngine:
    """Advanced recommendation engine with multiple scoring dimensions"""
    
    def __init__(self, embeddings_file: str = "course_embeddings.json"):
        self.similarity_engine = VectorSimilarityEngine(embeddings_file)
        
        # Scoring weights for different dimensions
        self.weights = {
            RecommendationMode.BASIC: {
                'similarity': 0.7,
                'prerequisite_readiness': 0.2,
                'academic_progression': 0.1,
                'serendipity': 0.0,
                'department_diversity': 0.0,
                'difficulty_appropriateness': 0.0
            },
            RecommendationMode.ADVANCED: {
                'similarity': 0.4,
                'prerequisite_readiness': 0.25,
                'academic_progression': 0.2,
                'serendipity': 0.05,
                'department_diversity': 0.05,
                'difficulty_appropriateness': 0.05
            },
            RecommendationMode.SUPER_ADVANCED: {
                'similarity': 0.3,
                'prerequisite_readiness': 0.2,
                'academic_progression': 0.2,
                'serendipity': 0.15,
                'department_diversity': 0.1,
                'difficulty_appropriateness': 0.05
            }
        }
    
    def generate_recommendations(
        self, 
        context: RecommendationContext, 
        mode: RecommendationMode = RecommendationMode.ADVANCED,
        top_k: int = 10
    ) -> List[AdvancedRecommendation]:
        """Generate multi-dimensional recommendations"""
        
        logger.info(f"Generating recommendations in {mode.value} mode for {context.program} student (Year {context.student_year})")
        
        # Get candidate courses from similarity engine
        candidates = self._get_candidate_courses(context, top_k * 3)  # Get more candidates for filtering
        
        if not candidates:
            logger.warning("No candidate courses found")
            return []
        
        # Score each candidate on multiple dimensions
        scored_recommendations = []
        
        for candidate in candidates:
            # Get full course info from database
            course = self._get_course_from_db(candidate.course_code)
            if not course:
                continue
            
            # Calculate multi-dimensional scores
            scores = self._calculate_multi_dimensional_scores(candidate, course, context, mode)
            
            if scores:
                recommendation = AdvancedRecommendation(
                    course=course,
                    overall_score=scores['overall_score'],
                    similarity_score=scores['similarity_score'],
                    prerequisite_readiness=scores['prerequisite_readiness'],
                    academic_progression=scores['academic_progression'],
                    serendipity_factor=scores['serendipity_factor'],
                    department_diversity=scores['department_diversity'],
                    difficulty_appropriateness=scores['difficulty_appropriateness'],
                    reasoning=scores['reasoning'],
                    confidence=scores['confidence'],
                    recommendation_sources=scores['sources']
                )
                scored_recommendations.append(recommendation)
        
        # Sort by overall score and return top recommendations
        scored_recommendations.sort(key=lambda x: x.overall_score, reverse=True)
        
        logger.info(f"Generated {len(scored_recommendations)} recommendations")
        
        return scored_recommendations[:top_k]
    
    def _get_candidate_courses(self, context: RecommendationContext, candidate_count: int) -> List[SimilarityResult]:
        """Get candidate courses using multiple strategies"""
        all_candidates = []
        seen_courses = set()
        
        # Strategy 1: Similarity to favorite courses (40% of candidates)
        if context.favorite_courses:
            favorite_candidates = self.similarity_engine.find_similar_to_multiple_courses(
                context.favorite_courses,
                top_k=int(candidate_count * 0.4)
            )
            for candidate in favorite_candidates:
                if candidate.course_code not in seen_courses:
                    all_candidates.append(candidate)
                    seen_courses.add(candidate.course_code)
        
        # Strategy 2: Interest-based text search (30% of candidates)
        if context.interests:
            interest_query = " ".join(context.interests)
            interest_candidates = self.similarity_engine.search_by_text_query(
                interest_query,
                top_k=int(candidate_count * 0.3)
            )
            for candidate in interest_candidates:
                if candidate.course_code not in seen_courses:
                    all_candidates.append(candidate)
                    seen_courses.add(candidate.course_code)
        
        # Strategy 3: Program-appropriate level courses (20% of candidates)
        level_candidates = self._get_level_appropriate_courses(context, int(candidate_count * 0.2))
        for candidate in level_candidates:
            if candidate.course_code not in seen_courses:
                all_candidates.append(candidate)
                seen_courses.add(candidate.course_code)
        
        # Strategy 4: Serendipity - random high-quality courses (10% of candidates)
        serendipity_candidates = self._get_serendipity_courses(context, int(candidate_count * 0.1))
        for candidate in serendipity_candidates:
            if candidate.course_code not in seen_courses:
                all_candidates.append(candidate)
                seen_courses.add(candidate.course_code)
        
        return all_candidates[:candidate_count]
    
    def _get_level_appropriate_courses(self, context: RecommendationContext, count: int) -> List[SimilarityResult]:
        """Get courses at appropriate academic level"""
        target_levels = [context.student_year * 100, (context.student_year + 1) * 100]
        
        candidates = []
        with SessionLocal() as db:
            # Query courses at target levels
            courses = db.query(Course).filter(
                Course.is_active == True,
                Course.level.in_(target_levels)
            ).limit(count * 2).all()
            
            for course in courses:
                # Create similarity result (with neutral similarity score)
                result = SimilarityResult(
                    course_code=course.code,
                    similarity_score=0.5,  # Neutral similarity
                    department=course.department,
                    level=course.level,
                    title=course.title,
                    metadata={}
                )
                candidates.append(result)
        
        return candidates[:count]
    
    def _get_serendipity_courses(self, context: RecommendationContext, count: int) -> List[SimilarityResult]:
        """Get random high-quality courses for serendipity"""
        candidates = []
        
        with SessionLocal() as db:
            # Get random sample of courses from different departments
            all_courses = db.query(Course).filter(Course.is_active == True).all()
            random_courses = random.sample(all_courses, min(count * 5, len(all_courses)))
            
            # Filter for quality courses (good description length, etc.)
            quality_courses = [
                course for course in random_courses 
                if course.description and len(course.description) > 50
            ]
            
            for course in quality_courses[:count]:
                result = SimilarityResult(
                    course_code=course.code,
                    similarity_score=0.3,  # Lower similarity for serendipity
                    department=course.department,
                    level=course.level,
                    title=course.title,
                    metadata={'serendipity': True}
                )
                candidates.append(result)
        
        return candidates
    
    def _calculate_multi_dimensional_scores(
        self, 
        candidate: SimilarityResult, 
        course: Course, 
        context: RecommendationContext,
        mode: RecommendationMode
    ) -> Optional[Dict]:
        """Calculate scores across all dimensions"""
        
        try:
            scores = {}
            sources = []
            
            # 1. Similarity Score (from vector similarity)
            scores['similarity_score'] = candidate.similarity_score
            if candidate.similarity_score > 0.7:
                sources.append("high_similarity")
            
            # 2. Prerequisite Readiness
            scores['prerequisite_readiness'] = self._calculate_prerequisite_readiness(course, context)
            
            # 3. Academic Progression
            scores['academic_progression'] = self._calculate_academic_progression(course, context)
            
            # 4. Serendipity Factor 
            scores['serendipity_factor'] = self._calculate_serendipity_factor(candidate, context)
            if scores['serendipity_factor'] > 0.5:
                sources.append("serendipity_discovery")
            
            # 5. Department Diversity
            scores['department_diversity'] = self._calculate_department_diversity(course, context)
            
            # 6. Difficulty Appropriateness
            scores['difficulty_appropriateness'] = self._calculate_difficulty_appropriateness(course, context)
            
            # Calculate overall weighted score
            weights = self.weights[mode]
            overall_score = (
                weights['similarity'] * scores['similarity_score'] +
                weights['prerequisite_readiness'] * scores['prerequisite_readiness'] +
                weights['academic_progression'] * scores['academic_progression'] +
                weights['serendipity'] * scores['serendipity_factor'] +
                weights['department_diversity'] * scores['department_diversity'] +
                weights['difficulty_appropriateness'] * scores['difficulty_appropriateness']
            )
            
            scores['overall_score'] = overall_score
            
            # Generate reasoning
            reasoning = self._generate_reasoning(scores, course, context, sources)
            scores['reasoning'] = reasoning
            
            # Calculate confidence based on score distribution
            score_variance = np.var([scores[key] for key in scores if key != 'overall_score'])
            confidence = min(0.95, 0.5 + (overall_score * 0.5) - (score_variance * 0.1))
            scores['confidence'] = max(0.1, confidence)
            
            scores['sources'] = sources
            
            return scores
            
        except Exception as e:
            logger.error(f"Failed to calculate scores for {course.code}: {e}")
            return None
    
    def _calculate_prerequisite_readiness(self, course: Course, context: RecommendationContext) -> float:
        """Calculate how ready the student is for this course's prerequisites"""
        if not course.prerequisites or course.prerequisites.lower() in ['none', 'n/a']:
            return 1.0  # No prerequisites = fully ready
        
        # Simple heuristic: if student has taken related courses, they're more ready
        # This would be enhanced with actual prerequisite parsing
        completed_courses = [c.upper() for c in context.favorite_courses]
        
        # Check if any completed courses are mentioned in prerequisites
        prereq_text = course.prerequisites.upper()
        matches = sum(1 for course_code in completed_courses if course_code in prereq_text)
        
        if matches > 0:
            return min(1.0, 0.7 + (matches * 0.15))  # Boost for having related courses
        
        # Base readiness based on academic level
        if course.level <= context.student_year * 100:
            return 0.8  # Level-appropriate course
        elif course.level <= (context.student_year + 1) * 100:
            return 0.6  # Slightly advanced
        else:
            return 0.3  # Too advanced
    
    def _calculate_academic_progression(self, course: Course, context: RecommendationContext) -> float:
        """Calculate how well this course fits academic progression"""
        target_level = context.student_year * 100
        course_year = course.level // 100
        
        if course_year == context.student_year:
            return 1.0  # Perfect level match
        elif course_year == context.student_year + 1:
            return 0.8  # Appropriate advancement
        elif course_year == context.student_year - 1:
            return 0.4  # Review/catch-up course
        elif course_year > context.student_year + 1:
            return 0.2  # Too advanced
        else:
            return 0.1  # Too basic
    
    def _calculate_serendipity_factor(self, candidate: SimilarityResult, context: RecommendationContext) -> float:
        """Calculate serendipity - discovering unexpected but valuable courses"""
        # High serendipity for courses outside student's typical pattern
        serendipity = 0.0
        
        # Bonus for different department than favorites
        if context.favorite_courses:
            favorite_depts = set()
            with SessionLocal() as db:
                for course_code in context.favorite_courses:
                    course = db.query(Course).filter(Course.code == course_code).first()
                    if course:
                        favorite_depts.add(course.department)
            
            if candidate.department not in favorite_depts:
                serendipity += 0.3
        
        # Bonus for courses marked as serendipity in metadata
        if candidate.metadata.get('serendipity'):
            serendipity += 0.5
        
        # Slight penalty for very high similarity (too predictable)
        if candidate.similarity_score > 0.9:
            serendipity = max(0, serendipity - 0.2)
        
        return min(1.0, serendipity)
    
    def _calculate_department_diversity(self, course: Course, context: RecommendationContext) -> float:
        """Calculate bonus for department diversity"""
        if not context.favorite_courses:
            return 0.5  # Neutral when no favorites
        
        # Get departments of favorite courses
        favorite_depts = set()
        with SessionLocal() as db:
            for course_code in context.favorite_courses:
                fav_course = db.query(Course).filter(Course.code == course_code).first()
                if fav_course:
                    favorite_depts.add(fav_course.department)
        
        # Bonus for exploring new departments
        if course.department not in favorite_depts:
            return 0.8
        else:
            return 0.3  # Lower score for same department
    
    def _calculate_difficulty_appropriateness(self, course: Course, context: RecommendationContext) -> float:
        """Calculate if course difficulty is appropriate for student"""
        base_score = 0.5
        
        # Adjust based on GPA if provided
        if context.gpa:
            if context.gpa >= 3.5:
                # High achiever - can handle challenging courses
                if course.level > context.student_year * 100:
                    base_score += 0.3
            elif context.gpa >= 3.0:
                # Average student - level-appropriate courses
                if course.level == context.student_year * 100:
                    base_score += 0.2
            else:
                # Lower GPA - might benefit from review or easier courses
                if course.level <= context.student_year * 100:
                    base_score += 0.2
        
        return min(1.0, base_score)
    
    def _generate_reasoning(self, scores: Dict, course: Course, context: RecommendationContext, sources: List[str]) -> str:
        """Generate human-readable reasoning for recommendation"""
        reasons = []
        
        # Similarity reasoning
        if scores['similarity_score'] > 0.7:
            reasons.append(f"highly similar to your favorite courses")
        elif scores['similarity_score'] > 0.5:
            reasons.append(f"relates well to your interests")
        
        # Academic progression
        if scores['academic_progression'] > 0.8:
            reasons.append(f"perfect for your current academic level")
        elif scores['academic_progression'] > 0.6:
            reasons.append(f"good next step in your academic progression")
        
        # Prerequisites
        if scores['prerequisite_readiness'] > 0.8:
            reasons.append(f"you appear ready for the prerequisites")
        elif scores['prerequisite_readiness'] < 0.5:
            reasons.append(f"might require additional preparation")
        
        # Serendipity
        if scores['serendipity_factor'] > 0.5:
            reasons.append(f"could introduce you to new areas of interest")
        
        # Department diversity
        if scores['department_diversity'] > 0.6:
            reasons.append(f"expands your knowledge beyond your main focus area")
        
        if not reasons:
            reasons.append("matches your academic profile")
        
        return f"Recommended because it {', '.join(reasons)}."
    
    def _get_course_from_db(self, course_code: str) -> Optional[Course]:
        """Get full course object from database"""
        try:
            with SessionLocal() as db:
                return db.query(Course).filter(
                    Course.code == course_code,
                    Course.is_active == True
                ).first()
        except Exception as e:
            logger.error(f"Failed to get course {course_code}: {e}")
            return None

def main():
    """Test the multi-dimensional recommendation engine"""
    engine = MultiDimensionalRecommendationEngine()
    
    # Test different recommendation modes
    context = RecommendationContext(
        student_year=2,
        favorite_courses=["CS135", "MATH135", "CS136"],
        interests=["algorithms", "software engineering", "databases"],
        program="Computer Science",
        gpa=3.7
    )
    
    for mode in RecommendationMode:
        print(f"\n🎯 Testing {mode.value.upper()} mode:")
        
        recommendations = engine.generate_recommendations(context, mode, top_k=5)
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec.course.code}: {rec.course.title}")
            print(f"   Overall Score: {rec.overall_score:.3f} (Confidence: {rec.confidence:.3f})")
            print(f"   Similarity: {rec.similarity_score:.3f} | Progression: {rec.academic_progression:.3f}")
            print(f"   Prerequisites: {rec.prerequisite_readiness:.3f} | Serendipity: {rec.serendipity_factor:.3f}")
            print(f"   Reasoning: {rec.reasoning}")

if __name__ == "__main__":
    main()