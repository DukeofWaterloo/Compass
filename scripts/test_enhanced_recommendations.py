#!/usr/bin/env python3
"""
Test the enhanced recommendation system with prerequisite validation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.recommendations.openrouter_engine import (
    OpenRouterAI, 
    CourseInfo, 
    StudentProfile,
    CourseRecommendation
)

def create_test_courses() -> list[CourseInfo]:
    """Create a set of test courses with various prerequisite patterns"""
    return [
        # First year courses
        CourseInfo(
            code="CS 135",
            title="Designing Functional Programs", 
            description="An introduction to the fundamentals of computer science through the application of elementary programming patterns.",
            credits=0.5,
            prerequisites="None",
            department="CS",
            level=100
        ),
        CourseInfo(
            code="MATH 135",
            title="Algebra for Honours Mathematics",
            description="An introduction to algebra designed for students in the Faculty of Mathematics.",
            credits=0.5,
            prerequisites="None", 
            department="MATH",
            level=100
        ),
        
        # Second year courses
        CourseInfo(
            code="CS 136",
            title="Elementary Algorithm Design and Data Abstraction",
            description="Introduction to algorithm design and implementation; data structures. ",
            credits=0.5,
            prerequisites="CS 135",
            department="CS", 
            level=100
        ),
        CourseInfo(
            code="CS 240",
            title="Data Structures and Data Management",
            description="Introduction to widely used and effective methods of data organization, focusing on data structures.",
            credits=0.5,
            prerequisites="CS 136 and (STAT 230 or STAT 240)",
            department="CS",
            level=200
        ),
        CourseInfo(
            code="STAT 230",
            title="Probability",
            description="Probability models for sample spaces, events, conditional probability and independence.",
            credits=0.5,
            prerequisites="MATH 135 or MATH 145",
            department="STAT",
            level=200
        ),
        
        # Third year courses
        CourseInfo(
            code="CS 341",
            title="Algorithms",
            description="Introduction to the design and analysis of algorithms.",
            credits=0.5,
            prerequisites="CS 240, CS 245; MATH 239",
            department="CS",
            level=300
        ),
        CourseInfo(
            code="CS 350",
            title="Operating Systems",
            description="An introduction to the fundamentals of operating system function, design, and implementation.",
            credits=0.5,
            prerequisites="CS 240, CS 241; STAT 230 or equivalent",
            department="CS",
            level=300
        ),
        
        # Advanced courses with complex prerequisites
        CourseInfo(
            code="CS 444",
            title="Compiler Construction",
            description="An introduction to compiler construction with particular emphasis on syntactic and semantic analysis.",
            credits=0.5,
            prerequisites="CS 350 and CS 341",
            department="CS",
            level=400
        ),
        
        # Non-CS courses
        CourseInfo(
            code="ENVS 200",
            title="Field Ecology",
            description="Introduction to field techniques in ecology, including bird watching and nature observation.",
            credits=0.5,
            prerequisites="2A standing",
            department="ENVS",
            level=200
        ),
        CourseInfo(
            code="BET 300", 
            title="Entrepreneurship and Innovation",
            description="Introduction to entrepreneurship, business development, and innovation management.",
            credits=0.5,
            prerequisites="Level at least 3A",
            department="BET",
            level=300
        )
    ]

def create_test_students() -> list[StudentProfile]:
    """Create various test student profiles"""
    return [
        # First year CS student
        StudentProfile(
            program="Computer Science",
            year=1,
            completed_courses=[],
            current_courses=["CS 135", "MATH 135"],
            interests=["programming", "algorithms"],
            preferred_terms=["Fall", "Winter"]
        ),
        
        # Second year CS student with some courses completed
        StudentProfile(
            program="Computer Science", 
            year=2,
            completed_courses=["CS 135", "CS 136", "MATH 135", "STAT 230"],
            current_courses=["CS 240"],
            interests=["data structures", "machine learning"],
            preferred_terms=["Fall", "Winter"]
        ),
        
        # Third year student ready for advanced courses
        StudentProfile(
            program="Computer Science",
            year=3, 
            completed_courses=["CS 135", "CS 136", "CS 240", "CS 245", "MATH 135", "MATH 239", "STAT 230"],
            current_courses=["CS 341"],
            interests=["systems programming", "compilers"],
            preferred_terms=["Fall"]
        ),
        
        # Diverse student interested in interdisciplinary courses
        StudentProfile(
            program="Environmental Studies",
            year=2,
            completed_courses=["ENVS 100", "BIOL 110"],
            current_courses=["ENVS 200"],
            interests=["ecology", "sustainability", "field work"],
            preferred_terms=["Spring", "Fall"]
        )
    ]

def test_prerequisite_filtering():
    """Test prerequisite filtering functionality"""
    print("🔍 Testing prerequisite filtering...")
    
    courses = create_test_courses()
    student = StudentProfile(
        program="Computer Science",
        year=2,
        completed_courses=["CS 135", "CS 136", "MATH 135"],
        interests=["algorithms"]
    )
    
    try:
        ai = OpenRouterAI()
        
        # Test filtering
        eligible_courses = ai._filter_courses_by_prerequisites(courses, student)
        
        print(f"\nStudent completed: {student.completed_courses}")
        print(f"Total courses available: {len(courses)}")
        print(f"Eligible courses after filtering: {len(eligible_courses)}")
        
        print("\nEligible courses:")
        for course in eligible_courses:
            print(f"  ✅ {course.code}: {course.title}")
            print(f"     Prerequisites: {course.prerequisites}")
        
        print("\nIneligible courses:")
        ineligible = [c for c in courses if c not in eligible_courses]
        for course in ineligible:
            print(f"  ❌ {course.code}: {course.title}")
            print(f"     Prerequisites: {course.prerequisites}")
            
    except Exception as e:
        print(f"❌ Error in prerequisite filtering test: {e}")

def test_enhanced_recommendations():
    """Test enhanced recommendations with validation"""
    print("\n🎯 Testing enhanced recommendations...")
    
    courses = create_test_courses()
    students = create_test_students()
    
    try:
        ai = OpenRouterAI()
        
        for i, student in enumerate(students, 1):
            print(f"\n--- Student {i}: {student.program} (Year {student.year}) ---")
            print(f"Completed: {student.completed_courses}")
            print(f"Interests: {student.interests}")
            
            # Test with prerequisite filtering enabled
            print(f"\n📚 Recommendations (with prerequisite filtering):")
            recs_filtered, stats_filtered = ai.get_course_recommendations(
                student, 
                courses, 
                max_recommendations=3,
                include_courses_with_missing_prereqs=False
            )
            
            print(f"Stats: {stats_filtered['eligible_courses']}/{stats_filtered['courses_considered']} eligible courses")
            
            for j, rec in enumerate(recs_filtered, 1):
                print(f"{j}. {rec.course_code} (confidence: {rec.confidence:.2f}, difficulty: {rec.difficulty_score:.2f})")
                print(f"   Prerequisites: {rec.prerequisite_status}")
                if rec.missing_prereqs:
                    print(f"   Missing: {rec.missing_prereqs}")
                print(f"   Reasoning: {rec.reasoning}")
                print()
            
            # Test without prerequisite filtering
            print(f"📚 Recommendations (including courses with missing prereqs):")
            recs_all, stats_all = ai.get_course_recommendations(
                student,
                courses,
                max_recommendations=3, 
                include_courses_with_missing_prereqs=True
            )
            
            for j, rec in enumerate(recs_all, 1):
                status_emoji = "✅" if rec.prerequisite_status == "satisfied" else "⚠️"
                print(f"{j}. {status_emoji} {rec.course_code} (confidence: {rec.confidence:.2f})")
                if rec.prerequisite_status == "missing":
                    print(f"   Missing prereqs: {rec.missing_prereqs}")
                print()
                
    except Exception as e:
        print(f"❌ Error in enhanced recommendations test: {e}")

def test_difficulty_scoring():
    """Test difficulty scoring integration"""
    print("\n📊 Testing difficulty scoring integration...")
    
    courses = create_test_courses()
    
    try:
        ai = OpenRouterAI()
        
        print("Course difficulty scores:")
        for course in courses:
            difficulty = ai.prereq_validator.get_course_difficulty_score(course.code, course.prerequisites or "")
            difficulty_label = "Easy" if difficulty < 0.3 else "Medium" if difficulty < 0.7 else "Hard"
            
            print(f"  {course.code}: {difficulty:.2f} ({difficulty_label})")
            print(f"    Prerequisites: {course.prerequisites or 'None'}")
            print()
            
    except Exception as e:
        print(f"❌ Error in difficulty scoring test: {e}")

def test_recommendation_enhancement():
    """Test the recommendation enhancement process"""
    print("\n✨ Testing recommendation enhancement...")
    
    # Create some basic recommendations to enhance
    basic_recommendations = [
        CourseRecommendation(
            course_code="CS 240",
            confidence=0.85,
            reasoning="Great data structures course"
        ),
        CourseRecommendation(
            course_code="CS 444", 
            confidence=0.75,
            reasoning="Advanced compiler construction"
        )
    ]
    
    courses = create_test_courses()
    student = StudentProfile(
        program="Computer Science",
        year=2,
        completed_courses=["CS 135", "CS 136", "MATH 135", "STAT 230"],
        interests=["algorithms"]
    )
    
    try:
        ai = OpenRouterAI()
        
        enhanced = ai._enhance_recommendations_with_validation(
            basic_recommendations,
            courses,
            student
        )
        
        print("Enhancement results:")
        for rec in enhanced:
            print(f"\n{rec.course_code}:")
            print(f"  Confidence: {rec.confidence:.2f}")
            print(f"  Prerequisite status: {rec.prerequisite_status}")
            print(f"  Missing prereqs: {rec.missing_prereqs}")
            print(f"  Difficulty: {rec.difficulty_score:.2f}")
            print(f"  Reasoning: {rec.reasoning}")
            
    except Exception as e:
        print(f"❌ Error in recommendation enhancement test: {e}")

if __name__ == "__main__":
    print("🧪 Testing enhanced recommendation system with prerequisite validation...")
    
    test_prerequisite_filtering()
    test_enhanced_recommendations()
    test_difficulty_scoring()
    test_recommendation_enhancement()
    
    print("\n✅ All tests completed!")