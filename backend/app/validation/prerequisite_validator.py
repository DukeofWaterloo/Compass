"""
Prerequisite validation system for course recommendations
"""

import re
from typing import List, Set, Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

class PrereqOperator(Enum):
    """Logical operators for prerequisites"""
    AND = "and"
    OR = "or"
    NOT = "not"

@dataclass
class PrerequisiteNode:
    """Tree node for prerequisite expressions"""
    operator: Optional[PrereqOperator] = None
    course_code: Optional[str] = None
    children: List['PrerequisiteNode'] = None
    min_grade: Optional[str] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []

@dataclass
class ValidationResult:
    """Result of prerequisite validation"""
    is_satisfied: bool
    missing_prereqs: List[str]
    warnings: List[str]
    grade_requirements: Dict[str, str]

class PrerequisiteParser:
    """Parses prerequisite strings into structured format"""
    
    def __init__(self):
        # Common course code pattern
        self.course_pattern = r'([A-Z]{2,5})\s*(\d{3}[A-Z]?)'
        
        # Grade requirement patterns
        self.grade_patterns = {
            r'minimum\s+(?:grade\s+)?(\d+)%': r'\1%',
            r'minimum\s+(?:of\s+)?(\d+)%': r'\1%',
            r'(\d+)%\s+or\s+higher': r'\1%',
            r'grade\s+of\s+([A-Z][+-]?)': r'\1',
        }
        
        # Logical operators
        self.and_keywords = ['and', '&', ',', ';']
        self.or_keywords = ['or', '/', 'either']
        
    def parse_prerequisites(self, prereq_string: str) -> Optional[PrerequisiteNode]:
        """Parse a prerequisite string into a tree structure"""
        if not prereq_string or prereq_string.lower() in ['none', 'n/a', '']:
            return None
            
        # Clean up the string
        prereq_string = self._clean_prereq_string(prereq_string)
        
        # Handle special cases
        if self._is_level_requirement(prereq_string):
            return self._parse_level_requirement(prereq_string)
        
        if self._is_program_requirement(prereq_string):
            return self._parse_program_requirement(prereq_string)
            
        # Parse complex expressions
        return self._parse_expression(prereq_string)
    
    def _clean_prereq_string(self, text: str) -> str:
        """Clean and normalize prerequisite string"""
        # Remove common prefixes
        text = re.sub(r'^(?:prereq:?\s*|prerequisite:?\s*)', '', text, flags=re.IGNORECASE)
        
        # Standardize course codes
        text = re.sub(r'([A-Z]{2,5})\s*(\d{3}[A-Z]?)', r'\1 \2', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _is_level_requirement(self, text: str) -> bool:
        """Check if this is a year/level requirement"""
        level_patterns = [
            r'\d+[A-Z]*\s+standing',
            r'year\s+\d+',
            r'\d+[A-Z]*\s+year',
            r'level\s+\d+[A-Z]*'
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in level_patterns)
    
    def _is_program_requirement(self, text: str) -> bool:
        """Check if this is a program enrollment requirement"""
        program_patterns = [
            r'enrolled?\s+in',
            r'admission\s+to',
            r'faculty\s+of',
            r'students?\s+in'
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in program_patterns)
    
    def _parse_level_requirement(self, text: str) -> PrerequisiteNode:
        """Parse year/level requirements"""
        # Extract level number
        level_match = re.search(r'(\d+)', text)
        level = level_match.group(1) if level_match else "1"
        
        return PrerequisiteNode(
            course_code=f"LEVEL_{level}",
            operator=None
        )
    
    def _parse_program_requirement(self, text: str) -> PrerequisiteNode:
        """Parse program enrollment requirements"""
        # Extract program/faculty name
        program_match = re.search(r'(?:enrolled?\s+in|admission\s+to|faculty\s+of|students?\s+in)\s+(.+)', text, re.IGNORECASE)
        program = program_match.group(1).strip() if program_match else "UNKNOWN"
        
        return PrerequisiteNode(
            course_code=f"PROGRAM_{program.upper()}",
            operator=None
        )
    
    def _parse_expression(self, text: str) -> PrerequisiteNode:
        """Parse complex prerequisite expressions"""
        # Find all course codes
        courses = re.findall(self.course_pattern, text)
        
        if not courses:
            return None
        
        if len(courses) == 1:
            # Single course requirement
            dept, num = courses[0]
            return PrerequisiteNode(course_code=f"{dept} {num}")
        
        # Multiple courses - determine logical relationship
        if self._contains_or_operator(text):
            # OR relationship
            root = PrerequisiteNode(operator=PrereqOperator.OR)
            for dept, num in courses:
                root.children.append(PrerequisiteNode(course_code=f"{dept} {num}"))
            return root
        else:
            # AND relationship (default)
            root = PrerequisiteNode(operator=PrereqOperator.AND)
            for dept, num in courses:
                root.children.append(PrerequisiteNode(course_code=f"{dept} {num}"))
            return root
    
    def _contains_or_operator(self, text: str) -> bool:
        """Check if text contains OR-type operators"""
        return any(keyword in text.lower() for keyword in self.or_keywords)

class PrerequisiteValidator:
    """Validates if a student meets course prerequisites"""
    
    def __init__(self):
        self.parser = PrerequisiteParser()
    
    def validate_prerequisites(self, 
                             course_prereqs: str,
                             completed_courses: List[str],
                             student_year: int = 1,
                             student_program: str = "") -> ValidationResult:
        """
        Validate if student meets prerequisites for a course
        
        Args:
            course_prereqs: Prerequisite string from course data
            completed_courses: List of course codes student has completed
            student_year: Student's current year (1-4)
            student_program: Student's program/faculty
            
        Returns:
            ValidationResult with satisfaction status and details
        """
        
        # Parse prerequisites
        prereq_tree = self.parser.parse_prerequisites(course_prereqs)
        
        if not prereq_tree:
            return ValidationResult(
                is_satisfied=True,
                missing_prereqs=[],
                warnings=[],
                grade_requirements={}
            )
        
        # Normalize completed courses
        completed_set = {self._normalize_course_code(code) for code in completed_courses}
        
        # Evaluate prerequisite tree
        is_satisfied, missing, warnings = self._evaluate_prereq_tree(
            prereq_tree, 
            completed_set, 
            student_year, 
            student_program
        )
        
        return ValidationResult(
            is_satisfied=is_satisfied,
            missing_prereqs=missing,
            warnings=warnings,
            grade_requirements={}
        )
    
    def _normalize_course_code(self, course_code: str) -> str:
        """Normalize course code format"""
        # Handle different formats: "CS135", "CS 135", "cs-135"
        course_code = re.sub(r'[^A-Z0-9]', ' ', course_code.upper())
        parts = course_code.split()
        if len(parts) >= 2:
            return f"{parts[0]} {parts[1]}"
        return course_code.strip()
    
    def _evaluate_prereq_tree(self, 
                             node: PrerequisiteNode,
                             completed: Set[str],
                             student_year: int,
                             student_program: str) -> Tuple[bool, List[str], List[str]]:
        """Recursively evaluate prerequisite tree"""
        
        if node.course_code:
            # Leaf node - check specific requirement
            return self._check_single_requirement(
                node.course_code, 
                completed, 
                student_year, 
                student_program
            )
        
        if not node.children:
            return True, [], []
        
        # Evaluate children
        child_results = []
        all_missing = []
        all_warnings = []
        
        for child in node.children:
            satisfied, missing, warnings = self._evaluate_prereq_tree(
                child, completed, student_year, student_program
            )
            child_results.append(satisfied)
            all_missing.extend(missing)
            all_warnings.extend(warnings)
        
        # Apply logical operator
        if node.operator == PrereqOperator.AND:
            is_satisfied = all(child_results)
            final_missing = all_missing if not is_satisfied else []
        elif node.operator == PrereqOperator.OR:
            is_satisfied = any(child_results)
            final_missing = all_missing if not is_satisfied else []
        else:
            # Default to AND
            is_satisfied = all(child_results)
            final_missing = all_missing if not is_satisfied else []
        
        return is_satisfied, final_missing, all_warnings
    
    def _check_single_requirement(self, 
                                 requirement: str,
                                 completed: Set[str],
                                 student_year: int,
                                 student_program: str) -> Tuple[bool, List[str], List[str]]:
        """Check a single prerequisite requirement"""
        
        # Handle special requirements
        if requirement.startswith("LEVEL_"):
            required_level = int(requirement.split("_")[1])
            is_satisfied = student_year >= required_level
            missing = [] if is_satisfied else [f"Year {required_level} standing"]
            return is_satisfied, missing, []
        
        if requirement.startswith("PROGRAM_"):
            required_program = requirement.split("_", 1)[1]
            # Simple program matching (can be enhanced)
            is_satisfied = required_program.lower() in student_program.lower()
            missing = [] if is_satisfied else [f"Enrollment in {required_program}"]
            return is_satisfied, missing, []
        
        # Regular course requirement
        normalized_req = self._normalize_course_code(requirement)
        is_satisfied = normalized_req in completed
        missing = [] if is_satisfied else [normalized_req]
        
        return is_satisfied, missing, []
    
    def get_course_difficulty_score(self, course_code: str, prerequisites: str) -> float:
        """
        Calculate a difficulty score based on prerequisites
        
        Returns:
            Float between 0.0 (easiest) and 1.0 (hardest)
        """
        if not prerequisites or prerequisites.lower() in ['none', 'n/a']:
            return 0.1  # Very easy
        
        # Parse prerequisites to count complexity
        prereq_tree = self.parser.parse_prerequisites(prerequisites)
        if not prereq_tree:
            return 0.1
        
        # Count prerequisite courses
        course_count = self._count_prerequisite_courses(prereq_tree)
        
        # Extract course level
        level_match = re.search(r'(\d)', course_code)
        course_level = int(level_match.group(1)) if level_match else 1
        
        # Calculate difficulty
        base_difficulty = (course_level - 1) / 4  # 0.0 to 0.75 based on level
        prereq_difficulty = min(course_count / 10, 0.3)  # 0.0 to 0.3 based on prereqs
        
        return min(base_difficulty + prereq_difficulty, 1.0)
    
    def _count_prerequisite_courses(self, node: PrerequisiteNode) -> int:
        """Count the number of course prerequisites"""
        if node.course_code and not node.course_code.startswith(("LEVEL_", "PROGRAM_")):
            return 1
        
        return sum(self._count_prerequisite_courses(child) for child in node.children)
    
    def suggest_prerequisite_path(self, 
                                target_course: str,
                                target_prereqs: str,
                                completed_courses: List[str],
                                available_courses: List[Dict]) -> List[str]:
        """
        Suggest a path of courses to take to meet prerequisites
        
        Args:
            target_course: The course the student wants to take
            target_prereqs: Prerequisites for the target course
            completed_courses: Courses already completed
            available_courses: All available courses with their prerequisites
            
        Returns:
            List of course codes to take in order
        """
        
        # Validate current prerequisites
        validation = self.validate_prerequisites(target_prereqs, completed_courses)
        
        if validation.is_satisfied:
            return []  # No additional courses needed
        
        # Find courses that would satisfy missing prerequisites
        suggestion_path = []
        remaining_missing = validation.missing_prereqs.copy()
        
        # Simple approach: suggest missing courses directly
        for missing in remaining_missing:
            if not missing.startswith(("LEVEL_", "PROGRAM_")):
                suggestion_path.append(missing)
        
        return suggestion_path