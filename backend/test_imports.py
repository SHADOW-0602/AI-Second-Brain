#!/usr/bin/env python3
"""
Test script to check route imports
"""
import sys
import os

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if routes can be imported"""
    
    try:
        print("Testing route imports...")
        
        print("1. Testing ingest route...")
        from routes import ingest
        print("   SUCCESS: ingest imported")
        
        print("2. Testing system route...")
        from routes import system
        print("   SUCCESS: system imported")
        
        print("3. Testing chat_sessions route...")
        from routes import chat_sessions
        print("   SUCCESS: chat_sessions imported")
        
        print("4. Testing workflow route...")
        from routes import workflow
        print("   SUCCESS: workflow imported")
        
        print("5. Testing smart_notes route...")
        from routes import smart_notes
        print("   SUCCESS: smart_notes imported")
        
        return True
        
    except Exception as e:
        print(f"   ERROR: Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Route Imports")
    print("=" * 40)
    
    success = test_imports()
    
    print("=" * 40)
    if success:
        print("All routes imported successfully!")
    else:
        print("Route import failed!")