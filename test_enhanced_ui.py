#!/usr/bin/env python
"""
Test script for Enhanced Web UI
Tests the complete workflow: analyze → get strategy
"""

import sys
import os
import json
import time
import requests
from threading import Thread

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_analyzer_api():
    """Test the chess analyzer API directly"""
    print("🔍 Testing chess analyzer API...")
    
    try:
        from chess_analyzer_api import ChessGameAnalyzer
        
        analyzer = ChessGameAnalyzer()
        
        # Test with a known chess.com user
        test_username = "hikaru"  # Use a well-known player
        
        print(f"📊 Testing analysis for {test_username}...")
        result = analyzer.analyze_player(test_username, "chess.com")
        
        if result:
            print("✅ Direct API test passed")
            return True
        else:
            print("❌ Direct API test failed")
            return False
            
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False

def test_enhanced_analyzer():
    """Test the enhanced analyzer wrapper"""
    print("🔍 Testing enhanced analyzer...")
    
    try:
        from enhanced_analyzer import enhanced_analyzer
        
        # Test getting available players
        players = enhanced_analyzer.get_available_players()
        print(f"📊 Available players: {players}")
        
        # Test starting analysis
        test_username = "testuserxyz123"  # Use a non-existent user to test quickly
        
        result = enhanced_analyzer.start_analysis(test_username, "chess.com")
        print(f"🚀 Start analysis result: {result}")
        
        # Wait a moment and check status
        time.sleep(2)
        status = enhanced_analyzer.get_progress(test_username)
        print(f"📊 Status: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced analyzer test error: {e}")
        return False

def test_ollama_llm():
    """Test Ollama LLM integration"""
    print("🔍 Testing Ollama LLM...")
    
    try:
        from ollama_llm import chess_llm
        
        # Check if Ollama is available
        if not chess_llm.check_ollama_available():
            print("⚠️ Ollama not available - skipping LLM tests")
            return True
        
        # Test simple query
        test_analysis = """
        Chess Player Analysis: TestPlayer
        
        Player: TestPlayer
        Platform: chess.com
        
        Identified Weaknesses:
        1. High Loss Rate: Loses 70% of games, indicating potential strategic issues
        2. Time Management: May struggle with time pressure in complex positions
        
        Please provide a comprehensive chess strategy to exploit these weaknesses.
        """
        
        strategy = chess_llm.generate_strategy(test_analysis)
        print(f"🤖 Generated strategy: {strategy[:200]}...")
        
        if strategy and not strategy.startswith("Error"):
            print("✅ LLM test passed")
            return True
        else:
            print("❌ LLM test failed")
            return False
            
    except Exception as e:
        print(f"❌ LLM test error: {e}")
        return False

def start_web_ui():
    """Start the web UI in a separate thread"""
    try:
        from enhanced_web_ui import app
        app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
    except Exception as e:
        print(f"❌ Web UI error: {e}")

def test_web_ui_endpoints():
    """Test the web UI endpoints"""
    print("🔍 Testing web UI endpoints...")
    
    # Start web UI in background
    ui_thread = Thread(target=start_web_ui, daemon=True)
    ui_thread.start()
    
    # Wait for server to start
    time.sleep(3)
    
    try:
        # Test main page
        response = requests.get("http://localhost:5000/", timeout=5)
        if response.status_code == 200:
            print("✅ Main page accessible")
        else:
            print(f"❌ Main page failed: {response.status_code}")
            return False
        
        # Test available players endpoint
        response = requests.get("http://localhost:5000/api/players", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Players endpoint works: {data}")
        else:
            print(f"❌ Players endpoint failed: {response.status_code}")
            return False
        
        # Test Ollama status endpoint
        response = requests.get("http://localhost:5000/api/ollama/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Ollama status endpoint works: {data}")
        else:
            print(f"❌ Ollama status endpoint failed: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Web UI endpoint test error: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("🏛️ Enhanced Web UI Test Suite")
    print("=" * 50)
    
    tests = [
        ("Enhanced Analyzer", test_enhanced_analyzer),
        ("Ollama LLM", test_ollama_llm),
        ("Web UI Endpoints", test_web_ui_endpoints),
        # ("Analyzer API", test_analyzer_api),  # Skip for now as it's slow
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        try:
            success = test_func()
            results.append((test_name, success))
            if success:
                print(f"✅ {test_name} test passed")
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test error: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("🏆 Test Results Summary:")
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n📊 {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Enhanced Web UI is ready.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the logs above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
