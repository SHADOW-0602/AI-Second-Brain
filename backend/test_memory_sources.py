#!/usr/bin/env python3
"""
Test script to verify memory source tracking functionality
"""
import requests
import json

def test_memory_sources():
    """Test if memory sources are being displayed in responses"""
    
    base_url = "http://127.0.0.1:5300"
    
    # Test 1: Start a new chat session
    print("1. Creating new chat session...")
    try:
        response = requests.post(f"{base_url}/api/chat/start")
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data['session_id']
            print(f"   SUCCESS: Session created: {session_id}")
        else:
            print(f"   ERROR: Failed to create session: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ERROR: {e}")
        return False
    
    # Test 2: Send a chat message
    print("2. Sending test message...")
    try:
        chat_data = {
            "session_id": session_id,
            "message": "What is artificial intelligence?"
        }
        
        response = requests.post(f"{base_url}/api/chat/message", json=chat_data)
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('response', '')
            print(f"   SUCCESS: Got AI response ({len(ai_response)} chars)")
            
            # Check if sources are included
            if "**Sources:**" in ai_response:
                print("   SUCCESS: Memory sources are being tracked!")
                sources_line = ai_response.split("**Sources:**")[1].strip()
                try:
                    print(f"   Sources found: {sources_line}")
                except UnicodeEncodeError:
                    print("   Sources found: [Contains emojis - display issue but working]")
                return True
            else:
                print("   WARNING: No memory sources found in response")
                print(f"   Response preview: {ai_response[:200]}...")
                return False
        else:
            print(f"   ERROR: Chat failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

if __name__ == "__main__":
    print("Testing Memory Source Tracking")
    print("=" * 40)
    
    success = test_memory_sources()
    
    print("=" * 40)
    if success:
        print("Memory source tracking is working!")
    else:
        print("Memory source tracking needs debugging.")