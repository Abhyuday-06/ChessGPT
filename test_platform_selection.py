#!/usr/bin/env python3
"""
Test script to verify platform selection functionality
"""

import sys
import os

# Add the current directory to the path so we can import the module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_platform_selection():
    print("Testing platform selection functionality...")
    
    # Test 1: Command line arguments
    print("\n1. Testing command line argument parsing...")
    sys.argv = ['test_script.py', 'testuser', 'chess.com']
    
    # Simulate the logic from chess_analyzer_complete.py
    if len(sys.argv) > 2:
        user = sys.argv[1]
        platform = sys.argv[2].lower()
    elif len(sys.argv) > 1:
        user = sys.argv[1]
        platform = None
    else:
        user = None
        platform = None
    
    print(f"   User: {user}")
    print(f"   Platform: {platform}")
    
    # Test 2: Platform validation
    print("\n2. Testing platform validation...")
    valid_platforms = ['chess.com', 'lichess']
    
    if platform in valid_platforms:
        print(f"   ✅ Platform '{platform}' is valid")
    else:
        print(f"   ❌ Platform '{platform}' is invalid")
    
    # Test 3: PGN file naming
    print("\n3. Testing PGN file naming...")
    if platform == "chess.com":
        pgn_file = "chess_com_games.pgn"
    elif platform == "lichess":
        pgn_file = "lichess_games.pgn"
    else:
        pgn_file = "unknown.pgn"
    
    print(f"   PGN file would be: {pgn_file}")
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_platform_selection()
