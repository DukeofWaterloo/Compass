#!/usr/bin/env python3
"""
Test the complete UWFlow integration with recommendations
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.models.database import init_db
from app.recommendations.openrouter_engine import (
    OpenRouterAI, 
    CourseInfo, 
    StudentProfile
)

def test_uwflow_integration():
    """Test UWFlow integration with recommendation system"""
    print("🌟 Testing Complete UWFlow Integration...")
    
    # Initialize database
    print("📊 Initializing database...")
    init_db()
    
    # Create test courses
    test_courses = [
        CourseInfo(
            code="CS 135",
            title="Designing Functional Programs", 
            description="Introduction to computer science through functional programming",
            credits=0.5,
            prerequisites="None",
            department="CS",
            level=100
        ),
        CourseInfo(
            code="CS 136",
            title="Elementary Algorithm Design",
            description="Introduction to algorithm design and data abstraction",
            credits=0.5,
            prerequisites="CS 135",
            department="CS",
            level=100
        ),
        CourseInfo(
            code="CS 240",
            title="Data Structures and Data Management",
            description="Data structures, algorithms, and performance analysis",
            credits=0.5,
            prerequisites="CS 136 and (STAT 230 or STAT 240)",
            department="CS",
            level=200
        ),
        CourseInfo(
            code="STAT 230",
            title="Probability",
            description="Probability models, random variables, and distributions",
            credits=0.5,
            prerequisites="MATH 135",
            department="STAT",
            level=200
        ),
        CourseInfo(
            code="ENVS 200",
            title="Field Ecology",
            description="Introduction to field techniques in ecology",
            credits=0.5,
            prerequisites="2A standing",
            department="ENVS",
            level=200
        )
    ]
    
    # Create test student
    student = StudentProfile(
        program="Computer Science",
        year=2,
        completed_courses=["CS 135", "CS 136", "MATH 135"],
        interests=["algorithms", "data structures"],
        preferred_terms=["Fall", "Winter"]
    )
    
    print(f"Student profile: {student.program} (Year {student.year})")
    print(f"Completed courses: {student.completed_courses}")
    print(f"Interests: {student.interests}")
    
    try:
        # Initialize recommendation engine (this should load UWFlow manager)
        print(f"\n🤖 Initializing AI recommendation engine...")
        ai_engine = OpenRouterAI()
        
        # Check if UWFlow manager is available
        if ai_engine.uwflow_manager:
            print("✅ UWFlow data manager loaded successfully")
        else:
            print("⚠️  UWFlow data manager not available - will use fallback")
        
        # Get recommendations (this will be fallback since we don't have real API)
        print(f"\n🎯 Getting course recommendations...")
        
        recommendations, stats = ai_engine.get_course_recommendations(
            student, 
            test_courses, 
            max_recommendations=3,
            include_courses_with_missing_prereqs=False
        )
        
        print(f"\n📊 Recommendation Stats:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print(f"\n🎓 Recommendations for {student.program} student:")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec.course_code}")
            print(f"   Confidence: {rec.confidence:.2f}")
            print(f"   Prerequisites: {rec.prerequisite_status}")
            if rec.missing_prereqs:
                print(f"   Missing: {rec.missing_prereqs}")
            print(f"   Difficulty Score: {rec.difficulty_score:.2f}")
            
            # UWFlow data
            if rec.uwflow_rating:
                print(f"   UWFlow Rating: {rec.uwflow_rating:.1f}/5.0")
                print(f"   UWFlow Difficulty: {rec.uwflow_difficulty:.1f}/5.0")
                print(f"   UWFlow Workload: {rec.uwflow_workload:.1f}/5.0")
                print(f"   UWFlow Usefulness: {rec.uwflow_usefulness:.1f}/5.0")
                print(f"   UWFlow Reviews: {rec.uwflow_reviews}")
            else:
                print(f"   UWFlow Data: Not available")
            
            print(f"   Reasoning: {rec.reasoning}")
        
        # Test with including courses with missing prereqs
        print(f"\n🔓 Testing with courses that have missing prerequisites...")
        all_recommendations, all_stats = ai_engine.get_course_recommendations(
            student,
            test_courses,
            max_recommendations=3,
            include_courses_with_missing_prereqs=True
        )
        
        print(f"Including missing prereqs: {len(all_recommendations)} recommendations")
        
        for rec in all_recommendations:
            status_emoji = "✅" if rec.prerequisite_status == "satisfied" else "⚠️" 
            uwflow_info = f" (UWFlow: {rec.uwflow_rating:.1f}/5.0)" if rec.uwflow_rating else ""
            print(f"  {status_emoji} {rec.course_code}: {rec.confidence:.2f}{uwflow_info}")
        
        # Test UWFlow manager directly
        if ai_engine.uwflow_manager:
            print(f"\n📊 UWFlow Data Manager Stats:")
            uwflow_stats = ai_engine.uwflow_manager.get_uwflow_stats()
            for key, value in uwflow_stats.items():
                print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"❌ Error during integration test: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ UWFlow integration test completed!")

if __name__ == "__main__":
    test_uwflow_integration()