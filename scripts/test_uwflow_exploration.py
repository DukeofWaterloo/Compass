#!/usr/bin/env python3
"""
Explore UWFlow to understand how to extract course data
"""

import requests
import json
import re
from bs4 import BeautifulSoup

def explore_uwflow_page(course_code: str = "ece140"):
    """Explore a UWFlow course page to understand its structure"""
    
    url = f"https://www.uwflow.com/course/{course_code}"
    
    print(f"🔍 Exploring UWFlow page: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        print(f"✅ Response status: {response.status_code}")
        print(f"📏 Content length: {len(response.text)} characters")
        
        # Check if it's a SPA (Single Page Application)
        if 'react' in response.text.lower() or 'angular' in response.text.lower() or 'vue' in response.text.lower():
            print("🔧 Detected client-side framework")
        
        # Look for any API endpoints or data loading patterns
        api_patterns = [
            r'api[/.]([a-zA-Z0-9_/-]+)',
            r'fetch\(["\']([^"\']+)["\']',
            r'axios\.get\(["\']([^"\']+)["\']',
            r'endpoint["\']:\s*["\']([^"\']+)["\']',
            r'/graphql',
            r'/api/v\d+',
        ]
        
        print("\n🔍 Looking for API endpoints...")
        found_apis = set()
        
        for pattern in api_patterns:
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                if match and not match.startswith('data:'):
                    found_apis.add(match)
        
        if found_apis:
            print("📡 Potential API endpoints found:")
            for api in sorted(found_apis)[:10]:  # Show first 10
                print(f"  - {api}")
        else:
            print("❌ No obvious API endpoints found")
        
        # Look for embedded JSON data
        print("\n🔍 Looking for embedded JSON data...")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check script tags for JSON data
        script_tags = soup.find_all('script')
        json_data_found = False
        
        for script in script_tags:
            if script.string:
                script_content = script.string.strip()
                
                # Look for course data patterns
                if course_code.upper() in script_content or course_code.lower() in script_content:
                    print(f"📊 Found course reference in script tag")
                    
                    # Try to extract JSON objects
                    json_objects = re.findall(r'\{[^{}]*(?:[^{}]*\{[^{}]*\}[^{}]*)*[^{}]*\}', script_content)
                    
                    for json_obj in json_objects[:3]:  # Check first 3 JSON objects
                        try:
                            data = json.loads(json_obj)
                            if isinstance(data, dict) and len(data) > 0:
                                print(f"✅ Found JSON data with keys: {list(data.keys())}")
                                json_data_found = True
                                
                                # Look for course-related data
                                course_keys = ['rating', 'difficulty', 'reviews', 'course', 'id']
                                for key in course_keys:
                                    if key in data:
                                        print(f"  📈 {key}: {data[key]}")
                                        
                        except json.JSONDecodeError:
                            continue
        
        if not json_data_found:
            print("❌ No embedded JSON course data found")
        
        # Check for Next.js or other framework data
        print("\n🔍 Looking for framework-specific data...")
        
        if '__NEXT_DATA__' in response.text:
            print("🔧 Detected Next.js application")
            
            # Extract Next.js data
            next_data_match = re.search(r'__NEXT_DATA__["\']?\s*=\s*({.+?})\s*(?:</script>|;)', response.text)
            if next_data_match:
                try:
                    next_data = json.loads(next_data_match.group(1))
                    print(f"✅ Next.js data found with keys: {list(next_data.keys())}")
                    
                    # Look for page props
                    if 'props' in next_data and 'pageProps' in next_data['props']:
                        page_props = next_data['props']['pageProps']
                        print(f"📄 Page props keys: {list(page_props.keys()) if isinstance(page_props, dict) else 'Not a dict'}")
                        
                        # Look for course data in page props
                        if isinstance(page_props, dict):
                            for key, value in page_props.items():
                                if 'course' in key.lower() or 'rating' in key.lower():
                                    print(f"  🎯 {key}: {value}")
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Error parsing Next.js data: {e}")
        
        # Check for GraphQL queries
        if 'graphql' in response.text.lower():
            print("🔧 Detected GraphQL usage")
            
            # Look for GraphQL query patterns
            graphql_patterns = [
                r'query\s+(\w+)\s*\{',
                r'mutation\s+(\w+)\s*\{',
                r'fragment\s+(\w+)\s*on',
            ]
            
            for pattern in graphql_patterns:
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                if matches:
                    print(f"📡 GraphQL operations found: {matches}")
        
        print(f"\n📋 Summary for {course_code.upper()}:")
        print(f"  - Content type: {'SPA/Dynamic' if any(fw in response.text.lower() for fw in ['react', 'vue', 'angular']) else 'Static'}")
        print(f"  - Framework: {'Next.js' if '__NEXT_DATA__' in response.text else 'Other/Unknown'}")
        print(f"  - API endpoints: {len(found_apis)} found")
        print(f"  - JSON data: {'Yes' if json_data_found else 'No'}")
        
    except requests.RequestException as e:
        print(f"❌ Network error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_potential_api_endpoints():
    """Test potential UWFlow API endpoints"""
    
    print("\n🧪 Testing potential API endpoints...")
    
    base_urls = [
        "https://www.uwflow.com/api",
        "https://api.uwflow.com",
        "https://www.uwflow.com/graphql",
    ]
    
    endpoints = [
        "/courses",
        "/course/ece140",
        "/v1/courses",
        "/v1/course/ece140",
        "",  # Just the base URL
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
    }
    
    for base_url in base_urls:
        for endpoint in endpoints:
            url = base_url + endpoint
            
            try:
                response = requests.get(url, headers=headers, timeout=5)
                print(f"✅ {url} - Status: {response.status_code}")
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    if 'json' in content_type:
                        try:
                            data = response.json()
                            print(f"  📊 JSON response with keys: {list(data.keys()) if isinstance(data, dict) else 'Array/Other'}")
                        except json.JSONDecodeError:
                            print(f"  📄 Response length: {len(response.text)} chars")
                    else:
                        print(f"  📄 Content-Type: {content_type}")
                        
            except requests.RequestException as e:
                print(f"❌ {url} - Error: {e}")

if __name__ == "__main__":
    print("🔍 UWFlow Exploration Script")
    print("=" * 50)
    
    # Test a few different courses
    test_courses = ["ece140", "cs135", "math135"]
    
    for course in test_courses:
        explore_uwflow_page(course)
        print("\n" + "="*50 + "\n")
    
    test_potential_api_endpoints()
    
    print("\n✅ Exploration completed!")