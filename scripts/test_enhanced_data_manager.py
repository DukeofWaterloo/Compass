#!/usr/bin/env python3
"""
Test enhanced data manager with validation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.scraping.data_manager import CourseDataManager

def test_enhanced_manager():
    """Test the enhanced data manager with validation"""
    print("🔧 Testing enhanced data manager with validation...")
    
    # Create manager (includes validation)
    manager = CourseDataManager()
    
    # Test enhanced department scraping with validation
    print("\n1. Testing enhanced department scraping (STAT)...")
    results = manager.scrape_and_save_department('STAT', validate=True)
    
    print(f"📊 Results for {results['department']}:")
    print(f"  Scraped: {results['scraped']} courses")
    print(f"  Saved: {results['saved']}/{results['total']} courses")
    if results['corrections'] > 0:
        print(f"  Corrections applied: {results['corrections']}")
    if results['failures'] > 0:
        print(f"  Validation failures: {results['failures']}")
    if 'error' in results:
        print(f"  Error: {results['error']}")
    
    # Test with a department that doesn't exist (edge case)
    print("\n2. Testing error handling with invalid department...")
    results = manager.scrape_and_save_department('INVALID', validate=True)
    print(f"📊 Results for {results['department']}:")
    print(f"  Scraped: {results['scraped']} courses")
    print(f"  Saved: {results['saved']} courses")
    if 'error' in results:
        print(f"  Error handled: {results['error']}")

if __name__ == "__main__":
    test_enhanced_manager()