#!/usr/bin/env python3
"""
Test prerequisite validation integration without AI calls
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.recommendations.openrouter_engine import (
    CourseInfo, 
    StudentProfile,
    CourseRecommendation
)
from app.validation.prerequisite_validator import PrerequisiteValidator

def test_prerequisite_integration():
    """Test prerequisite validation integration"""
    print("🔗 Testing prerequisite validation integration...")
    
    # Create test courses
    courses = [
        CourseInfo(
            code="CS 135",
            title="Designing Functional Programs",
            description="Intro to CS",
            credits=0.5,
            prerequisites="None",
            department="CS",
            level=100
        ),
        CourseInfo(
            code="CS 136", 
            title="Elementary Algorithm Design",
            description="Algorithm design",
            credits=0.5,
            prerequisites="CS 135",
            department="CS",
            level=100
        ),
        CourseInfo(
            code="CS 240",
            title="Data Structures",
            description="Data structures course",
            credits=0.5,
            prerequisites="CS 136 and (STAT 230 or STAT 240)",
            department="CS",
            level=200
        ),
        CourseInfo(
            code="STAT 230",
            title="Probability",
            description="Probability course",
            credits=0.5,
            prerequisites="MATH 135",
            department="STAT",
            level=200
        )
    ]
    
    # Test student
    student = StudentProfile(
        program="Computer Science",
        year=2,
        completed_courses=["CS 135", "CS 136", "MATH 135"],
        interests=["algorithms"]
    )
    
    validator = PrerequisiteValidator()
    
    print(f"Student completed: {student.completed_courses}")
    print("\nCourse eligibility:")
    
    for course in courses:
        validation = validator.validate_prerequisites(
            course_prereqs=course.prerequisites or "",
            completed_courses=student.completed_courses,
            student_year=student.year,
            student_program=student.program
        )
        
        difficulty = validator.get_course_difficulty_score(course.code, course.prerequisites or "")
        
        status = "✅ ELIGIBLE" if validation.is_satisfied else "❌ NOT ELIGIBLE"
        print(f"\n{course.code}: {status}")
        print(f"  Prerequisites: {course.prerequisites}")
        print(f"  Difficulty: {difficulty:.2f}")
        
        if not validation.is_satisfied:
            print(f"  Missing: {validation.missing_prereqs}")
        if validation.warnings:
            print(f"  Warnings: {validation.warnings}")

def test_filtering_logic():
    """Test the filtering logic without AI"""
    print("\n🗂️  Testing course filtering logic...")
    
    # Mock the filtering method
    class MockAI:
        def __init__(self):
            self.prereq_validator = PrerequisiteValidator()
        
        def filter_courses_by_prerequisites(self, courses, student_profile):
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
            
            return eligible_courses
    
    # Test data
    courses = [
        CourseInfo("CS 135", "Intro", "desc", 0.5, "None", "CS", 100),
        CourseInfo("CS 136", "Algorithms", "desc", 0.5, "CS 135", "CS", 100),
        CourseInfo("CS 240", "Data Structures", "desc", 0.5, "CS 136", "CS", 200),
        CourseInfo("CS 341", "Advanced Algorithms", "desc", 0.5, "CS 240, CS 245", "CS", 300),
    ]
    
    student = StudentProfile(
        program="Computer Science",
        year=2,
        completed_courses=["CS 135", "CS 136"],
        interests=[]
    )
    
    mock_ai = MockAI()
    eligible = mock_ai.filter_courses_by_prerequisites(courses, student)
    
    print(f"Total courses: {len(courses)}")
    print(f"Eligible courses: {len(eligible)}")
    print("\nEligible courses:")
    for course in eligible:
        print(f"  ✅ {course.code}")
    
    print("\nIneligible courses:")
    ineligible = [c for c in courses if c not in eligible]
    for course in ineligible:
        print(f"  ❌ {course.code} (requires: {course.prerequisites})")

def test_enhancement_logic():
    """Test recommendation enhancement logic"""
    print("\n✨ Testing recommendation enhancement...")
    
    # Basic recommendations
    recommendations = [
        CourseRecommendation(
            course_code="CS 240",
            confidence=0.85,
            reasoning="Good data structures course"
        ),
        CourseRecommendation(
            course_code="CS 341", 
            confidence=0.75,
            reasoning="Advanced algorithms"
        )
    ]
    
    # Available courses
    courses = [
        CourseInfo("CS 240", "Data Structures", "desc", 0.5, "CS 136", "CS", 200),
        CourseInfo("CS 341", "Algorithms", "desc", 0.5, "CS 240, CS 245", "CS", 300),
    ]
    
    student = StudentProfile(
        program="Computer Science",
        year=2,
        completed_courses=["CS 135", "CS 136"],
        interests=[]
    )
    
    # Mock enhancement logic
    validator = PrerequisiteValidator()
    course_lookup = {course.code: course for course in courses}
    
    enhanced = []
    for rec in recommendations:
        course = course_lookup.get(rec.course_code)
        if course:
            validation = validator.validate_prerequisites(
                course_prereqs=course.prerequisites or "",
                completed_courses=student.completed_courses,
                student_year=student.year,
                student_program=student.program
            )
            
            difficulty = validator.get_course_difficulty_score(course.code, course.prerequisites or "")
            
            enhanced_rec = CourseRecommendation(
                course_code=rec.course_code,
                confidence=rec.confidence,
                reasoning=rec.reasoning,
                prerequisite_status="satisfied" if validation.is_satisfied else "missing",
                missing_prereqs=validation.missing_prereqs,
                difficulty_score=difficulty
            )
            enhanced.append(enhanced_rec)
    
    print("Enhanced recommendations:")
    for rec in enhanced:
        status_emoji = "✅" if rec.prerequisite_status == "satisfied" else "❌"
        print(f"{status_emoji} {rec.course_code}:")
        print(f"  Confidence: {rec.confidence:.2f}")
        print(f"  Difficulty: {rec.difficulty_score:.2f}")
        print(f"  Prerequisites: {rec.prerequisite_status}")
        if rec.missing_prereqs:
            print(f"  Missing: {rec.missing_prereqs}")
        print(f"  Reasoning: {rec.reasoning}")
        print()

if __name__ == "__main__":
    print("🧪 Testing prerequisite validation integration...")
    
    test_prerequisite_integration()
    test_filtering_logic()
    test_enhancement_logic()
    
    print("\n✅ Integration tests completed!")