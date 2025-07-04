#!/usr/bin/env python
"""
Chess Strategy AI - System Test
Test the system components
"""

import sys
import os
import subprocess

def test_imports():
    """Test if all required imports work"""
    print("🔍 Testing imports...")
    
    try:
        from enhanced_analyzer import enhanced_analyzer
        print("✅ enhanced_analyzer imported successfully")
    except Exception as e:
        print(f"❌ enhanced_analyzer import failed: {e}")
        return False
    
    try:
        from ollama_llm import chess_llm
        print("✅ ollama_llm imported successfully")
    except Exception as e:
        print(f"❌ ollama_llm import failed: {e}")
        return False
    
    try:
        import chess
        print("✅ python-chess imported successfully")
    except Exception as e:
        print(f"❌ python-chess import failed: {e}")
        return False
    
    try:
        from flask import Flask
        print("✅ Flask imported successfully")
    except Exception as e:
        print(f"❌ Flask import failed: {e}")
        return False
    
    return True

def test_ollama():
    """Test if Ollama is available"""
    print("🔍 Testing Ollama...")
    
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print("✅ Ollama is running")
            print(f"📋 Available models: {result.stdout.strip()}")
            return True
        else:
            print("❌ Ollama is not running")
            return False
    except Exception as e:
        print(f"❌ Ollama test failed: {e}")
        return False

def test_stockfish():
    """Test if Stockfish is available"""
    print("🔍 Testing Stockfish...")
    
    stockfish_path = "stockfish/stockfish.exe"
    if os.path.exists(stockfish_path):
        print("✅ Stockfish found")
        return True
    else:
        print("❌ Stockfish not found")
        return False

def test_directories():
    """Test if required directories exist"""
    print("🔍 Testing directories...")
    
    required_dirs = ["templates", "stockfish"]
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✅ {dir_name} directory exists")
        else:
            print(f"❌ {dir_name} directory missing")
            return False
    
    return True

def main():
    print("🏛️ Chess Strategy AI - System Test")
    print("=" * 40)
    
    # Run all tests
    tests = [
        ("Imports", test_imports),
        ("Ollama", test_ollama),
        ("Stockfish", test_stockfish),
        ("Directories", test_directories)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📊 Running {test_name} test...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} test failed")
    
    print(f"\n📈 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready.")
        print("\n🚀 To start the system:")
        print("   python quick_start.py")
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
        
        if not test_ollama():
            print("\n💡 To fix Ollama issues:")
            print("   1. Install Ollama from https://ollama.ai/")
            print("   2. Run: ollama serve")
            print("   3. Run: ollama pull llama3.1:8b")

if __name__ == "__main__":
    main()
