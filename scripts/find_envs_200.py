#!/usr/bin/env python3
"""
Search for ENVS 200 specifically
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.scraping.course_scraper import UWaterlooCourseScraper

def find_envs_200():
    """Find the bird watching course ENVS 200"""
    scraper = UWaterlooCourseScraper()
    
    print("🐦 Searching for ENVS 200 (bird watching course)...")
    
    try:
        envs_courses = scraper.extract_courses_from_department('ENVS')
        print(f"Found {len(envs_courses)} ENVS courses total")
        
        for course in envs_courses:
            print(f"  {course.code}: {course.title}")
            if '200' in course.code:
                print(f"    🎯 FOUND IT! Description: {course.description}")
        
        # Also look for any bird-related courses
        print(f"\n🔍 Looking for bird-related courses in ENVS...")
        for course in envs_courses:
            if any(keyword in course.description.lower() for keyword in ['bird', 'ornithology', 'wildlife', 'animal']):
                print(f"  🐦 {course.code}: {course.title}")
                print(f"     Description: {course.description[:150]}...")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    find_envs_200()