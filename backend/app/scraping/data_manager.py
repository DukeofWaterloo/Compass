"""
Data manager for course scraping and database operations
"""

import json
import hashlib
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.database import Course, SessionLocal, get_db, init_db
from app.scraping.course_scraper import CourseData, UWaterlooCourseScraper
from app.scraping.validators import CourseDataValidator, BatchValidator
import logging

logger = logging.getLogger(__name__)

class CourseDataManager:
    """Manages course data between scraping and database"""
    
    def __init__(self):
        self.scraper = UWaterlooCourseScraper()
        self.validator = CourseDataValidator()
        self.batch_validator = BatchValidator()
        # Ensure database tables exist
        init_db()
    
    def save_course_to_db(self, course_data: CourseData, db: Session) -> Course:
        """Save a single course to database"""
        # Check if course already exists
        existing_course = db.query(Course).filter(Course.code == course_data.code).first()
        
        # Convert terms list to JSON string
        terms_json = json.dumps(course_data.terms_offered) if course_data.terms_offered else "[]"
        
        if existing_course:
            # Update existing course
            existing_course.title = course_data.title
            existing_course.description = course_data.description
            existing_course.credits = course_data.credits
            existing_course.course_id = course_data.course_id
            existing_course.course_type = course_data.course_type
            existing_course.prerequisites = course_data.prerequisites
            existing_course.corequisites = course_data.corequisites
            existing_course.antirequisites = course_data.antirequisites
            existing_course.terms_offered = terms_json
            existing_course.notes = course_data.notes
            existing_course.department = course_data.department
            existing_course.level = course_data.level
            existing_course.url = course_data.url
            existing_course.is_active = True
            
            db.commit()
            db.refresh(existing_course)
            logger.debug(f"Updated course: {course_data.code}")
            return existing_course
        
        else:
            # Create new course
            new_course = Course(
                code=course_data.code,
                title=course_data.title,
                description=course_data.description,
                credits=course_data.credits,
                course_id=course_data.course_id,
                course_type=course_data.course_type,
                prerequisites=course_data.prerequisites,
                corequisites=course_data.corequisites,
                antirequisites=course_data.antirequisites,
                terms_offered=terms_json,
                notes=course_data.notes,
                department=course_data.department,
                level=course_data.level,
                url=course_data.url
            )
            
            db.add(new_course)
            db.commit()
            db.refresh(new_course)
            logger.debug(f"Created course: {course_data.code}")
            return new_course
    
    def save_courses_to_db(self, courses: List[CourseData], db: Session, validate: bool = True) -> Dict[str, int]:
        """Save multiple courses to database with validation"""
        saved_count = 0
        validation_corrections = 0
        validation_failures = 0
        
        # Validate courses if requested
        if validate:
            logger.info(f"Validating {len(courses)} courses...")
            validation_results = self.batch_validator.validate_batch(courses)
            
            logger.info(f"Validation summary: {validation_results['valid_courses']} valid, "
                       f"{validation_results['invalid_courses']} invalid, "
                       f"{validation_results['courses_with_warnings']} with warnings")
            
            # Get corrected courses
            courses = self.batch_validator.get_corrected_courses(courses)
            validation_corrections = validation_results['corrected_courses']
        
        for course_data in courses:
            try:
                # Final validation before saving
                if validate:
                    validation_result = self.validator.validate_course(course_data)
                    if not validation_result.is_valid:
                        logger.warning(f"Skipping invalid course {course_data.code}: {validation_result.issues}")
                        validation_failures += 1
                        continue
                
                self.save_course_to_db(course_data, db)
                saved_count += 1
            except Exception as e:
                logger.error(f"Failed to save course {course_data.code}: {e}")
        
        logger.info(f"Saved {saved_count}/{len(courses)} courses to database")
        if validation_corrections > 0:
            logger.info(f"Applied corrections to {validation_corrections} courses")
        if validation_failures > 0:
            logger.warning(f"Skipped {validation_failures} courses due to validation failures")
        
        return {
            'saved': saved_count,
            'total': len(courses),
            'corrections': validation_corrections,
            'failures': validation_failures
        }
    
    def scrape_and_save_department(self, department: str, validate: bool = True) -> Dict[str, any]:
        """Scrape a department and save to database with validation"""
        logger.info(f"Scraping and saving {department} courses...")
        
        try:
            # Scrape courses
            courses = self.scraper.extract_courses_from_department(department)
            
            # Save to database with validation
            with SessionLocal() as db:
                results = self.save_courses_to_db(courses, db, validate=validate)
            
            results['department'] = department
            results['scraped'] = len(courses)
            
            logger.info(f"Successfully processed {department}: {results['saved']} courses saved")
            return results
            
        except Exception as e:
            logger.error(f"Failed to scrape and save {department}: {e}")
            return {
                'department': department,
                'saved': 0,
                'total': 0,
                'scraped': 0,
                'corrections': 0,
                'failures': 0,
                'error': str(e)
            }
    
    def scrape_and_save_all_departments(self) -> Dict[str, int]:
        """Scrape all departments and save to database"""
        logger.info("Starting full course data refresh...")
        
        results = {}
        total_saved = 0
        
        for department in self.scraper.DEPARTMENT_URLS.keys():
            saved_count = self.scrape_and_save_department(department)
            results[department] = saved_count
            total_saved += saved_count
        
        logger.info(f"Course data refresh complete: {total_saved} total courses saved")
        return results
    
    def get_courses_by_department(self, department: str, db: Session) -> List[Course]:
        """Get all courses for a department from database"""
        return db.query(Course).filter(
            and_(Course.department == department, Course.is_active == True)
        ).all()
    
    def search_courses(self, query: str, db: Session, limit: int = 50) -> List[Course]:
        """Search courses by code, title, or description"""
        search_filter = or_(
            Course.code.ilike(f"%{query}%"),
            Course.title.ilike(f"%{query}%"),
            Course.description.ilike(f"%{query}%")
        )
        
        return db.query(Course).filter(
            and_(search_filter, Course.is_active == True)
        ).limit(limit).all()
    
    def get_course_by_code(self, course_code: str, db: Session) -> Optional[Course]:
        """Get a specific course by code"""
        return db.query(Course).filter(
            and_(Course.code == course_code, Course.is_active == True)
        ).first()
    
    def get_courses_by_level(self, level: int, db: Session, limit: int = 100) -> List[Course]:
        """Get courses by level (100, 200, 300, 400)"""
        return db.query(Course).filter(
            and_(Course.level == level, Course.is_active == True)
        ).limit(limit).all()
    
    def get_database_stats(self, db: Session) -> Dict[str, int]:
        """Get database statistics"""
        total_courses = db.query(Course).filter(Course.is_active == True).count()
        
        department_counts = {}
        for dept in self.scraper.DEPARTMENT_URLS.keys():
            count = db.query(Course).filter(
                and_(Course.department == dept, Course.is_active == True)
            ).count()
            department_counts[dept] = count
        
        return {
            "total_courses": total_courses,
            "department_breakdown": department_counts
        }

# Utility function for initial data population
def populate_database():
    """Initial database population with course data"""
    from app.models.database import init_db
    
    # Initialize database
    init_db()
    
    # Create data manager and populate
    manager = CourseDataManager()
    results = manager.scrape_and_save_all_departments()
    
    print("Database population complete!")
    print("Results:")
    for dept, count in results.items():
        print(f"  {dept}: {count} courses")
    
    total = sum(results.values())
    print(f"Total: {total} courses")

if __name__ == "__main__":
    populate_database()