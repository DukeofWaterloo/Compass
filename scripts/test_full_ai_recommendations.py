#!/usr/bin/env python3
"""
Test AI recommendations with full course database
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.recommendations.openrouter_engine import OpenRouterAI, StudentProfile, CourseInfo
from app.scraping.data_manager import CourseDataManager
from app.models.database import SessionLocal

def test_full_ai_system():
    """Test AI recommendations with real course data"""
    print("🚀 Testing full AI recommendation system...")
    
    # Initialize components
    course_manager = CourseDataManager()
    ai_engine = OpenRouterAI()
    
    # Create test student profile
    test_student = StudentProfile(
        program="Computer Engineering",
        year=2,
        completed_courses=["CS 135", "ECE 140", "MATH 119"],
        current_courses=["ECE 240"],
        interests=["machine learning", "artificial intelligence", "data science"],
        preferred_terms=["Fall", "Winter"]
    )
    
    print(f"📋 Student Profile:")
    print(f"  Program: {test_student.program}")
    print(f"  Year: {test_student.year}")
    print(f"  Completed: {', '.join(test_student.completed_courses)}")
    print(f"  Current: {', '.join(test_student.current_courses)}")
    print(f"  Interests: {', '.join(test_student.interests)}")
    
    # Get relevant courses from database
    print(f"\n📚 Fetching relevant courses from database...")
    
    with SessionLocal() as db:
        # Get courses from relevant departments
        relevant_departments = ['CS', 'ECE', 'STAT', 'MATH', 'AMATH']
        all_courses = []
        
        for dept in relevant_departments:
            dept_courses = course_manager.get_courses_by_department(dept, db)
            # Filter for appropriate level (200-300 level for year 2)
            level_courses = [c for c in dept_courses if c.level in [200, 300]]
            # Exclude completed courses
            available_courses = [c for c in level_courses if c.code not in test_student.completed_courses + test_student.current_courses]
            all_courses.extend(available_courses)
            print(f"  {dept}: {len(available_courses)} available courses")
        
        print(f"  Total available: {len(all_courses)} courses")
        
        # Convert to CourseInfo format for AI
        course_infos = []
        for course in all_courses[:50]:  # Limit to avoid token limits
            course_info = CourseInfo(
                code=course.code,
                title=course.title,
                description=course.description,
                credits=course.credits,
                prerequisites=course.prerequisites,
                department=course.department,
                level=course.level
            )
            course_infos.append(course_info)
        
        print(f"\n🤖 Getting AI recommendations for {len(course_infos)} courses...")
        
        # Get AI recommendations
        recommendations, stats = ai_engine.get_course_recommendations(
            test_student, 
            course_infos, 
            max_recommendations=5
        )
        
        print(f"\n📊 AI Results:")
        print(f"  Model: {stats['model_used']}")
        print(f"  Processing time: {stats['processing_time_ms']}ms")
        print(f"  Courses analyzed: {stats['courses_considered']}")
        print(f"  Recommendations: {stats['recommendations_generated']}")
        
        print(f"\n🎯 AI Course Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            # Find full course details
            full_course = next((c for c in all_courses if c.code == rec.course_code), None)
            if full_course:
                print(f"\n  {i}. {rec.course_code}: {full_course.title}")
                print(f"     Credits: {full_course.credits} | Level: {full_course.level} | Dept: {full_course.department}")
                print(f"     Confidence: {rec.confidence:.2f}")
                print(f"     AI Reasoning: {rec.reasoning}")
                if full_course.prerequisites:
                    print(f"     Prerequisites: {full_course.prerequisites}")
            else:
                print(f"\n  {i}. {rec.course_code} (course details not found)")
                print(f"     Confidence: {rec.confidence:.2f}")
                print(f"     AI Reasoning: {rec.reasoning}")

def test_different_student_profiles():
    """Test with different student profiles"""
    print(f"\n🎭 Testing different student profiles...")
    
    profiles = [
        StudentProfile(
            program="Environmental Studies",
            year=3,
            completed_courses=["ENVS 200", "BIOL 150"],
            interests=["sustainability", "ecology", "environmental policy"],
            preferred_terms=["Fall"]
        ),
        StudentProfile(
            program="Business",
            year=1,
            completed_courses=["BET 100"],
            interests=["entrepreneurship", "marketing", "finance"],
            preferred_terms=["Winter", "Spring"]
        )
    ]
    
    ai_engine = OpenRouterAI()
    course_manager = CourseDataManager()
    
    for profile in profiles:
        print(f"\n👤 Profile: {profile.program} Year {profile.year}")
        print(f"   Interests: {', '.join(profile.interests)}")
        
        # Get sample courses for this profile
        with SessionLocal() as db:
            if "environmental" in profile.program.lower():
                depts = ['ENVS', 'BIOL', 'EARTH', 'GEOG']
            elif "business" in profile.program.lower():
                depts = ['BET', 'AFM', 'ECON', 'MGMT']
            else:
                depts = ['CS', 'MATH']
            
            sample_courses = []
            for dept in depts:
                dept_courses = course_manager.get_courses_by_department(dept, db)
                level_courses = [c for c in dept_courses if c.level <= (profile.year + 1) * 100]
                sample_courses.extend(level_courses[:5])  # 5 per dept
            
            if sample_courses:
                course_infos = [CourseInfo(
                    code=c.code, title=c.title, description=c.description,
                    credits=c.credits, prerequisites=c.prerequisites,
                    department=c.department, level=c.level
                ) for c in sample_courses[:15]]
                
                recs, _ = ai_engine.get_course_recommendations(profile, course_infos, max_recommendations=2)
                
                print(f"   🎯 Top recommendations:")
                for rec in recs:
                    print(f"     • {rec.course_code} (confidence: {rec.confidence:.2f})")

if __name__ == "__main__":
    test_full_ai_system()
    test_different_student_profiles()