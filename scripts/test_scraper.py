#!/usr/bin/env python3
"""
Quick POC to test UWaterloo course data extraction strategy
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from typing import Dict, List, Optional

def extract_courses_from_page(url: str) -> List[Dict]:
    """Extract course data from a UWaterloo course catalog page"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        courses = []
        
        # Look for course entries - they typically have a specific pattern
        # This is a rough pattern, may need adjustment based on actual HTML structure
        course_blocks = soup.find_all('p')
        
        for block in course_blocks:
            text = block.get_text().strip()
            
            # Look for course code pattern (e.g., "ECE 101A")
            course_match = re.search(r'^([A-Z]+\s+\d+[A-Z]?)', text)
            if course_match:
                course_code = course_match.group(1)
                
                # Extract course title (usually after the code)
                title_match = re.search(rf'{re.escape(course_code)}\s+(.+?)(?:\s+\([\d.]+\s+credits?\)|\s+Prereq:|\s+Coreq:|\s+Antireq:|$)', text)
                title = title_match.group(1).strip() if title_match else "Unknown"
                
                # Extract description (everything after title)
                desc_start = text.find(title) + len(title) if title != "Unknown" else len(course_code)
                description = text[desc_start:].strip()
                
                # Extract prerequisites
                prereq_match = re.search(r'Prereq:\s*([^;.]+)', description)
                prerequisites = prereq_match.group(1).strip() if prereq_match else None
                
                courses.append({
                    'code': course_code,
                    'title': title,
                    'description': description,
                    'prerequisites': prerequisites,
                    'url': url
                })
        
        return courses
        
    except Exception as e:
        print(f"Error extracting from {url}: {e}")
        return []

def test_query_form(subject: str = "CS", course_num: str = "135") -> Optional[str]:
    """Test the query form on classes.uwaterloo.ca"""
    url = "https://classes.uwaterloo.ca/cgi-bin/cgiwrap/infocour/salook.pl"
    
    data = {
        'level': 'under',
        'sess': '1259',  # Fall 2025
        'subject': subject,
        'cournum': course_num
    }
    
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        return response.text[:1000]  # Return first 1000 chars for inspection
    except Exception as e:
        print(f"Error querying form: {e}")
        return None

if __name__ == "__main__":
    print("🧪 Testing UWaterloo data extraction...")
    
    # Test 1: Extract courses from ECE catalog
    print("\n1. Testing course catalog extraction...")
    ece_url = "https://ucalendar.uwaterloo.ca/2324/COURSE/course-ECE.html"
    courses = extract_courses_from_page(ece_url)
    
    print(f"Found {len(courses)} courses")
    if courses:
        print("Sample course:")
        print(json.dumps(courses[0], indent=2))
    
    # Test 2: Test query form
    print("\n2. Testing schedule query form...")
    result = test_query_form("CS", "135")
    if result:
        print("Query form response (first 1000 chars):")
        print(result)
    
    print("\n✅ POC complete!")