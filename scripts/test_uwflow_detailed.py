#!/usr/bin/env python3
"""
Detailed UWFlow analysis to understand their current structure
"""

import requests
import time
from bs4 import BeautifulSoup

def analyze_uwflow_homepage():
    """Analyze the UWFlow homepage to understand the current structure"""
    
    url = "https://www.uwflow.com"
    
    print(f"🏠 Analyzing UWFlow homepage: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"✅ Status: {response.status_code}")
        print(f"📏 Content length: {len(response.text)}")
        print(f"🔧 Content-Type: {response.headers.get('content-type', 'Unknown')}")
        
        # Parse the content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Print the title
        title = soup.find('title')
        if title:
            print(f"📄 Page title: {title.get_text()}")
        
        # Look for any course links or structure
        links = soup.find_all('a', href=True)
        course_links = []
        
        for link in links[:20]:  # Check first 20 links
            href = link.get('href', '')
            if 'course' in href:
                course_links.append(href)
        
        if course_links:
            print(f"🔗 Found course links: {course_links}")
        else:
            print("❌ No course links found in homepage")
        
        # Check for search functionality
        search_inputs = soup.find_all(['input', 'form'])
        search_found = False
        
        for element in search_inputs:
            if element.get('type') == 'search' or 'search' in str(element.get('placeholder', '')).lower():
                search_found = True
                print(f"🔍 Found search element: {element}")
        
        if not search_found:
            print("❌ No obvious search functionality found")
        
        # Print a sample of the content
        print(f"\n📄 Sample content (first 500 chars):")
        print(response.text[:500])
        print("...")
        
        return response.text
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_course_page_with_different_methods():
    """Test different methods to access course pages"""
    
    print("\n🧪 Testing different approaches to course pages...")
    
    course_codes = ["cs135", "ece140", "math135"]
    
    for course_code in course_codes:
        print(f"\n📚 Testing {course_code.upper()}...")
        
        # Method 1: Direct URL
        url1 = f"https://www.uwflow.com/course/{course_code}"
        
        # Method 2: Alternative formats
        url2 = f"https://www.uwflow.com/course/{course_code.upper()}"
        url3 = f"https://www.uwflow.com/courses/{course_code}"
        
        # Method 3: Search-like URLs
        url4 = f"https://www.uwflow.com/search?q={course_code}"
        
        urls_to_test = [url1, url2, url3, url4]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.uwflow.com/',
        }
        
        for url in urls_to_test:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                
                print(f"  {url}")
                print(f"    Status: {response.status_code}")
                print(f"    Length: {len(response.text)}")
                
                if response.status_code == 200:
                    # Check if we got actual course content
                    content = response.text.lower()
                    
                    # Look for course-related keywords
                    course_indicators = [
                        course_code.lower(),
                        'rating',
                        'difficulty', 
                        'professor',
                        'review',
                        'prerequisite',
                        'description'
                    ]
                    
                    found_indicators = [word for word in course_indicators if word in content]
                    
                    if found_indicators:
                        print(f"    ✅ Found course indicators: {found_indicators}")
                        
                        # If this looks promising, save a sample
                        if len(found_indicators) >= 3:
                            print(f"    📊 This looks like actual course content!")
                            
                            # Extract a relevant snippet
                            soup = BeautifulSoup(response.text, 'html.parser')
                            text_content = soup.get_text()[:1000]
                            print(f"    📄 Sample content: {text_content[:200]}...")
                    else:
                        print(f"    ❌ No course indicators found")
                
                elif response.status_code == 404:
                    print(f"    ❌ Not found")
                elif response.status_code in [301, 302, 303, 307, 308]:
                    redirect_url = response.headers.get('location', 'Unknown')
                    print(f"    🔄 Redirected to: {redirect_url}")
                else:
                    print(f"    ⚠️  Unexpected status code")
                    
            except Exception as e:
                print(f"    ❌ Error: {e}")
                
            time.sleep(0.5)  # Small delay between requests

def check_uwflow_status():
    """Check if UWFlow is accessible and operational"""
    
    print("\n🏥 Checking UWFlow status...")
    
    # Test basic connectivity
    try:
        response = requests.get("https://www.uwflow.com", timeout=10)
        print(f"✅ UWFlow is accessible (Status: {response.status_code})")
        
        # Check if it's a maintenance page or similar
        content = response.text.lower()
        
        maintenance_keywords = [
            'maintenance',
            'down for maintenance', 
            'temporarily unavailable',
            'under construction',
            'coming soon',
            '503',
            'service unavailable'
        ]
        
        for keyword in maintenance_keywords:
            if keyword in content:
                print(f"⚠️  Possible maintenance mode detected: '{keyword}' found")
                return False
        
        # Check if it looks like a normal site
        if len(response.text) < 1000:
            print(f"⚠️  Very short response ({len(response.text)} chars) - might be an error page")
        elif 'uwflow' in content or 'course' in content:
            print(f"✅ Looks like normal UWFlow content")
        else:
            print(f"⚠️  Content doesn't look like expected UWFlow site")
        
        return True
        
    except Exception as e:
        print(f"❌ UWFlow not accessible: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Detailed UWFlow Analysis")
    print("=" * 50)
    
    # Check if UWFlow is accessible
    if check_uwflow_status():
        
        # Analyze homepage
        homepage_content = analyze_uwflow_homepage()
        
        # Test course pages
        test_course_page_with_different_methods()
    
    print("\n✅ Analysis completed!")