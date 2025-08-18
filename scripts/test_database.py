#!/usr/bin/env python3
"""
Test database operations with a small amount of data
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.scraping.data_manager import CourseDataManager
from app.models.database import SessionLocal

def test_database_operations():
    """Test database operations with CS department only"""
    print("🗄️  Testing database operations...")
    
    # Create data manager
    manager = CourseDataManager()
    
    # Test 1: Scrape and save CS department only (smaller dataset)
    print("\n1. Testing scrape and save for CS department...")
    saved_count = manager.scrape_and_save_department('CS')
    print(f"Saved {saved_count} CS courses to database")
    
    # Test 2: Query database
    print("\n2. Testing database queries...")
    with SessionLocal() as db:
        # Get all CS courses
        cs_courses = manager.get_courses_by_department('CS', db)
        print(f"Found {len(cs_courses)} CS courses in database")
        
        if cs_courses:
            sample_course = cs_courses[0]
            print(f"Sample course: {sample_course.code} - {sample_course.title}")
            print(f"Description: {sample_course.description[:100]}...")
        
        # Test search
        search_results = manager.search_courses('programming', db, limit=5)
        print(f"\nSearch for 'programming': {len(search_results)} results")
        for course in search_results:
            print(f"  - {course.code}: {course.title}")
        
        # Test course by code
        specific_course = manager.get_course_by_code('CS 135', db)
        if specific_course:
            print(f"\nFound CS 135: {specific_course.title}")
            print(f"Prerequisites: {specific_course.prerequisites}")
        
        # Get database stats
        stats = manager.get_database_stats(db)
        print(f"\n📊 Database stats:")
        print(f"Total courses: {stats['total_courses']}")
        for dept, count in stats['department_breakdown'].items():
            if count > 0:
                print(f"  {dept}: {count} courses")

if __name__ == "__main__":
    test_database_operations()