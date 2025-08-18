#!/usr/bin/env python3
"""
Test the prerequisite validation system
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.validation.prerequisite_validator import (
    PrerequisiteParser, 
    PrerequisiteValidator,
    ValidationResult
)

def test_prerequisite_parsing():
    """Test prerequisite string parsing"""
    print("🔍 Testing prerequisite parsing...")
    
    parser = PrerequisiteParser()
    
    test_cases = [
        "CS 135",  # Simple single course
        "MATH 135 and MATH 136",  # Two courses with AND
        "STAT 230 or STAT 240",  # Two courses with OR
        "CS 135, CS 136, MATH 135",  # Multiple courses (implicit AND)
        "2A standing",  # Level requirement
        "Enrolled in Computer Engineering",  # Program requirement
        "None",  # No prerequisites
        "CS 240 and (STAT 230 or STAT 240)",  # Complex expression
        "ECE 106, 140, MATH 119",  # Multiple with implicit AND
    ]
    
    for i, prereq_string in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{prereq_string}'")
        tree = parser.parse_prerequisites(prereq_string)
        
        if tree:
            print(f"   Parsed successfully")
            print(f"   Root operator: {tree.operator}")
            print(f"   Course code: {tree.course_code}")
            print(f"   Children: {len(tree.children)}")
            
            if tree.children:
                for j, child in enumerate(tree.children):
                    print(f"     Child {j+1}: {child.course_code} (op: {child.operator})")
        else:
            print("   No prerequisites (None)")

def test_prerequisite_validation():
    """Test prerequisite validation logic"""
    print("\n🎯 Testing prerequisite validation...")
    
    validator = PrerequisiteValidator()
    
    # Test cases: (prereq_string, completed_courses, expected_result)
    test_cases = [
        # Simple cases
        ("CS 135", ["CS 135"], True),
        ("CS 135", ["CS 136"], False),
        ("None", [], True),
        
        # AND cases
        ("CS 135 and MATH 135", ["CS 135", "MATH 135"], True),
        ("CS 135 and MATH 135", ["CS 135"], False),
        ("CS 135, MATH 135", ["CS 135", "MATH 135"], True),
        
        # OR cases
        ("CS 135 or CS 145", ["CS 135"], True),
        ("CS 135 or CS 145", ["CS 145"], True),
        ("CS 135 or CS 145", ["MATH 135"], False),
        
        # Level requirements
        ("2A standing", [], True),  # Assuming default year > 2
        
        # Complex cases
        ("CS 240 and (STAT 230 or STAT 240)", ["CS 240", "STAT 230"], True),
        ("CS 240 and (STAT 230 or STAT 240)", ["CS 240", "STAT 240"], True),
        ("CS 240 and (STAT 230 or STAT 240)", ["CS 240"], False),
    ]
    
    for i, (prereq_string, completed, expected) in enumerate(test_cases, 1):
        print(f"\n{i}. Testing validation:")
        print(f"   Prerequisites: '{prereq_string}'")
        print(f"   Completed: {completed}")
        print(f"   Expected: {expected}")
        
        result = validator.validate_prerequisites(
            course_prereqs=prereq_string,
            completed_courses=completed,
            student_year=3,  # 3rd year student
            student_program="Computer Science"
        )
        
        print(f"   Result: {result.is_satisfied}")
        if not result.is_satisfied:
            print(f"   Missing: {result.missing_prereqs}")
        if result.warnings:
            print(f"   Warnings: {result.warnings}")
        
        # Check if result matches expectation
        if result.is_satisfied == expected:
            print("   ✅ PASS")
        else:
            print("   ❌ FAIL")

def test_difficulty_scoring():
    """Test course difficulty scoring"""
    print("\n📊 Testing difficulty scoring...")
    
    validator = PrerequisiteValidator()
    
    test_courses = [
        ("CS 135", "None"),
        ("CS 136", "CS 135"),
        ("CS 240", "CS 136 and (STAT 230 or STAT 240)"),
        ("CS 341", "CS 240, CS 245"),
        ("CS 444", "CS 350 and CS 341"),
        ("MATH 135", "None"),
        ("STAT 430", "STAT 330 and STAT 230"),
    ]
    
    print("\nCourse difficulty scores (0.0 = easiest, 1.0 = hardest):")
    for course_code, prereqs in test_courses:
        score = validator.get_course_difficulty_score(course_code, prereqs)
        print(f"  {course_code}: {score:.2f} (prereqs: {prereqs})")

def test_path_suggestions():
    """Test prerequisite path suggestions"""
    print("\n🛤️  Testing prerequisite path suggestions...")
    
    validator = PrerequisiteValidator()
    
    # Simulate a student who wants to take CS 240 but only has CS 135
    target_course = "CS 240"
    target_prereqs = "CS 136 and (STAT 230 or STAT 240)"
    completed_courses = ["CS 135", "MATH 135", "MATH 136"]
    
    print(f"Target course: {target_course}")
    print(f"Prerequisites: {target_prereqs}")
    print(f"Completed courses: {completed_courses}")
    
    # Check current validation
    validation = validator.validate_prerequisites(
        target_prereqs, 
        completed_courses,
        student_year=2,
        student_program="Computer Science"
    )
    
    print(f"\nCurrent validation:")
    print(f"  Can take course: {validation.is_satisfied}")
    print(f"  Missing prerequisites: {validation.missing_prereqs}")
    
    # Get path suggestions
    available_courses = []  # Would normally contain all available courses
    path = validator.suggest_prerequisite_path(
        target_course,
        target_prereqs, 
        completed_courses,
        available_courses
    )
    
    print(f"  Suggested prerequisite path: {path}")

def test_real_uwaterloo_prerequisites():
    """Test with real UWaterloo prerequisite strings"""
    print("\n🏫 Testing with real UWaterloo prerequisite patterns...")
    
    validator = PrerequisiteValidator()
    
    # Real prerequisite strings from UWaterloo courses
    real_prereqs = [
        "One of MATH 114, 115, 117, 135, 145",
        "MATH 135; one of MATH 136, 146",
        "CS 136; MATH 135, 136; one of MATH 237, 247",
        "4A students, or permission of instructor",
        "Level at least 3A",
        "Admission to the Faculty of Engineering",
        "CS 240, 245; STAT 230",
        "Not open to Computer Science students",
        "One of CS 230, 240, 330, ECE 250",
        "Prereq: CS 341 or (CS 240 and MATH 239)",
    ]
    
    # Test student profile
    completed_courses = [
        "MATH 135", "MATH 136", "MATH 237", 
        "CS 135", "CS 136", "CS 240", "CS 245",
        "STAT 230"
    ]
    
    print("Student completed courses:", completed_courses)
    print("\nValidation results:")
    
    for i, prereq_string in enumerate(real_prereqs, 1):
        print(f"\n{i}. Prerequisites: '{prereq_string}'")
        
        result = validator.validate_prerequisites(
            course_prereqs=prereq_string,
            completed_courses=completed_courses,
            student_year=3,
            student_program="Computer Science"
        )
        
        print(f"   Can take: {result.is_satisfied}")
        if not result.is_satisfied:
            print(f"   Missing: {result.missing_prereqs}")
        if result.warnings:
            print(f"   Warnings: {result.warnings}")

if __name__ == "__main__":
    print("🧪 Testing prerequisite validation system...")
    
    test_prerequisite_parsing()
    test_prerequisite_validation()
    test_difficulty_scoring()
    test_path_suggestions()
    test_real_uwaterloo_prerequisites()
    
    print("\n✅ All tests completed!")