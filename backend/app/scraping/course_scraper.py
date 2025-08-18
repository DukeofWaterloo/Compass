"""
Enhanced UWaterloo course catalog scraper
"""

import requests
from bs4 import BeautifulSoup
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CourseData:
    """Raw course data from scraping"""
    code: str
    title: str
    description: str
    credits: float
    course_id: Optional[str] = None
    course_type: Optional[str] = None  # PRJ, LEC, LAB, etc.
    prerequisites: Optional[str] = None
    corequisites: Optional[str] = None
    antirequisites: Optional[str] = None
    terms_offered: List[str] = None
    notes: Optional[str] = None
    department: str = ""
    level: int = 0
    url: str = ""

    def __post_init__(self):
        if self.terms_offered is None:
            self.terms_offered = []
        
        # Extract department and level from code
        if self.code:
            parts = self.code.split()
            if len(parts) >= 2:
                self.department = parts[0]
                # Extract numeric part for level
                number_match = re.search(r'(\d+)', parts[1])
                if number_match:
                    self.level = int(number_match.group(1)[0]) * 100  # 135 -> 100, 240 -> 200

class UWaterlooCourseScraperError(Exception):
    """Custom exception for scraper errors"""
    pass

class UWaterlooCourseScraper:
    """Enhanced scraper for UWaterloo course catalog"""
    
    BASE_URL = "https://ucalendar.uwaterloo.ca/2324/COURSE/"
    RATE_LIMIT_DELAY = 1.0  # seconds between requests
    
    # Department URL patterns - ALL available UWaterloo departments
    DEPARTMENT_URLS = {
        'ACTSC': 'course-ACTSC.html',
        'AE': 'course-AE.html',
        'AFM': 'course-AFM.html',
        'AMATH': 'course-AMATH.html',
        'ANTH': 'course-ANTH.html',
        'APPLS': 'course-APPLS.html',
        'ARABIC': 'course-ARABIC.html',
        'ARBUS': 'course-ARBUS.html',
        'ARCH': 'course-ARCH.html',
        'ARTS': 'course-ARTS.html',
        'ASL': 'course-ASL.html',
        'AVIA': 'course-AVIA.html',
        'BASE': 'course-BASE.html',
        'BET': 'course-BET.html',
        'BIOL': 'course-BIOL.html',
        'BLKST': 'course-BLKST.html',
        'BME': 'course-BME.html',
        'BUS': 'course-BUS.html',
        'CDNST': 'course-CDNST.html',
        'CFM': 'course-CFM.html',
        'CHE': 'course-CHE.html',
        'CHEM': 'course-CHEM.html',
        'CHINA': 'course-CHINA.html',
        'CI': 'course-CI.html',
        'CIVE': 'course-CIVE.html',
        'CLAS': 'course-CLAS.html',
        'CMW': 'course-CMW.html',
        'CO': 'course-CO.html',
        'COGSCI': 'course-COGSCI.html',
        'COMM': 'course-COMM.html',
        'COMMST': 'course-COMMST.html',
        'CROAT': 'course-CROAT.html',
        'CS': 'course-CS.html',
        'DAC': 'course-DAC.html',
        'DUTCH': 'course-DUTCH.html',
        'EARTH': 'course-EARTH.html',
        'EASIA': 'course-EASIA.html',
        'ECE': 'course-ECE.html',
        'ECON': 'course-ECON.html',
        'EMLS': 'course-EMLS.html',
        'ENBUS': 'course-ENBUS.html',
        'ENGL': 'course-ENGL.html',
        'ENVE': 'course-ENVE.html',
        'ENVS': 'course-ENVS.html',
        'ERS': 'course-ERS.html',
        'FINE': 'course-FINE.html',
        'FR': 'course-FR.html',
        'GBDA': 'course-GBDA.html',
        'GENE': 'course-GENE.html',
        'GEOE': 'course-GEOE.html',
        'GEOG': 'course-GEOG.html',
        'GER': 'course-GER.html',
        'GERON': 'course-GERON.html',
        'GRK': 'course-GRK.html',
        'GSJ': 'course-GSJ.html',
        'HEALTH': 'course-HEALTH.html',
        'HHUM': 'course-HHUM.html',
        'HIST': 'course-HIST.html',
        'HLTH': 'course-HLTH.html',
        'HRM': 'course-HRM.html',
        'HRTS': 'course-HRTS.html',
        'HUMSC': 'course-HUMSC.html',
        'INDENT': 'course-INDENT.html',
        'INDEV': 'course-INDEV.html',
        'INDG': 'course-INDG.html',
        'INTEG': 'course-INTEG.html',
        'INTST': 'course-INTST.html',
        'ITAL': 'course-ITAL.html',
        'ITALST': 'course-ITALST.html',
        'JAPAN': 'course-JAPAN.html',
        'JS': 'course-JS.html',
        'KIN': 'course-KIN.html',
        'KOREA': 'course-KOREA.html',
        'LAT': 'course-LAT.html',
        'LS': 'course-LS.html',
        'MATBUS': 'course-MATBUS.html',
        'MATH': 'course-MATH.html',
        'ME': 'course-ME.html',
        'MEDVL': 'course-MEDVL.html',
        'MGMT': 'course-MGMT.html',
        'MNS': 'course-MNS.html',
        'MTE': 'course-MTE.html',
        'MTHEL': 'course-MTHEL.html',
        'MUSIC': 'course-MUSIC.html',
        'NE': 'course-NE.html',
        'OPTOM': 'course-OPTOM.html',
        'PACS': 'course-PACS.html',
        'PD': 'course-PD.html',
        'PDARCH': 'course-PDARCH.html',
        'PDPHRM': 'course-PDPHRM.html',
        'PHARM': 'course-PHARM.html',
        'PHIL': 'course-PHIL.html',
        'PHYS': 'course-PHYS.html',
        'PLAN': 'course-PLAN.html',
        'PMATH': 'course-PMATH.html',
        'PSCI': 'course-PSCI.html',
        'PSYCH': 'course-PSYCH.html',
        'REC': 'course-REC.html',
        'REES': 'course-REES.html',
        'RS': 'course-RS.html',
        'RUSS': 'course-RUSS.html',
        'SCBUS': 'course-SCBUS.html',
        'SCI': 'course-SCI.html',
        'SDS': 'course-SDS.html',
        'SE': 'course-SE.html',
        'SFM': 'course-SFM.html',
        'SI': 'course-SI.html',
        'SMF': 'course-SMF.html',
        'SOC': 'course-SOC.html',
        'SOCWK': 'course-SOCWK.html',
        'SPAN': 'course-SPAN.html',
        'STAT': 'course-STAT.html',
        'STV': 'course-STV.html',
        'SWREN': 'course-SWREN.html',
        'SYDE': 'course-SYDE.html',
        'THPERF': 'course-THPERF.html',
        'UNIV': 'course-UNIV.html',
        'VCULT': 'course-VCULT.html',
        'WKRPT': 'course-WKRPT.html',
    }
    
    def __init__(self, rate_limit: float = 1.0):
        self.rate_limit_delay = rate_limit
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; CompassBot/1.0; +https://github.com/DukeofWaterloo/Compass)'
        })
    
    def extract_courses_from_department(self, department: str) -> List[CourseData]:
        """Extract all courses from a specific department"""
        if department not in self.DEPARTMENT_URLS:
            raise UWaterlooCourseScraperError(f"Unknown department: {department}")
        
        url = urljoin(self.BASE_URL, self.DEPARTMENT_URLS[department])
        logger.info(f"Scraping {department} courses from {url}")
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            # Add rate limiting
            time.sleep(self.rate_limit_delay)
            
            return self._parse_course_page(response.text, url, department)
            
        except requests.RequestException as e:
            raise UWaterlooCourseScraperError(f"Failed to fetch {department} courses: {e}")
    
    def _parse_course_page(self, html_content: str, url: str, department: str) -> List[CourseData]:
        """Parse course data from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        courses = []
        
        # Find course entries by looking for specific patterns
        # Each course starts with a code like "ECE 101A PRJ 0.13"
        text_content = soup.get_text()
        
        # Split by course pattern and parse each section
        course_pattern = r'([A-Z]+\s+\d+[A-Z]?)\s+([A-Z,]+)\s+([\d.]+)\s*Course ID:\s*(\d+)'
        course_matches = re.finditer(course_pattern, text_content)
        
        for match in course_matches:
            course_code = match.group(1)
            course_type = match.group(2) 
            credits = float(match.group(3))
            course_id = match.group(4)
            
            # Extract the text section for this course
            start_pos = match.start()
            # Find the next course or end of text
            next_match = None
            for next_course in re.finditer(course_pattern, text_content[match.end():]):
                next_match = next_course
                break
            
            if next_match:
                end_pos = match.end() + next_match.start()
            else:
                end_pos = len(text_content)
            
            course_text = text_content[start_pos:end_pos]
            
            # Extract course details from this text section
            course_data = self._extract_course_details(
                course_text, course_code, course_type, credits, course_id, url, department
            )
            if course_data:
                courses.append(course_data)
                logger.debug(f"Extracted course: {course_code}")
        
        logger.info(f"Successfully extracted {len(courses)} courses from {department}")
        return courses
    
    def _extract_course_details(self, text: str, code: str, course_type: str, credits: float, course_id: str, url: str, department: str) -> Optional[CourseData]:
        """Extract detailed course information from text block"""
        try:
            # Extract title - text after course ID until description starts
            title_pattern = rf'Course ID:\s*{course_id}\s*([^\n]+?)(?:\n|[A-Z][a-z])'
            title_match = re.search(title_pattern, text)
            title = title_match.group(1).strip() if title_match else "Unknown Title"
            
            # Extract description - main content between title and prerequisites
            desc_start = text.find(title) + len(title) if title != "Unknown Title" else text.find(course_id) + len(course_id)
            desc_end = len(text)
            
            # Find where metadata starts (Prereq, Offered, Note, etc.)
            for pattern in [r'Prereq:', r'Coreq:', r'Antireq:', r'\[Note:', r'Offered:']:
                match = re.search(pattern, text[desc_start:])
                if match:
                    desc_end = min(desc_end, desc_start + match.start())
            
            description = text[desc_start:desc_end].strip()
            
            # Extract prerequisites
            prereq_match = re.search(r'Prereq:\s*([^.]*?)(?:\s*Coreq:|\s*Antireq:|\s*\[|$)', text, re.DOTALL)
            prerequisites = prereq_match.group(1).strip() if prereq_match else None
            
            # Extract corequisites  
            coreq_match = re.search(r'Coreq:\s*([^.]*?)(?:\s*Antireq:|\s*\[|$)', text, re.DOTALL)
            corequisites = coreq_match.group(1).strip() if coreq_match else None
            
            # Extract antirequisites
            antireq_match = re.search(r'Antireq:\s*([^.]*?)(?:\s*\[|$)', text, re.DOTALL)
            antirequisites = antireq_match.group(1).strip() if antireq_match else None
            
            # Extract terms offered
            terms_match = re.search(r'Offered:\s*([FWSJ, ]+)', text)
            terms_offered = []
            if terms_match:
                term_str = terms_match.group(1)
                if 'F' in term_str:
                    terms_offered.append('Fall')
                if 'W' in term_str:
                    terms_offered.append('Winter')
                if 'S' in term_str:
                    terms_offered.append('Spring')
            
            # Extract notes
            notes_match = re.search(r'\[Note:\s*([^\]]+)\]', text)
            notes = notes_match.group(1).strip() if notes_match else None
            
            return CourseData(
                code=code,
                title=title,
                description=description,
                credits=credits,
                course_id=course_id,
                course_type=course_type,
                prerequisites=prerequisites,
                corequisites=corequisites,
                antirequisites=antirequisites,
                terms_offered=terms_offered,
                notes=notes,
                url=url
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse course {code}: {e}")
            return None
    
    def scrape_all_departments(self) -> Dict[str, List[CourseData]]:
        """Scrape courses from all departments"""
        all_courses = {}
        
        for department in self.DEPARTMENT_URLS.keys():
            try:
                courses = self.extract_courses_from_department(department)
                all_courses[department] = courses
                logger.info(f"Scraped {len(courses)} courses from {department}")
            except UWaterlooCourseScraperError as e:
                logger.error(f"Failed to scrape {department}: {e}")
                all_courses[department] = []
        
        total_courses = sum(len(courses) for courses in all_courses.values())
        logger.info(f"Total courses scraped: {total_courses}")
        
        return all_courses
    
    def validate_course_data(self, course: CourseData) -> Tuple[bool, List[str]]:
        """Validate course data and return issues"""
        issues = []
        
        if not course.code or not course.code.strip():
            issues.append("Missing course code")
        
        if not course.title or course.title == "Unknown Title":
            issues.append("Missing or unknown course title")
        
        if not course.description or len(course.description.strip()) < 10:
            issues.append("Missing or too short course description")
        
        if course.credits < 0:
            issues.append("Invalid credit value")
        
        if not course.department:
            issues.append("Missing department")
        
        return len(issues) == 0, issues

# Test function
def test_enhanced_scraper():
    """Test the enhanced scraper"""
    scraper = UWaterlooCourseScraper()
    
    # Test single department
    try:
        ece_courses = scraper.extract_courses_from_department('ECE')
        print(f"Found {len(ece_courses)} ECE courses")
        
        if ece_courses:
            sample_course = ece_courses[0]
            print(f"\nSample course: {sample_course.code}")
            print(f"Title: {sample_course.title}")
            print(f"Credits: {sample_course.credits}")
            print(f"Prerequisites: {sample_course.prerequisites}")
            print(f"Terms: {sample_course.terms_offered}")
            
            # Validate the course
            is_valid, issues = scraper.validate_course_data(sample_course)
            print(f"Valid: {is_valid}")
            if issues:
                print(f"Issues: {issues}")
    
    except Exception as e:
        print(f"Error testing scraper: {e}")

if __name__ == "__main__":
    test_enhanced_scraper()