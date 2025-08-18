"""
UWFlow data manager for storing and retrieving course ratings
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.database import UWFlowData, SessionLocal
from app.scraping.uwflow_enhanced import EnhancedUWFlowScraper, UWFlowCourseData

logger = logging.getLogger(__name__)

class UWFlowDataManager:
    """Manages UWFlow data storage and retrieval"""
    
    def __init__(self):
        self.scraper = EnhancedUWFlowScraper()
        logger.info("Initialized UWFlow data manager")
    
    def get_or_fetch_uwflow_data(self, course_code: str, db: Session = None, force_refresh: bool = False) -> Optional[UWFlowData]:
        """
        Get UWFlow data from database or fetch from web if needed
        
        Args:
            course_code: Course code like "CS135"
            db: Database session (optional)
            force_refresh: Force fetching fresh data from web
            
        Returns:
            UWFlowData object or None
        """
        should_close_db = db is None
        if db is None:
            db = SessionLocal()
        
        try:
            normalized_code = self._normalize_course_code(course_code)
            
            # Check if we have recent data
            if not force_refresh:
                cached_data = self._get_cached_data(normalized_code, db)
                if cached_data:
                    logger.debug(f"Using cached UWFlow data for {normalized_code}")
                    return cached_data
            
            # Fetch fresh data from UWFlow
            logger.info(f"Fetching fresh UWFlow data for {normalized_code}")
            scraped_data = self.scraper.get_course_data(normalized_code)
            
            if scraped_data:
                # Store or update in database
                uwflow_data = self._store_uwflow_data(scraped_data, db)
                logger.info(f"Successfully stored UWFlow data for {normalized_code}")
                return uwflow_data
            else:
                logger.warning(f"No UWFlow data available for {normalized_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting UWFlow data for {course_code}: {e}")
            return None
        finally:
            if should_close_db:
                db.close()
    
    def get_multiple_uwflow_data(self, course_codes: List[str], db: Session = None, force_refresh: bool = False) -> Dict[str, Dict]:
        """
        Get UWFlow data for multiple courses efficiently
        
        Args:
            course_codes: List of course codes
            db: Database session (optional)
            force_refresh: Force fetching fresh data
            
        Returns:
            Dictionary mapping course codes to UWFlow data dicts
        """
        should_close_db = db is None
        if db is None:
            db = SessionLocal()
        
        try:
            results = {}
            
            # Normalize course codes
            normalized_codes = [self._normalize_course_code(code) for code in course_codes]
            
            if not force_refresh:
                # Get cached data for all courses
                cached_data = self._get_multiple_cached_data(normalized_codes, db)
                for code, data in cached_data.items():
                    results[code] = self._uwflow_data_to_dict(data)
                
                # Find courses that need fresh data
                missing_codes = [code for code in normalized_codes if code not in results]
            else:
                missing_codes = normalized_codes
            
            # Fetch missing data from UWFlow
            if missing_codes:
                logger.info(f"Fetching UWFlow data for {len(missing_codes)} courses")
                
                for course_code in missing_codes:
                    try:
                        scraped_data = self.scraper.get_course_data(course_code)
                        if scraped_data:
                            uwflow_data = self._store_uwflow_data(scraped_data, db)
                            results[course_code] = self._uwflow_data_to_dict(uwflow_data)
                    except Exception as e:
                        logger.error(f"Error fetching UWFlow data for {course_code}: {e}")
                        continue
            
            logger.info(f"Retrieved UWFlow data for {len(results)}/{len(course_codes)} courses")
            return results
            
        finally:
            if should_close_db:
                db.close()
    
    def refresh_stale_data(self, db: Session = None, max_age_days: int = 30) -> int:
        """
        Refresh stale UWFlow data
        
        Args:
            db: Database session (optional)
            max_age_days: Maximum age in days before data is considered stale
            
        Returns:
            Number of courses refreshed
        """
        should_close_db = db is None
        if db is None:
            db = SessionLocal()
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
            
            # Find stale data
            stale_courses = db.query(UWFlowData).filter(
                and_(
                    UWFlowData.updated_at < cutoff_date,
                    UWFlowData.is_stale == False
                )
            ).all()
            
            logger.info(f"Found {len(stale_courses)} courses with stale UWFlow data")
            
            refreshed_count = 0
            for course_data in stale_courses:
                try:
                    # Fetch fresh data
                    scraped_data = self.scraper.get_course_data(course_data.course_code)
                    
                    if scraped_data:
                        # Update existing record
                        self._update_uwflow_data(course_data, scraped_data, db)
                        refreshed_count += 1
                        logger.debug(f"Refreshed UWFlow data for {course_data.course_code}")
                    else:
                        # Mark as stale if no data available
                        course_data.is_stale = True
                        db.commit()
                        
                except Exception as e:
                    logger.error(f"Error refreshing UWFlow data for {course_data.course_code}: {e}")
                    continue
            
            logger.info(f"Successfully refreshed {refreshed_count} courses")
            return refreshed_count
            
        finally:
            if should_close_db:
                db.close()
    
    def _normalize_course_code(self, course_code: str) -> str:
        """Normalize course code format"""
        return course_code.replace(" ", "").upper()
    
    def _get_cached_data(self, course_code: str, db: Session, max_age_days: int = 7) -> Optional[UWFlowData]:
        """Get cached UWFlow data if recent enough"""
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        
        return db.query(UWFlowData).filter(
            and_(
                UWFlowData.course_code == course_code,
                UWFlowData.updated_at >= cutoff_date,
                UWFlowData.is_stale == False
            )
        ).first()
    
    def _get_multiple_cached_data(self, course_codes: List[str], db: Session, max_age_days: int = 7) -> Dict[str, UWFlowData]:
        """Get cached UWFlow data for multiple courses"""
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        
        cached_data = db.query(UWFlowData).filter(
            and_(
                UWFlowData.course_code.in_(course_codes),
                UWFlowData.updated_at >= cutoff_date,
                UWFlowData.is_stale == False
            )
        ).all()
        
        return {data.course_code: data for data in cached_data}
    
    def _store_uwflow_data(self, scraped_data: UWFlowCourseData, db: Session) -> UWFlowData:
        """Store scraped UWFlow data in database"""
        
        # Check if record already exists
        existing = db.query(UWFlowData).filter(
            UWFlowData.course_code == scraped_data.course_code
        ).first()
        
        if existing:
            # Update existing record
            self._update_uwflow_data(existing, scraped_data, db)
            return existing
        else:
            # Create new record
            professor_ratings_json = json.dumps(scraped_data.professor_ratings) if scraped_data.professor_ratings else None
            
            uwflow_data = UWFlowData(
                course_code=scraped_data.course_code,
                rating=scraped_data.rating,
                difficulty=scraped_data.difficulty,
                workload=scraped_data.workload,
                usefulness=scraped_data.usefulness,
                num_ratings=scraped_data.num_ratings,
                review_count=scraped_data.review_count,
                liked_percentage=scraped_data.liked_percentage,
                professor_ratings=professor_ratings_json,
                is_stale=False
            )
            
            db.add(uwflow_data)
            db.commit()
            db.refresh(uwflow_data)
            
            return uwflow_data
    
    def _update_uwflow_data(self, existing: UWFlowData, scraped_data: UWFlowCourseData, db: Session):
        """Update existing UWFlow data record"""
        
        existing.rating = scraped_data.rating
        existing.difficulty = scraped_data.difficulty
        existing.workload = scraped_data.workload
        existing.usefulness = scraped_data.usefulness
        existing.num_ratings = scraped_data.num_ratings
        existing.review_count = scraped_data.review_count
        existing.liked_percentage = scraped_data.liked_percentage
        existing.professor_ratings = json.dumps(scraped_data.professor_ratings) if scraped_data.professor_ratings else None
        existing.is_stale = False
        existing.updated_at = datetime.utcnow()
        
        db.commit()
    
    def _uwflow_data_to_dict(self, uwflow_data: UWFlowData) -> Dict:
        """Convert UWFlowData object to dictionary"""
        return {
            'course_code': uwflow_data.course_code,
            'rating': uwflow_data.rating,
            'difficulty': uwflow_data.difficulty,
            'workload': uwflow_data.workload,
            'usefulness': uwflow_data.usefulness,
            'num_ratings': uwflow_data.num_ratings,
            'review_count': uwflow_data.review_count,
            'liked_percentage': uwflow_data.liked_percentage,
            'professor_ratings': json.loads(uwflow_data.professor_ratings) if uwflow_data.professor_ratings else [],
            'created_at': uwflow_data.created_at.isoformat() if uwflow_data.created_at else None,
            'updated_at': uwflow_data.updated_at.isoformat() if uwflow_data.updated_at else None
        }
    
    def get_uwflow_stats(self, db: Session = None) -> Dict:
        """Get statistics about UWFlow data in database"""
        should_close_db = db is None
        if db is None:
            db = SessionLocal()
        
        try:
            total_courses = db.query(UWFlowData).count()
            courses_with_ratings = db.query(UWFlowData).filter(UWFlowData.rating.isnot(None)).count()
            stale_courses = db.query(UWFlowData).filter(UWFlowData.is_stale == True).count()
            
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            recent_courses = db.query(UWFlowData).filter(UWFlowData.updated_at >= cutoff_date).count()
            
            from sqlalchemy import func
            avg_rating = db.query(func.avg(UWFlowData.rating)).filter(UWFlowData.rating.isnot(None)).scalar() or 0
            avg_difficulty = db.query(func.avg(UWFlowData.difficulty)).filter(UWFlowData.difficulty.isnot(None)).scalar() or 0
            
            return {
                'total_courses': total_courses,
                'courses_with_ratings': courses_with_ratings,
                'stale_courses': stale_courses,
                'recent_courses': recent_courses,
                'average_rating': round(avg_rating, 2) if avg_rating else 0,
                'average_difficulty': round(avg_difficulty, 2) if avg_difficulty else 0,
                'data_coverage': round((courses_with_ratings / total_courses * 100), 1) if total_courses > 0 else 0
            }
            
        finally:
            if should_close_db:
                db.close()


def test_uwflow_data_manager():
    """Test the UWFlow data manager"""
    print("🧪 Testing UWFlow Data Manager...")
    
    manager = UWFlowDataManager()
    
    # Test courses
    test_courses = ["CS135", "ECE140", "STAT230", "MATH135", "ENVS200"]
    
    print(f"Testing with courses: {test_courses}")
    
    # Test individual course
    print(f"\n📚 Testing individual course fetch...")
    course_data = manager.get_or_fetch_uwflow_data("CS135")
    
    if course_data:
        print(f"✅ CS135 data:")
        print(f"  Rating: {course_data.rating}")
        print(f"  Difficulty: {course_data.difficulty}")
        print(f"  Workload: {course_data.workload}")
        print(f"  Reviews: {course_data.review_count}")
    
    # Test multiple courses
    print(f"\n📚 Testing multiple course fetch...")
    multiple_data = manager.get_multiple_uwflow_data(test_courses)
    
    print(f"Retrieved data for {len(multiple_data)} courses:")
    for course_code, data in multiple_data.items():
        print(f"  {course_code}: Rating {data.rating}, Difficulty {data.difficulty}")
    
    # Test cached data (should be faster)
    print(f"\n📚 Testing cached data retrieval...")
    cached_data = manager.get_or_fetch_uwflow_data("CS135")
    
    if cached_data:
        print(f"✅ Retrieved cached data for CS135")
    
    # Test stats
    print(f"\n📊 UWFlow data statistics:")
    from app.models.database import SessionLocal
    db = SessionLocal()
    try:
        stats = manager.get_uwflow_stats(db)
        for key, value in stats.items():
            print(f"  {key}: {value}")
    finally:
        db.close()
    
    print("\n✅ UWFlow data manager test completed!")


if __name__ == "__main__":
    # Initialize database first
    from app.models.database import init_db
    init_db()
    
    test_uwflow_data_manager()