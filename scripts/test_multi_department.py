#!/usr/bin/env python3
"""
Test multi-department scraping
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.scraping.course_scraper import UWaterlooCourseScraper

def test_multi_department():
    """Test scraping multiple departments"""
    scraper = UWaterlooCourseScraper(rate_limit=0.5)  # Faster for testing
    
    # Test a few key departments
    test_departments = ['CS', 'MATH', 'STAT']
    
    for dept in test_departments:
        try:
            print(f"\n📚 Testing {dept} department...")
            courses = scraper.extract_courses_from_department(dept)
            print(f"Found {len(courses)} courses in {dept}")
            
            if courses:
                sample = courses[0]
                print(f"Sample: {sample.code} - {sample.title}")
                print(f"Credits: {sample.credits}, Level: {sample.level}")
                
                # Validate the course
                is_valid, issues = scraper.validate_course_data(sample)
                if not is_valid:
                    print(f"⚠️  Validation issues: {issues}")
                else:
                    print("✅ Course data valid")
        
        except Exception as e:
            print(f"❌ Error scraping {dept}: {e}")
    
    print(f"\n🎯 Testing scrape_all_departments()...")
    try:
        all_courses = scraper.scrape_all_departments()
        total = sum(len(courses) for courses in all_courses.values())
        print(f"Total courses across all departments: {total}")
        
        for dept, courses in all_courses.items():
            print(f"  {dept}: {len(courses)} courses")
    
    except Exception as e:
        print(f"❌ Error in bulk scraping: {e}")

if __name__ == "__main__":
    test_multi_department()