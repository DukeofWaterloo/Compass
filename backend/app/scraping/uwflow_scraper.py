"""
UWFlow data scraper for course ratings and student feedback
"""

import requests
import json
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

@dataclass
class UWFlowCourseData:
    """Data structure for UWFlow course information"""
    course_code: str
    rating: Optional[float] = None
    difficulty: Optional[float] = None
    workload: Optional[float] = None
    usefulness: Optional[float] = None
    num_ratings: int = 0
    review_count: int = 0
    liked_percentage: Optional[float] = None
    professor_ratings: List[Dict] = None
    recent_reviews: List[Dict] = None
    terms_offered_recently: List[str] = None
    
    def __post_init__(self):
        if self.professor_ratings is None:
            self.professor_ratings = []
        if self.recent_reviews is None:
            self.recent_reviews = []
        if self.terms_offered_recently is None:
            self.terms_offered_recently = []

class UWFlowScraper:
    """Scraper for UWFlow course data"""
    
    def __init__(self, rate_limit: float = 1.0):
        self.base_url = "https://www.uwflow.com"
        self.session = requests.Session()
        self.rate_limit = rate_limit
        
        # Set headers to mimic a browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        logger.info("Initialized UWFlow scraper")
    
    def get_course_data(self, course_code: str) -> Optional[UWFlowCourseData]:
        """
        Get course data from UWFlow
        
        Args:
            course_code: Course code like "ECE140" or "CS135"
            
        Returns:
            UWFlowCourseData object or None if not found
        """
        # Clean course code (remove spaces, make lowercase)
        clean_code = course_code.replace(" ", "").lower()
        
        # Try multiple URL formats
        url_patterns = [
            f"{self.base_url}/course/{clean_code}",
            f"{self.base_url}/course/{course_code.replace(' ', '').lower()}",
            f"{self.base_url}/course/{course_code.replace(' ', '')}"
        ]
        
        for url in url_patterns:
            try:
                data = self._scrape_course_page(url, course_code)
                if data:
                    return data
            except Exception as e:
                logger.debug(f"Failed to scrape {url}: {e}")
                continue
        
        logger.warning(f"Could not find UWFlow data for course {course_code}")
        return None
    
    def _scrape_course_page(self, url: str, course_code: str) -> Optional[UWFlowCourseData]:
        """Scrape a single course page from UWFlow"""
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Rate limiting
            time.sleep(self.rate_limit)
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Initialize course data
            course_data = UWFlowCourseData(course_code=course_code)
            
            # Try to extract data from various sources
            self._extract_from_meta_tags(soup, course_data)
            self._extract_from_json_ld(soup, course_data)
            self._extract_from_page_content(soup, course_data)
            self._extract_from_script_tags(soup, course_data)
            
            # Only return if we found some useful data
            if course_data.rating or course_data.difficulty or course_data.review_count > 0:
                logger.info(f"Successfully scraped UWFlow data for {course_code}")
                return course_data
            else:
                logger.debug(f"No useful data found for {course_code} at {url}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Network error scraping {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
    
    def _extract_from_meta_tags(self, soup: BeautifulSoup, course_data: UWFlowCourseData):
        """Extract data from meta tags"""
        
        # Look for Open Graph and other meta tags
        meta_tags = soup.find_all('meta')
        
        for tag in meta_tags:
            content = tag.get('content', '')
            name = tag.get('name', '').lower()
            property_name = tag.get('property', '').lower()
            
            # Extract rating information
            if 'rating' in name or 'rating' in property_name:
                try:
                    rating = float(re.search(r'(\d+\.?\d*)', content).group(1))
                    course_data.rating = rating
                except (AttributeError, ValueError):
                    pass
    
    def _extract_from_json_ld(self, soup: BeautifulSoup, course_data: UWFlowCourseData):
        """Extract data from JSON-LD structured data"""
        
        json_scripts = soup.find_all('script', type='application/ld+json')
        
        for script in json_scripts:
            try:
                data = json.loads(script.string)
                
                if isinstance(data, dict):
                    # Look for course or educational content
                    if data.get('@type') in ['Course', 'EducationalOrganization']:
                        # Extract any available ratings
                        if 'aggregateRating' in data:
                            rating_info = data['aggregateRating']
                            course_data.rating = float(rating_info.get('ratingValue', 0))
                            course_data.num_ratings = int(rating_info.get('ratingCount', 0))
                        
                        # Extract other metrics if available
                        if 'review' in data:
                            course_data.review_count = len(data['review'])
                
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.debug(f"Error parsing JSON-LD: {e}")
                continue
    
    def _extract_from_page_content(self, soup: BeautifulSoup, course_data: UWFlowCourseData):
        """Extract data from visible page content"""
        
        # Look for common rating patterns in text
        text = soup.get_text()
        
        # Extract rating (e.g., "4.2/5", "Rating: 4.2")
        rating_patterns = [
            r'(?:rating:?\s*)?(\d+\.?\d*)\s*/\s*5',
            r'(?:rating:?\s*)(\d+\.?\d*)\s*out\s*of\s*5',
            r'(\d+\.?\d*)\s*(?:star|★)',
        ]
        
        for pattern in rating_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    course_data.rating = float(match.group(1))
                    break
                except ValueError:
                    continue
        
        # Extract difficulty (e.g., "Difficulty: 3.5")
        difficulty_patterns = [
            r'difficulty:?\s*(\d+\.?\d*)',
            r'hard(?:ness)?:?\s*(\d+\.?\d*)',
        ]
        
        for pattern in difficulty_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    course_data.difficulty = float(match.group(1))
                    break
                except ValueError:
                    continue
        
        # Extract workload information
        workload_patterns = [
            r'workload:?\s*(\d+\.?\d*)',
            r'hours?\s*per\s*week:?\s*(\d+\.?\d*)',
        ]
        
        for pattern in workload_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    course_data.workload = float(match.group(1))
                    break
                except ValueError:
                    continue
        
        # Count reviews mentioned
        review_mentions = re.findall(r'(\d+)\s*reviews?', text, re.IGNORECASE)
        if review_mentions:
            try:
                course_data.review_count = max(int(r) for r in review_mentions)
            except ValueError:
                pass
    
    def _extract_from_script_tags(self, soup: BeautifulSoup, course_data: UWFlowCourseData):
        """Extract data from JavaScript variables or inline scripts"""
        
        scripts = soup.find_all('script')
        
        for script in scripts:
            if not script.string:
                continue
            
            script_content = script.string
            
            # Look for common JavaScript patterns that might contain course data
            patterns = [
                r'rating["\']:\s*(\d+\.?\d*)',
                r'difficulty["\']:\s*(\d+\.?\d*)',
                r'workload["\']:\s*(\d+\.?\d*)',
                r'usefulness["\']:\s*(\d+\.?\d*)',
                r'reviewCount["\']:\s*(\d+)',
                r'numRatings["\']:\s*(\d+)',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, script_content, re.IGNORECASE)
                if matches:
                    try:
                        value = float(matches[0])
                        if 'rating' in pattern:
                            course_data.rating = value
                        elif 'difficulty' in pattern:
                            course_data.difficulty = value
                        elif 'workload' in pattern:
                            course_data.workload = value
                        elif 'usefulness' in pattern:
                            course_data.usefulness = value
                        elif 'reviewcount' in pattern.lower():
                            course_data.review_count = int(value)
                        elif 'numratings' in pattern.lower():
                            course_data.num_ratings = int(value)
                    except ValueError:
                        continue
    
    def get_multiple_courses(self, course_codes: List[str]) -> Dict[str, UWFlowCourseData]:
        """
        Get UWFlow data for multiple courses
        
        Args:
            course_codes: List of course codes
            
        Returns:
            Dictionary mapping course codes to UWFlowCourseData
        """
        results = {}
        
        logger.info(f"Fetching UWFlow data for {len(course_codes)} courses...")
        
        for i, course_code in enumerate(course_codes):
            logger.debug(f"Processing course {i+1}/{len(course_codes)}: {course_code}")
            
            course_data = self.get_course_data(course_code)
            if course_data:
                results[course_code] = course_data
            
            # Rate limiting between requests
            if i < len(course_codes) - 1:
                time.sleep(self.rate_limit)
        
        logger.info(f"Successfully retrieved UWFlow data for {len(results)}/{len(course_codes)} courses")
        return results


def test_uwflow_scraper():
    """Test the UWFlow scraper"""
    print("🧪 Testing UWFlow scraper...")
    
    scraper = UWFlowScraper(rate_limit=0.5)  # Faster for testing
    
    # Test courses
    test_courses = [
        "ECE140",
        "CS135", 
        "CS136",
        "STAT230",
        "MATH135"
    ]
    
    print(f"Testing with courses: {test_courses}")
    
    for course_code in test_courses:
        print(f"\n📚 Testing {course_code}...")
        
        course_data = scraper.get_course_data(course_code)
        
        if course_data:
            print(f"✅ Found data for {course_code}:")
            print(f"  Rating: {course_data.rating}")
            print(f"  Difficulty: {course_data.difficulty}")
            print(f"  Workload: {course_data.workload}")
            print(f"  Usefulness: {course_data.usefulness}")
            print(f"  Reviews: {course_data.review_count}")
            print(f"  Number of ratings: {course_data.num_ratings}")
        else:
            print(f"❌ No data found for {course_code}")
    
    print("\n✅ UWFlow scraper test completed!")


if __name__ == "__main__":
    test_uwflow_scraper()