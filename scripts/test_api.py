#!/usr/bin/env python3
"""
Test the AI-powered API endpoints
"""

import requests
import json

API_BASE = "http://localhost:8000/api/v1"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{API_BASE}/health")
    print(f"Health: {response.status_code} - {response.json()}")

def test_courses():
    """Test courses endpoint"""
    print("\n📚 Testing courses endpoint...")
    response = requests.get(f"{API_BASE}/courses?department=CS&limit=3")
    if response.status_code == 200:
        courses = response.json()
        print(f"Found {len(courses)} CS courses")
        for course in courses:
            print(f"  - {course['code']}: {course['title']}")
    else:
        print(f"Error: {response.status_code}")

def test_ai_recommendations():
    """Test AI-powered recommendations"""
    print("\n🤖 Testing AI recommendations...")
    
    # Test student profile
    student_profile = {
        "program": "Computer Engineering",
        "year": 2,
        "completed_courses": ["CS 135", "ECE 140", "MATH 119"],
        "current_courses": ["ECE 240"],
        "interests": ["machine learning", "artificial intelligence"],
        "preferred_terms": ["Fall", "Winter"]
    }
    
    print(f"Student: {student_profile['program']} Year {student_profile['year']}")
    print(f"Interests: {', '.join(student_profile['interests'])}")
    
    response = requests.post(
        f"{API_BASE}/recommendations",
        json=student_profile,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        recommendations = response.json()
        print(f"\n🎯 Got {len(recommendations)} AI recommendations:")
        
        for i, rec in enumerate(recommendations, 1):
            course = rec['course']
            print(f"\n  {i}. {course['code']}: {course['title']}")
            print(f"     Credits: {course['credits']} | Department: {course['department']} | Level: {course['level']}")
            print(f"     Confidence: {rec['confidence']:.2f}")
            print(f"     AI Reasoning: {rec['reasoning']}")
            if course.get('prerequisites'):
                print(f"     Prerequisites: {course['prerequisites']}")
    
    else:
        print(f"Error: {response.status_code} - {response.text}")

def test_course_explanation():
    """Test course explanation endpoint"""
    print("\n💡 Testing course explanation...")
    
    student_profile = {
        "program": "Computer Engineering",
        "year": 2,
        "interests": ["machine learning"]
    }
    
    # Test explanation for CS 240
    response = requests.post(
        f"{API_BASE}/recommendations/explain?course_code=CS 240",
        json=student_profile,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        explanation = response.json()
        print(f"Explanation for {explanation['course_code']}:")
        print(f"  Fit Score: {explanation['fit_score']}")
        print(f"  Explanation: {explanation['explanation']}")
        print(f"  Prerequisites: {explanation['prerequisite_analysis']}")
        print(f"  Career Relevance: {explanation['career_relevance']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

def test_different_programs():
    """Test recommendations for different programs"""
    print("\n🎭 Testing different programs...")
    
    test_profiles = [
        {
            "program": "Environmental Studies",
            "year": 3,
            "completed_courses": ["ENVS 200"],
            "interests": ["sustainability", "ecology"],
            "preferred_terms": ["Fall"]
        },
        {
            "program": "Business Administration",
            "year": 1,
            "completed_courses": ["BET 100"],
            "interests": ["entrepreneurship", "marketing"],
            "preferred_terms": ["Winter"]
        }
    ]
    
    for profile in test_profiles:
        print(f"\n👤 {profile['program']} Year {profile['year']}:")
        print(f"   Interests: {', '.join(profile['interests'])}")
        
        response = requests.post(
            f"{API_BASE}/recommendations",
            json=profile,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            recommendations = response.json()
            print(f"   🎯 Top recommendations:")
            for rec in recommendations[:2]:
                course = rec['course']
                print(f"     • {course['code']}: {course['title']} (confidence: {rec['confidence']:.2f})")
        else:
            print(f"   ❌ Error: {response.status_code}")

if __name__ == "__main__":
    test_health()
    test_courses()
    test_ai_recommendations()
    test_course_explanation()
    test_different_programs()