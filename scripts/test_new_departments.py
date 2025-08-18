#!/usr/bin/env python3
"""
Test the new departments including ENVS and BET
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.scraping.course_scraper import UWaterlooCourseScraper

def test_specific_departments():
    """Test specific departments that were mentioned"""
    scraper = UWaterlooCourseScraper()
    
    test_departments = ['ENVS', 'BET', 'MUSIC', 'THPERF', 'FINE']
    
    print("🎯 Testing specific departments of interest...")
    
    for dept in test_departments:
        print(f"\n📚 Testing {dept} department...")
        try:
            courses = scraper.extract_courses_from_department(dept)
            print(f"Found {len(courses)} {dept} courses")
            
            if courses:
                for i, course in enumerate(courses[:3]):  # Show first 3 courses
                    print(f"  {i+1}. {course.code}: {course.title}")
                    if course.code == 'ENVS 200':
                        print(f"     🐦 Found the bird watching course! Description: {course.description[:100]}...")
                    elif course.code == 'BET 300':
                        print(f"     💡 Found the entrepreneurship course! Description: {course.description[:100]}...")
                
                if len(courses) > 3:
                    print(f"  ... and {len(courses) - 3} more courses")
        
        except Exception as e:
            print(f"❌ Error with {dept}: {e}")
    
    # Test the total count now
    print(f"\n📊 Total departments available: {len(scraper.DEPARTMENT_URLS)}")
    print(f"Original count: 10 departments")
    print(f"New count: {len(scraper.DEPARTMENT_URLS)} departments")
    print(f"Improvement: {len(scraper.DEPARTMENT_URLS) / 10:.1f}x more departments!")

if __name__ == "__main__":
    test_specific_departments()