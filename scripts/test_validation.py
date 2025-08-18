#!/usr/bin/env python3
"""
Test enhanced data validation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.scraping.validators import CourseDataValidator, BatchValidator
from app.scraping.course_scraper import UWaterlooCourseScraper

def test_validation():
    """Test the validation system"""
    print("🔍 Testing course data validation...")
    
    # Get some sample courses
    scraper = UWaterlooCourseScraper()
    courses = scraper.extract_courses_from_department('CS')[:5]  # First 5 courses
    
    # Test individual validation
    validator = CourseDataValidator()
    print(f"\n📋 Individual validation results:")
    
    for course in courses:
        result = validator.validate_course(course)
        print(f"\n{course.code}:")
        print(f"  Valid: {result.is_valid}")
        if result.issues:
            print(f"  Issues: {result.issues}")
        if result.warnings:
            print(f"  Warnings: {result.warnings}")
        if result.corrected_data:
            print(f"  Has corrections: Department={result.corrected_data.department}, Level={result.corrected_data.level}")
    
    # Test batch validation
    batch_validator = BatchValidator()
    batch_results = batch_validator.validate_batch(courses)
    
    print(f"\n📊 Batch validation summary:")
    print(f"  Total courses: {batch_results['total_courses']}")
    print(f"  Valid: {batch_results['valid_courses']}")
    print(f"  Invalid: {batch_results['invalid_courses']}")
    print(f"  With warnings: {batch_results['courses_with_warnings']}")
    print(f"  Corrected: {batch_results['corrected_courses']}")
    
    if batch_results['summary_issues']:
        print(f"\n⚠️  Common issues:")
        for issue, count in batch_results['summary_issues'].items():
            print(f"    {issue}: {count}")
    
    if batch_results['summary_warnings']:
        print(f"\n⚡ Common warnings:")
        for warning, count in batch_results['summary_warnings'].items():
            print(f"    {warning}: {count}")

if __name__ == "__main__":
    test_validation()