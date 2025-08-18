#!/usr/bin/env python3
"""
Test UWFlow data manager
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.models.database import init_db, SessionLocal, UWFlowData
from app.scraping.uwflow_data_manager import UWFlowDataManager

def test_uwflow_integration():
    """Test UWFlow data manager integration"""
    print("🧪 Testing UWFlow Data Manager Integration...")
    
    # Initialize database
    print("📊 Initializing database...")
    init_db()
    
    # Create manager
    manager = UWFlowDataManager()
    
    # Test courses
    test_courses = ["CS135", "ECE140", "STAT230", "MATH135", "ENVS200"]
    
    print(f"Testing with courses: {test_courses}")
    
    # Test individual course
    print(f"\n📚 Testing individual course fetch...")
    course_data = manager.get_or_fetch_uwflow_data("CS135")
    
    if course_data:
        print(f"✅ CS135 data:")
        print(f"  ID: {course_data.id}")
        print(f"  Rating: {course_data.rating}")
        print(f"  Difficulty: {course_data.difficulty}")
        print(f"  Workload: {course_data.workload}")
        print(f"  Usefulness: {course_data.usefulness}")
        print(f"  Reviews: {course_data.review_count}")
        print(f"  Liked: {course_data.liked_percentage}%")
    
    # Test multiple courses
    print(f"\n📚 Testing multiple course fetch...")
    multiple_data = manager.get_multiple_uwflow_data(test_courses)
    
    print(f"Retrieved data for {len(multiple_data)} courses:")
    for course_code, data in multiple_data.items():
        print(f"  {course_code}: Rating {data['rating']}/5.0, Difficulty {data['difficulty']}/5.0")
    
    # Test cached data (should be faster)
    print(f"\n📚 Testing cached data retrieval...")
    cached_data = manager.get_or_fetch_uwflow_data("CS135")
    
    if cached_data:
        print(f"✅ Retrieved cached data for CS135 (ID: {cached_data.id})")
        print(f"  Created: {cached_data.created_at}")
        print(f"  Updated: {cached_data.updated_at}")
    
    # Test force refresh
    print(f"\n🔄 Testing force refresh...")
    refreshed_data = manager.get_or_fetch_uwflow_data("CS135", force_refresh=True)
    
    if refreshed_data:
        print(f"✅ Force refreshed CS135 data")
        print(f"  Updated: {refreshed_data.updated_at}")
    
    # Test stats
    print(f"\n📊 UWFlow data statistics:")
    db = SessionLocal()
    try:
        stats = manager.get_uwflow_stats(db)
        for key, value in stats.items():
            print(f"  {key}: {value}")
    finally:
        db.close()
    
    # Test database query directly
    print(f"\n🗄️  Testing direct database queries...")
    db = SessionLocal()
    try:
        all_uwflow_data = db.query(UWFlowData).all()
        print(f"Total UWFlow records in database: {len(all_uwflow_data)}")
        
        for data in all_uwflow_data[:3]:  # Show first 3
            print(f"  {data.course_code}: {data.rating}/5.0 rating, {data.num_ratings} ratings")
    finally:
        db.close()
    
    print("\n✅ UWFlow data manager integration test completed!")

if __name__ == "__main__":
    test_uwflow_integration()