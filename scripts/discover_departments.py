#!/usr/bin/env python3
"""
Discover all available UWaterloo course catalog departments
"""

import requests
import time
from urllib.parse import urljoin

# All subject codes from the query page
ALL_SUBJECT_CODES = [
    'ACC', 'ACINTY', 'ACTSC', 'AE', 'AFM', 'AMATH', 'ANTH', 'APPLS', 'ARABIC', 
    'ARBUS', 'ARCH', 'ARTS', 'ASL', 'ASTRN', 'AVIA', 'BASE', 'BE', 'BET', 
    'BIOL', 'BLKST', 'BME', 'BUS', 'CC', 'CDNST', 'CFM', 'CHE', 'CHEM', 
    'CHINA', 'CI', 'CIVE', 'CLAS', 'CM', 'CMW', 'CO', 'COGSCI', 'COMM', 
    'COMMST', 'CROAT', 'CS', 'CT', 'CULT', 'DAC', 'DATSC', 'DEI', 'DEVP', 
    'DUTCH', 'EARTH', 'EASIA', 'ECDEV', 'ECE', 'ECON', 'EDMI', 'EMLS', 
    'ENBUS', 'ENGL', 'ENTR', 'ENVE', 'ENVS', 'ERS', 'EVST', 'FCIT', 'FILM', 
    'FINE', 'FR', 'GBDA', 'GC', 'GEMCC', 'GENE', 'GEOE', 'GEOG', 'GER', 
    'GERON', 'GESC', 'GGOV', 'GLST', 'GRK', 'GS', 'GSJ', 'HBIO', 'HEALTH', 
    'HHUM', 'HIST', 'HLTH', 'HRM', 'HRTS', 'HUMSC', 'INDENT', 'INDEV', 
    'INDG', 'INNOV', 'INTEG', 'INTST', 'ITAL', 'ITALST', 'JAPAN', 'JS', 
    'KIN', 'KOREA', 'LANG', 'LAT', 'LS', 'MATBUS', 'MATH', 'ME', 'MEDVL', 
    'MGMT', 'MISC', 'MNS', 'MSE', 'MTE', 'MTHEL', 'MUSIC', 'NANO', 'NE', 
    'OLRD', 'OPTOM', 'PACS', 'PD', 'PDARCH', 'PDPHRM', 'PHARM', 'PHIL', 
    'PHYS', 'PLAN', 'PMATH', 'PS', 'PSCI', 'PSYCH', 'QIC', 'RCS', 'REC', 
    'REES', 'RELC', 'RS', 'RSCH', 'RUSS', 'SCBUS', 'SCI', 'SDS', 'SE', 
    'SEQ', 'SFM', 'SI', 'SMF', 'SOC', 'SOCWK', 'SPAN', 'SRF', 'STAT', 
    'STV', 'SUSM', 'SWK', 'SWREN', 'SYDE', 'TAX', 'THPERF', 'TN', 'TPM', 
    'TS', 'UCR', 'UN', 'UNDC', 'UNIV', 'UU', 'VCULT', 'WATER', 'WIL', 
    'WKRPT', 'YC'
]

BASE_URL = "https://ucalendar.uwaterloo.ca/2324/COURSE/"

def check_department_page(dept_code):
    """Check if a department has a course catalog page"""
    url = urljoin(BASE_URL, f"course-{dept_code}.html")
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            # Check if page has actual course content (not just empty/error page)
            content = response.text.lower()
            if f"{dept_code.lower()}" in content and ("course" in content or "credit" in content):
                return True, len(response.text)
        return False, None
    except Exception as e:
        return False, str(e)

def discover_all_departments():
    """Discover all available department course pages"""
    print(f"🔍 Checking {len(ALL_SUBJECT_CODES)} potential department pages...")
    
    available_departments = {}
    unavailable_departments = []
    
    for i, dept in enumerate(ALL_SUBJECT_CODES):
        print(f"[{i+1:3d}/{len(ALL_SUBJECT_CODES)}] Checking {dept}...", end=" ")
        
        is_available, size_or_error = check_department_page(dept)
        
        if is_available:
            available_departments[dept] = size_or_error
            print(f"✅ Available ({size_or_error:,} bytes)")
        else:
            unavailable_departments.append(dept)
            print(f"❌ Not available")
        
        # Rate limiting to be respectful
        time.sleep(0.5)
    
    print(f"\n📊 Discovery Results:")
    print(f"  Available departments: {len(available_departments)}")
    print(f"  Unavailable departments: {len(unavailable_departments)}")
    
    print(f"\n✅ Available departments ({len(available_departments)}):")
    for dept, size in sorted(available_departments.items()):
        print(f"  {dept}: {size:,} bytes")
    
    print(f"\n❌ Unavailable departments ({len(unavailable_departments)}):")
    for dept in sorted(unavailable_departments):
        print(f"  {dept}")
    
    # Generate Python dictionary for the scraper
    print(f"\n🐍 Python dictionary for scraper:")
    print("DEPARTMENT_URLS = {")
    for dept in sorted(available_departments.keys()):
        print(f"    '{dept}': 'course-{dept}.html',")
    print("}")
    
    return available_departments, unavailable_departments

if __name__ == "__main__":
    available, unavailable = discover_all_departments()