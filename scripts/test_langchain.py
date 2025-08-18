#!/usr/bin/env python3
"""
Quick POC to test LangChain integration for course recommendations
"""

import os
from typing import List, Dict

# Mock course data for testing
SAMPLE_COURSES = [
    {
        "code": "CS 135",
        "title": "Designing Functional Programs",
        "description": "An introduction to the fundamentals of computer science through the application of elementary programming patterns and the design of algorithms. Introduction to problem solving, syntax, and semantics of a functional programming language.",
        "prerequisites": "None",
        "credits": 0.5
    },
    {
        "code": "ECE 240",
        "title": "Electronic Circuits 1",
        "description": "Introduction to electronic signal processing; second-order circuits; operational amplifier circuits; diode device and circuits; MOS biasing networks; load-line analysis.",
        "prerequisites": "ECE 106, 140, MATH 119",
        "credits": 0.5
    },
    {
        "code": "MATH 239",
        "title": "Introduction to Combinatorics",
        "description": "Introduction to graph theory: colourings, matchings, connectivity, planarity. Introduction to combinatorial analysis: generating series, recurrence relations, binary strings, plane trees.",
        "prerequisites": "MATH 138",
        "credits": 0.5
    },
    {
        "code": "STAT 230",
        "title": "Probability",
        "description": "Probability models for sample spaces, events, conditional probability and independence. Random variables, distribution functions, expectation and variance.",
        "prerequisites": "MATH 128 or 138",
        "credits": 0.5
    }
]

def simple_recommendation_engine(user_input: Dict) -> List[str]:
    """
    Simple rule-based recommendation without LangChain (for comparison)
    """
    program = user_input.get("program", "").lower()
    year = user_input.get("year", 1)
    interests = user_input.get("interests", [])
    
    recommendations = []
    
    for course in SAMPLE_COURSES:
        # Simple matching logic
        if program in ["computer science", "cs"] and course["code"].startswith("CS"):
            recommendations.append(f"{course['code']}: {course['title']}")
        elif program in ["electrical engineering", "ece"] and course["code"].startswith("ECE"):
            recommendations.append(f"{course['code']}: {course['title']}")
        elif "math" in interests and course["code"].startswith("MATH"):
            recommendations.append(f"{course['code']}: {course['title']}")
        elif "statistics" in interests and course["code"].startswith("STAT"):
            recommendations.append(f"{course['code']}: {course['title']}")
    
    return recommendations

def test_langchain_approach():
    """
    Test LangChain approach for course recommendations
    Note: This is a mock since we don't have API keys set up
    """
    print("🔗 Testing LangChain approach (simulated)...")
    
    # This would be the actual LangChain implementation:
    """
    from langchain.llms import OpenAI
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
    
    # Create prompt template
    template = '''
    Based on the following course catalog and student information, recommend 3-5 courses:
    
    Student Profile:
    - Program: {program}
    - Year: {year}
    - Interests: {interests}
    - Completed Courses: {completed}
    
    Available Courses:
    {courses}
    
    Please recommend courses that:
    1. Match the student's program requirements
    2. Align with their interests
    3. Are appropriate for their year level
    4. Have prerequisites they've likely met
    
    Recommendations:
    '''
    
    prompt = PromptTemplate(
        input_variables=["program", "year", "interests", "completed", "courses"],
        template=template
    )
    
    llm = OpenAI(temperature=0.7)
    chain = LLMChain(llm=llm, prompt=prompt)
    
    result = chain.run({
        "program": "Computer Engineering",
        "year": 2,
        "interests": ["machine learning", "circuits"],
        "completed": ["CS 135", "ECE 140"],
        "courses": course_data
    })
    """
    
    # Simulated LangChain response
    simulated_response = """
    Based on your Computer Engineering program and interests in machine learning and circuits, I recommend:

    1. ECE 240: Electronic Circuits 1 - Perfect for your circuits interest and builds on ECE 140
    2. STAT 230: Probability - Essential foundation for machine learning
    3. MATH 239: Introduction to Combinatorics - Useful for algorithm design and ML theory
    
    These courses align with your year level and program requirements while supporting your interests.
    """
    
    return simulated_response.strip()

if __name__ == "__main__":
    print("🧪 Testing Course Recommendation Approaches...")
    
    # Test data
    test_student = {
        "program": "Computer Engineering", 
        "year": 2,
        "interests": ["machine learning", "circuits"],
        "completed": ["CS 135", "ECE 140"]
    }
    
    print(f"\nStudent Profile: {test_student}")
    
    # Test 1: Simple rule-based
    print("\n1. Simple Rule-Based Recommendations:")
    simple_recs = simple_recommendation_engine(test_student)
    for rec in simple_recs:
        print(f"  • {rec}")
    
    # Test 2: LangChain approach (simulated)
    print("\n2. LangChain AI Recommendations:")
    ai_recs = test_langchain_approach()
    print(f"  {ai_recs}")
    
    print("\n✅ POC complete!")
    print("\nNext steps:")
    print("- Set up proper LangChain with API keys")
    print("- Improve course data extraction")
    print("- Build web interface")
    print("- Create GitHub repo structure")