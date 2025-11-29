#!/usr/bin/env python3

import requests
import json
import time

def test_memory_sources():
    """Test memory source tracking functionality"""
    
    print("Testing Memory Source Tracking...")
    print("=" * 50)
    
    # Test API endpoint
    url = "http://localhost:5300/api/chat/message"
    
    test_cases = [
        {
            "session_id": "test-sources-frontend",
            "message": "What is Python programming?",
            "expected_source": "🧠 General Knowledge"
        },
        {
            "session_id": "test-sources-frontend", 
            "message": "Tell me about artificial intelligence",
            "expected_source": "🧠 General Knowledge"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['message'][:30]}...")
        
        try:
            response = requests.post(url, json=test_case, timeout=45)
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get('response', '')
                
                print(f"Status: {response.status_code}")
                print(f"Response length: {len(ai_response)} characters")
                
                # Check for sources section
                if '**Sources:**' in ai_response:
                    print("SOURCES SECTION FOUND!")
                    
                    # Extract sources section
                    sources_start = ai_response.find('**Sources:**')
                    sources_end = ai_response.find('\n', sources_start)
                    if sources_end == -1:
                        sources_end = len(ai_response)
                    
                    sources_section = ai_response[sources_start:sources_end].strip()
                    print(f"Sources: {sources_section}")
                    
                    # Check if expected source is present
                    if test_case['expected_source'] in sources_section:
                        print(f"Expected source '{test_case['expected_source']}' found!")
                    else:
                        print(f"Expected source '{test_case['expected_source']}' not found")
                        
                    # Show markdown formatting
                    print("Markdown formatting check:")
                    print(f"   Raw: {repr(sources_section)}")
                    print(f"   Will render as: {sources_section.replace('**', '')}")
                    
                else:
                    print("No sources section found in response")
                    print("Response preview:")
                    print(ai_response[-150:])
                    
            else:
                print(f"HTTP Error: {response.status_code}")
                print(f"Error details: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print("Request timed out (45s)")
        except Exception as e:
            print(f"Request failed: {e}")
            
        # Small delay between requests
        if i < len(test_cases):
            time.sleep(2)
    
    print("\n" + "=" * 50)
    print("Frontend Testing Instructions:")
    print("1. Open http://localhost:5300 in your browser")
    print("2. Navigate to Search & Chat (M key)")
    print("3. Send a message like 'What is Python?'")
    print("4. Look for '**Sources:** 🧠 General Knowledge' at the end")
    print("5. Verify it displays as bold text: 'Sources: 🧠 General Knowledge'")
    print("6. The markdown renderer should convert ** to <strong> tags")

if __name__ == "__main__":
    test_memory_sources()