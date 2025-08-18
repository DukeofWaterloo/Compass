"""
Enhanced data validation for course scraping
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from app.scraping.course_scraper import CourseData
import logging

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of course data validation"""
    is_valid: bool
    issues: List[str]
    warnings: List[str]
    corrected_data: Optional[CourseData] = None

class CourseDataValidator:
    """Enhanced validator for course data"""
    
    # Known department codes - ALL UWaterloo departments
    VALID_DEPARTMENTS = {
        'ACTSC', 'AE', 'AFM', 'AMATH', 'ANTH', 'APPLS', 'ARABIC', 'ARBUS', 'ARCH', 'ARTS', 
        'ASL', 'AVIA', 'BASE', 'BET', 'BIOL', 'BLKST', 'BME', 'BUS', 'CDNST', 'CFM', 
        'CHE', 'CHEM', 'CHINA', 'CI', 'CIVE', 'CLAS', 'CMW', 'CO', 'COGSCI', 'COMM', 
        'COMMST', 'CROAT', 'CS', 'DAC', 'DUTCH', 'EARTH', 'EASIA', 'ECE', 'ECON', 'EMLS', 
        'ENBUS', 'ENGL', 'ENVE', 'ENVS', 'ERS', 'FINE', 'FR', 'GBDA', 'GENE', 'GEOE', 
        'GEOG', 'GER', 'GERON', 'GRK', 'GSJ', 'HEALTH', 'HHUM', 'HIST', 'HLTH', 'HRM', 
        'HRTS', 'HUMSC', 'INDENT', 'INDEV', 'INDG', 'INTEG', 'INTST', 'ITAL', 'ITALST', 
        'JAPAN', 'JS', 'KIN', 'KOREA', 'LAT', 'LS', 'MATBUS', 'MATH', 'ME', 'MEDVL', 
        'MGMT', 'MNS', 'MTE', 'MTHEL', 'MUSIC', 'NE', 'OPTOM', 'PACS', 'PD', 'PDARCH', 
        'PDPHRM', 'PHARM', 'PHIL', 'PHYS', 'PLAN', 'PMATH', 'PSCI', 'PSYCH', 'REC', 
        'REES', 'RS', 'RUSS', 'SCBUS', 'SCI', 'SDS', 'SE', 'SFM', 'SI', 'SMF', 'SOC', 
        'SOCWK', 'SPAN', 'STAT', 'STV', 'SWREN', 'SYDE', 'THPERF', 'UNIV', 'VCULT', 'WKRPT'
    }
    
    # Valid course types
    VALID_COURSE_TYPES = {
        'LEC', 'LAB', 'PRJ', 'SEM', 'TUT', 'TST', 'WRK', 'STU', 'IND', 'FLD'
    }
    
    # Valid credit ranges
    MIN_CREDITS = 0.0
    MAX_CREDITS = 2.0
    
    # Valid course code pattern
    COURSE_CODE_PATTERN = re.compile(r'^[A-Z]{2,8}\s+\d{1,4}[A-Z]?$')
    
    def validate_course(self, course: CourseData) -> ValidationResult:
        """Comprehensive validation of a course"""
        issues = []
        warnings = []
        corrected_data = None
        
        # Validate course code
        code_issues = self._validate_course_code(course.code)
        issues.extend(code_issues)
        
        # Validate title
        title_issues = self._validate_title(course.title)
        issues.extend(title_issues)
        
        # Validate description
        desc_issues, desc_warnings = self._validate_description(course.description)
        issues.extend(desc_issues)
        warnings.extend(desc_warnings)
        
        # Validate credits
        credit_issues = self._validate_credits(course.credits)
        issues.extend(credit_issues)
        
        # Validate department
        dept_issues, corrected_dept = self._validate_department(course.department, course.code)
        issues.extend(dept_issues)
        
        # Validate course type
        type_warnings = self._validate_course_type(course.course_type)
        warnings.extend(type_warnings)
        
        # Validate level
        level_issues, corrected_level = self._validate_level(course.level, course.code)
        issues.extend(level_issues)
        
        # Validate prerequisites format
        prereq_warnings = self._validate_prerequisites(course.prerequisites)
        warnings.extend(prereq_warnings)
        
        # Validate terms offered
        terms_warnings = self._validate_terms(course.terms_offered)
        warnings.extend(terms_warnings)
        
        # Create corrected data if needed
        if corrected_dept or corrected_level:
            corrected_data = CourseData(
                code=course.code,
                title=course.title,
                description=course.description,
                credits=course.credits,
                course_id=course.course_id,
                course_type=course.course_type,
                prerequisites=course.prerequisites,
                corequisites=course.corequisites,
                antirequisites=course.antirequisites,
                terms_offered=course.terms_offered,
                notes=course.notes,
                department=corrected_dept or course.department,
                level=corrected_level or course.level,
                url=course.url
            )
        
        is_valid = len(issues) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            warnings=warnings,
            corrected_data=corrected_data
        )
    
    def _validate_course_code(self, code: str) -> List[str]:
        """Validate course code format"""
        issues = []
        
        if not code or not code.strip():
            issues.append("Course code is missing")
            return issues
        
        code = code.strip()
        
        if not self.COURSE_CODE_PATTERN.match(code):
            issues.append(f"Invalid course code format: {code}")
        
        return issues
    
    def _validate_title(self, title: str) -> List[str]:
        """Validate course title"""
        issues = []
        
        if not title or not title.strip():
            issues.append("Course title is missing")
            return issues
        
        title = title.strip()
        
        if len(title) < 3:
            issues.append("Course title is too short")
        
        if len(title) > 200:
            issues.append("Course title is too long")
        
        if title == "Unknown Title":
            issues.append("Course title was not properly extracted")
        
        return issues
    
    def _validate_description(self, description: str) -> Tuple[List[str], List[str]]:
        """Validate course description"""
        issues = []
        warnings = []
        
        if not description or not description.strip():
            issues.append("Course description is missing")
            return issues, warnings
        
        description = description.strip()
        
        if len(description) < 20:
            warnings.append("Course description is very short")
        
        if len(description) > 5000:
            warnings.append("Course description is unusually long")
        
        # Check for common extraction issues
        if "Course ID:" in description:
            warnings.append("Description contains metadata that should be cleaned")
        
        if description.count('\n') > 10:
            warnings.append("Description contains many line breaks")
        
        return issues, warnings
    
    def _validate_credits(self, credits: float) -> List[str]:
        """Validate course credits"""
        issues = []
        
        if credits < self.MIN_CREDITS or credits > self.MAX_CREDITS:
            issues.append(f"Invalid credit value: {credits}")
        
        # Check for common valid credit values
        valid_credits = {0.0, 0.13, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5}
        if credits not in valid_credits:
            issues.append(f"Unusual credit value: {credits}")
        
        return issues
    
    def _validate_department(self, department: str, code: str) -> Tuple[List[str], Optional[str]]:
        """Validate department code and extract from course code if needed"""
        issues = []
        corrected_dept = None
        
        # Extract department from course code if department is missing
        if not department or not department.strip():
            if code:
                dept_match = re.match(r'^([A-Z]+)', code.strip())
                if dept_match:
                    corrected_dept = dept_match.group(1)
                    if corrected_dept not in self.VALID_DEPARTMENTS:
                        issues.append(f"Unknown department code: {corrected_dept}")
                else:
                    issues.append("Cannot extract department from course code")
            else:
                issues.append("Department is missing and cannot be extracted")
        else:
            department = department.strip().upper()
            if department not in self.VALID_DEPARTMENTS:
                issues.append(f"Unknown department code: {department}")
        
        return issues, corrected_dept
    
    def _validate_course_type(self, course_type: str) -> List[str]:
        """Validate course type"""
        warnings = []
        
        if not course_type:
            warnings.append("Course type is missing")
            return warnings
        
        # Split by comma for multiple types
        types = [t.strip() for t in course_type.split(',')]
        
        for t in types:
            if t not in self.VALID_COURSE_TYPES:
                warnings.append(f"Unknown course type: {t}")
        
        return warnings
    
    def _validate_level(self, level: int, code: str) -> Tuple[List[str], Optional[int]]:
        """Validate course level and extract from code if needed"""
        issues = []
        corrected_level = None
        
        # Extract level from course code if level is missing or wrong
        if code:
            number_match = re.search(r'(\d+)', code)
            if number_match:
                number = number_match.group(1)
                expected_level = int(number[0]) * 100
                
                if level != expected_level:
                    corrected_level = expected_level
                    if level == 0:
                        pass  # Missing level, will be corrected
                    else:
                        issues.append(f"Level mismatch: {level} vs expected {expected_level}")
            else:
                issues.append("Cannot extract level from course code")
        
        if level not in {0, 100, 200, 300, 400, 500, 600, 700, 800, 900}:
            issues.append(f"Invalid course level: {level}")
        
        return issues, corrected_level
    
    def _validate_prerequisites(self, prerequisites: Optional[str]) -> List[str]:
        """Validate prerequisite format"""
        warnings = []
        
        if not prerequisites:
            return warnings
        
        prereq = prerequisites.strip()
        
        # Check for common issues
        if len(prereq) > 1000:
            warnings.append("Prerequisites text is very long")
        
        if "Course ID:" in prereq:
            warnings.append("Prerequisites contain metadata")
        
        return warnings
    
    def _validate_terms(self, terms: List[str]) -> List[str]:
        """Validate terms offered"""
        warnings = []
        
        if not terms:
            warnings.append("No terms offered specified")
            return warnings
        
        valid_terms = {'Fall', 'Winter', 'Spring', 'Summer'}
        
        for term in terms:
            if term not in valid_terms:
                warnings.append(f"Unknown term: {term}")
        
        return warnings

class BatchValidator:
    """Validator for batches of courses"""
    
    def __init__(self):
        self.validator = CourseDataValidator()
    
    def validate_batch(self, courses: List[CourseData]) -> Dict[str, any]:
        """Validate a batch of courses and return summary"""
        results = {
            'total_courses': len(courses),
            'valid_courses': 0,
            'invalid_courses': 0,
            'courses_with_warnings': 0,
            'corrected_courses': 0,
            'detailed_results': [],
            'summary_issues': {},
            'summary_warnings': {}
        }
        
        for course in courses:
            validation_result = self.validator.validate_course(course)
            
            # Count results
            if validation_result.is_valid:
                results['valid_courses'] += 1
            else:
                results['invalid_courses'] += 1
            
            if validation_result.warnings:
                results['courses_with_warnings'] += 1
            
            if validation_result.corrected_data:
                results['corrected_courses'] += 1
            
            # Track issue patterns
            for issue in validation_result.issues:
                results['summary_issues'][issue] = results['summary_issues'].get(issue, 0) + 1
            
            for warning in validation_result.warnings:
                results['summary_warnings'][warning] = results['summary_warnings'].get(warning, 0) + 1
            
            # Store detailed result
            results['detailed_results'].append({
                'course_code': course.code,
                'is_valid': validation_result.is_valid,
                'issues': validation_result.issues,
                'warnings': validation_result.warnings,
                'has_corrections': validation_result.corrected_data is not None
            })
        
        return results
    
    def get_corrected_courses(self, courses: List[CourseData]) -> List[CourseData]:
        """Get corrected versions of courses"""
        corrected = []
        
        for course in courses:
            validation_result = self.validator.validate_course(course)
            if validation_result.corrected_data:
                corrected.append(validation_result.corrected_data)
            else:
                corrected.append(course)
        
        return corrected

# Test function
def test_validation():
    """Test the validation system"""
    from app.scraping.course_scraper import UWaterlooCourseScraper
    
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