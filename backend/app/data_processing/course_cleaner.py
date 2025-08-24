"""
Course data cleaning pipeline for high-quality embeddings
"""

import re
import logging
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from app.models.database import Course, SessionLocal

logger = logging.getLogger(__name__)

class CourseDataCleaner:
    """Clean and enhance course data for embedding generation"""
    
    def __init__(self):
        self.boilerplate_patterns = [
            r'Preparing for, conducting, and reporting of laboratory experiments\.?',
            r'Students will gain experience.*through.*assignments\.?',
            r'This course is offered.*terms?\.?',
            r'Offered.*terms?\.?',
            r'Prerequisites?:?\s*(None|NONE|N/A)\.?',
            r'Antirequisites?:?\s*(None|NONE|N/A)\.?',
            r'Corequisites?:?\s*(None|NONE|N/A)\.?',
            r'Course ID:\s*\d+',
            r'\[Offered:.*?\]',
            r'\(Credit course for designated students only\)',
        ]
        
        self.abbreviation_expansions = {
            'prereq': 'prerequisite',
            'coreq': 'corequisite', 
            'antireq': 'antirequisite',
            'eng': 'engineering',
            'sci': 'science',
            'math': 'mathematics',
            'phys': 'physics',
            'chem': 'chemistry',
            'biol': 'biology',
            'psych': 'psychology',
            'econ': 'economics',
            'mgmt': 'management'
        }

    def clean_all_courses(self) -> Dict[str, int]:
        """Clean all courses in the database"""
        with SessionLocal() as db:
            courses = db.query(Course).filter(Course.is_active == True).all()
            
            stats = {
                'total_processed': 0,
                'descriptions_cleaned': 0,
                'titles_cleaned': 0,
                'prerequisites_normalized': 0
            }
            
            for course in courses:
                if self.clean_course(course, db):
                    stats['total_processed'] += 1
                    if hasattr(course, '_description_cleaned'):
                        stats['descriptions_cleaned'] += 1
                    if hasattr(course, '_title_cleaned'):
                        stats['titles_cleaned'] += 1
                    if hasattr(course, '_prereqs_cleaned'):
                        stats['prerequisites_normalized'] += 1
            
            db.commit()
            logger.info(f"Cleaned {stats['total_processed']} courses")
            return stats

    def clean_course(self, course: Course, db: Session) -> bool:
        """Clean an individual course"""
        changed = False
        
        # Clean description
        if course.description:
            cleaned_desc = self.clean_description(course.description)
            if cleaned_desc != course.description:
                course.description = cleaned_desc
                course._description_cleaned = True
                changed = True
        
        # Clean title
        if course.title:
            cleaned_title = self.clean_title(course.title)
            if cleaned_title != course.title:
                course.title = cleaned_title
                course._title_cleaned = True
                changed = True
        
        # Normalize prerequisites
        if course.prerequisites:
            normalized_prereqs = self.normalize_prerequisites(course.prerequisites)
            if normalized_prereqs != course.prerequisites:
                course.prerequisites = normalized_prereqs
                course._prereqs_cleaned = True
                changed = True
        
        return changed

    def clean_description(self, description: str) -> str:
        """Clean course description for better embeddings"""
        if not description:
            return description
        
        # Remove HTML artifacts
        desc = re.sub(r'<[^>]+>', '', description)
        
        # Normalize whitespace
        desc = re.sub(r'\s+', ' ', desc).strip()
        
        # Remove boilerplate text
        for pattern in self.boilerplate_patterns:
            desc = re.sub(pattern, '', desc, flags=re.IGNORECASE)
        
        # Expand abbreviations for better semantic understanding
        words = desc.split()
        expanded_words = []
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word.lower())
            if clean_word in self.abbreviation_expansions:
                expanded_words.append(self.abbreviation_expansions[clean_word])
            else:
                expanded_words.append(word)
        
        desc = ' '.join(expanded_words)
        
        # Remove extra punctuation and normalize
        desc = re.sub(r'[\.\s]+$', '.', desc)
        desc = re.sub(r'^\s*[\.\s]+', '', desc)
        
        return desc.strip()

    def clean_title(self, title: str) -> str:
        """Clean course title"""
        if not title:
            return title
        
        # Remove course code if it appears at start of title
        title = re.sub(r'^[A-Z]+\s+\d+[A-Z]?\s*[-:]?\s*', '', title)
        
        # Normalize whitespace
        title = re.sub(r'\s+', ' ', title).strip()
        
        # Remove trailing punctuation except periods that belong to abbreviations
        title = re.sub(r'[,;:\-]+$', '', title)
        
        return title.title() if title else title

    def normalize_prerequisites(self, prereqs: str) -> str:
        """Normalize prerequisite text"""
        if not prereqs or prereqs.lower() in ['none', 'n/a', 'null']:
            return None
        
        # Normalize whitespace
        prereqs = re.sub(r'\s+', ' ', prereqs).strip()
        
        # Standardize course code format (ECE240 -> ECE 240)
        prereqs = re.sub(r'([A-Z]+)(\d+)', r'\1 \2', prereqs)
        
        # Clean up common patterns
        prereqs = re.sub(r'Prerequisites?:?\s*', '', prereqs, flags=re.IGNORECASE)
        prereqs = re.sub(r'Prereq:?\s*', '', prereqs, flags=re.IGNORECASE)
        
        return prereqs.strip() if prereqs.strip() else None

    def validate_course_quality(self, course: Course) -> List[str]:
        """Validate course data quality for embeddings"""
        issues = []
        
        # Check description length and quality
        if not course.description or len(course.description.strip()) < 20:
            issues.append("Description too short for meaningful embeddings")
        
        if course.description and len(course.description.split()) < 5:
            issues.append("Description has too few words")
        
        # Check title quality
        if not course.title or len(course.title.strip()) < 3:
            issues.append("Title too short")
        
        if course.title and course.title.isupper():
            issues.append("Title is all uppercase (may need normalization)")
        
        # Check for potential parsing errors
        if course.description and 'Course ID:' in course.description:
            issues.append("Description contains unparsed course catalog artifacts")
        
        return issues

    def generate_quality_report(self) -> Dict:
        """Generate a data quality report"""
        with SessionLocal() as db:
            courses = db.query(Course).filter(Course.is_active == True).all()
            
            report = {
                'total_courses': len(courses),
                'quality_issues': {},
                'department_stats': {},
                'level_distribution': {},
                'high_quality_courses': 0
            }
            
            for course in courses:
                # Track department stats
                dept = course.department
                if dept not in report['department_stats']:
                    report['department_stats'][dept] = {'count': 0, 'avg_desc_length': 0}
                
                report['department_stats'][dept]['count'] += 1
                desc_len = len(course.description.split()) if course.description else 0
                report['department_stats'][dept]['avg_desc_length'] += desc_len
                
                # Track level distribution
                level = course.level
                report['level_distribution'][level] = report['level_distribution'].get(level, 0) + 1
                
                # Check quality
                issues = self.validate_course_quality(course)
                if not issues:
                    report['high_quality_courses'] += 1
                else:
                    for issue in issues:
                        report['quality_issues'][issue] = report['quality_issues'].get(issue, 0) + 1
            
            # Calculate averages
            for dept_stats in report['department_stats'].values():
                if dept_stats['count'] > 0:
                    dept_stats['avg_desc_length'] /= dept_stats['count']
            
            return report

def main():
    """Run the cleaning pipeline"""
    cleaner = CourseDataCleaner()
    
    print("🧹 Starting course data cleaning pipeline...")
    
    # Generate initial quality report
    print("\n📊 Initial Quality Report:")
    initial_report = cleaner.generate_quality_report()
    print(f"Total courses: {initial_report['total_courses']}")
    print(f"High quality courses: {initial_report['high_quality_courses']}")
    print("Top quality issues:")
    for issue, count in sorted(initial_report['quality_issues'].items(), 
                              key=lambda x: x[1], reverse=True)[:5]:
        print(f"  - {issue}: {count} courses")
    
    # Run cleaning
    print("\n🔧 Cleaning courses...")
    stats = cleaner.clean_all_courses()
    
    print("\n✅ Cleaning Results:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    
    # Generate final quality report
    print("\n📊 Final Quality Report:")
    final_report = cleaner.generate_quality_report()
    print(f"High quality courses: {final_report['high_quality_courses']} (was {initial_report['high_quality_courses']})")
    
    improvement = final_report['high_quality_courses'] - initial_report['high_quality_courses']
    print(f"Quality improvement: +{improvement} courses")

if __name__ == "__main__":
    main()