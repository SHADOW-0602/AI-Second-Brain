#!/usr/bin/env python3
"""
Test script to verify Groq model functionality
"""
import sys
import os

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_groq_model():
    """Test Groq model connectivity and functionality"""
    try:
        from groq_client import groq_client
        
        if not groq_client.client:
            print("ERROR: Groq client not initialized - check GROQ_API_KEY")
            return False
            
        print("Testing Groq model...")
        
        # Test simple completion
        completion = groq_client.client.chat.completions.create(
            messages=[{"role": "user", "content": "Say 'Hello' in one word."}],
            model="llama-3.1-8b-instant",
            temperature=0.1,
            max_tokens=10
        )
        
        response = completion.choices[0].message.content
        print(f"SUCCESS: Groq model working: {response}")
        
        # Test note generation function
        from routes.smart_notes import process_single_chunk
        import asyncio
        
        async def test_note_gen():
            result = await process_single_chunk("This is a test document.", "llama-3.1-8b-instant")
            print(f"SUCCESS: Note generation working: {len(result)} chars generated")
            return True
            
        asyncio.run(test_note_gen())
        return True
        
    except Exception as e:
        print(f"ERROR: Groq test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Groq Model Functionality")
    print("=" * 40)
    
    success = test_groq_model()
    
    print("=" * 40)
    if success:
        print("All tests passed!")
        sys.exit(0)
    else:
        print("Tests failed!")
        sys.exit(1)