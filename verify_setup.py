#!/usr/bin/env python
"""
Chess Strategy AI - Setup Verification
Verify all components are working correctly
"""

import sys
import os
import subprocess
import time
import json

def run_command(command, timeout=30):
    """Run a command and return success status"""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def verify_python_version():
    """Verify Python version"""
    print("🔍 Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
        return False

def verify_dependencies():
    """Verify required Python packages"""
    print("🔍 Checking Python dependencies...")
    
    required_packages = [
        'flask', 'requests', 'chess', 'stockfish', 'bs4', 'lxml'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing.append(package)
    
    if missing:
        print(f"\n💡 Install missing packages:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    return True

def verify_ollama():
    """Verify Ollama installation and models"""
    print("🔍 Checking Ollama...")
    
    # Check if Ollama is installed
    success, stdout, stderr = run_command("ollama --version")
    if not success:
        print("❌ Ollama not installed")
        print("💡 Install from: https://ollama.ai/")
        return False
    
    print(f"✅ Ollama installed: {stdout.strip()}")
    
    # Check if Ollama is running
    success, stdout, stderr = run_command("ollama list")
    if not success:
        print("⚠️ Ollama not running")
        print("💡 Start with: ollama serve")
        
        # Try to start Ollama
        print("🔄 Attempting to start Ollama...")
        if os.name == 'nt':  # Windows
            subprocess.Popen(["ollama", "serve"], shell=True)
        else:
            subprocess.Popen(["ollama", "serve"])
        
        time.sleep(5)
        
        # Check again
        success, stdout, stderr = run_command("ollama list")
        if not success:
            print("❌ Failed to start Ollama")
            return False
    
    print("✅ Ollama is running")
    
    # Check available models
    models = stdout.strip().split('\n')[1:]  # Skip header
    if not models or len(models) == 0:
        print("⚠️ No models installed")
        print("💡 Install a model:")
        print("   ollama pull llama3.1:8b")
        return False
    
    print(f"✅ Available models: {len(models)}")
    for model in models:
        if model.strip():
            print(f"   - {model.strip()}")
    
    return True

def verify_stockfish():
    """Verify Stockfish engine"""
    print("🔍 Checking Stockfish...")
    
    stockfish_paths = [
        "stockfish/stockfish.exe",
        "stockfish/stockfish",
        "stockfish/stockfish/stockfish-windows-x86-64-avx2.exe"
    ]
    
    for path in stockfish_paths:
        if os.path.exists(path):
            print(f"✅ Stockfish found: {path}")
            return True
    
    print("❌ Stockfish not found")
    print("💡 Run: python setup_stockfish.py")
    return False

def verify_config_files():
    """Verify configuration files"""
    print("🔍 Checking configuration files...")
    
    config_files = [
        "requirements.txt",
        "ollama_config.json"
    ]
    
    all_present = True
    for file in config_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"⚠️ {file} - Missing (optional)")
            if file == "ollama_config.json":
                print("💡 Run: python setup_enhanced.py")
    
    return all_present

def verify_directories():
    """Verify required directories"""
    print("🔍 Checking directories...")
    
    required_dirs = ["templates", "stockfish"]
    optional_dirs = ["simple_chess_model", "__pycache__"]
    
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✅ {dir_name}/")
        else:
            print(f"❌ {dir_name}/ - Missing")
            if dir_name == "templates":
                print("💡 Will be created automatically")
    
    for dir_name in optional_dirs:
        if os.path.exists(dir_name):
            print(f"✅ {dir_name}/")
    
    return True

def verify_core_files():
    """Verify core Python files"""
    print("🔍 Checking core files...")
    
    core_files = [
        "chess_analyzer.py",
        "enhanced_analyzer.py",
        "ollama_llm.py",
        "single_input_ui.py",
        "openwebui_backend.py",
        "enhanced_web_ui.py",
        "quick_start.py"
    ]
    
    all_present = True
    for file in core_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - Missing")
            all_present = False
    
    return all_present

def verify_imports():
    """Verify that core modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from enhanced_analyzer import enhanced_analyzer
        print("✅ enhanced_analyzer")
    except Exception as e:
        print(f"❌ enhanced_analyzer: {e}")
        return False
    
    try:
        from ollama_llm import chess_llm
        print("✅ ollama_llm")
    except Exception as e:
        print(f"❌ ollama_llm: {e}")
        return False
    
    return True

def create_setup_report():
    """Create a setup report"""
    print("📊 Creating setup report...")
    
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "system": os.name,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "working_directory": os.getcwd(),
        "tests": {}
    }
    
    # Run all tests
    tests = [
        ("python_version", verify_python_version),
        ("dependencies", verify_dependencies),
        ("ollama", verify_ollama),
        ("stockfish", verify_stockfish),
        ("config_files", verify_config_files),
        ("directories", verify_directories),
        ("core_files", verify_core_files),
        ("imports", verify_imports)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"🧪 {test_name.replace('_', ' ').title()}")
        print(f"{'='*50}")
        
        try:
            result = test_func()
            report["tests"][test_name] = {"passed": result, "error": None}
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            report["tests"][test_name] = {"passed": False, "error": str(e)}
    
    # Save report
    with open("setup_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n{'='*50}")
    print("📈 FINAL RESULTS")
    print(f"{'='*50}")
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All systems ready! You can start using Chess Strategy AI.")
        print("\n🚀 Quick start options:")
        print("   python quick_start.py       # Choose interface")
        print("   python single_input_ui.py   # Simple interface")
        print("   python openwebui_backend.py # Open WebUI backend")
    else:
        print("⚠️ Some components need attention. Check the output above.")
        
        if not verify_ollama():
            print("\n🔧 Common fixes:")
            print("   1. Install Ollama: https://ollama.ai/")
            print("   2. Start service: ollama serve")
            print("   3. Install model: ollama pull llama3.1:8b")
    
    print(f"\n📄 Detailed report saved to: setup_report.json")
    
    return passed == total

def main():
    print("🏛️ Chess Strategy AI - Setup Verification")
    print("=" * 60)
    print("This script will verify all components are working correctly.")
    print("=" * 60)
    
    try:
        success = create_setup_report()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Verification cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
