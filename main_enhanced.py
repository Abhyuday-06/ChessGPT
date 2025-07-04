"""
Enhanced Chess Strategy AI - Main Integration Script
Combines all components for seamless operation
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_modules = [
        'flask', 'requests', 'chess', 'stockfish', 'bs4'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("📦 Please run: pip install -r requirements.txt")
        return False
    
    return True

def check_ollama_setup():
    """Check if Ollama is properly configured"""
    if not os.path.exists("ollama_config.json"):
        print("⚠️ Ollama not configured. Please run setup_enhanced.py first.")
        return False, None
    
    try:
        with open("ollama_config.json", "r") as f:
            config = json.load(f)
        
        model_name = config.get("model_name", "gemma2:2b")
        print(f"✅ Ollama configured with model: {model_name}")
        return True, model_name
    except Exception as e:
        print(f"❌ Error reading Ollama config: {e}")
        return False, None

def check_stockfish():
    """Check if Stockfish is available"""
    stockfish_path = "stockfish/stockfish.exe"
    if os.path.exists(stockfish_path):
        print("✅ Stockfish engine found")
        return True
    else:
        print("⚠️ Stockfish not found. Please run setup_stockfish.py")
        return False

def check_training_data():
    """Check training data status"""
    if os.path.exists("chess_strategy_training_data.json"):
        try:
            with open("chess_strategy_training_data.json", "r") as f:
                data = json.load(f)
            
            if isinstance(data, list) and len(data) > 0:
                print(f"✅ Training data available: {len(data)} entries")
                return True
            else:
                print("⚠️ Training data file is empty")
                return False
        except Exception as e:
            print(f"❌ Error reading training data: {e}")
            return False
    else:
        print("⚠️ No training data found. Analyze some players first.")
        return False

def run_system_checks():
    """Run comprehensive system checks"""
    print("🔍 Running system checks...")
    print("-" * 40)
    
    checks = [
        ("Dependencies", check_dependencies()),
        ("Ollama Setup", check_ollama_setup()[0]),
        ("Stockfish Engine", check_stockfish()),
        ("Training Data", check_training_data())
    ]
    
    all_passed = True
    for check_name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:20} {status}")
        if not result:
            all_passed = False
    
    print("-" * 40)
    return all_passed

def show_usage_guide():
    """Show usage guide"""
    print("\n📚 USAGE GUIDE")
    print("=" * 50)
    print("1. 🔧 Setup (First time only):")
    print("   python setup_enhanced.py")
    print()
    print("2. 🚀 Start the enhanced web UI:")
    print("   python enhanced_web_ui.py")
    print()
    print("3. 🌐 Open your browser:")
    print("   http://localhost:5000")
    print()
    print("4. 📊 Use the system:")
    print("   • Enter any chess username to analyze")
    print("   • Wait for analysis to complete")
    print("   • Get AI-powered strategies")
    print()
    print("5. 💡 Command line tools:")
    print("   • python chess_strategy_cli.py  (CLI interface)")
    print("   • python view_dataset.py       (View training data)")
    print("   • python chess_analyzer.py <username>  (Direct analysis)")

def main():
    print("🏛️ Enhanced Chess Strategy AI")
    print("=" * 50)
    
    # Run system checks
    if not run_system_checks():
        print("\n❌ System checks failed. Please address the issues above.")
        show_usage_guide()
        return
    
    print("\n✅ All system checks passed!")
    
    # Check if Ollama is running
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama service is running")
        else:
            print("⚠️ Ollama service not responding")
    except:
        print("⚠️ Ollama service not running. Starting...")
        try:
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3)
            print("✅ Ollama service started")
        except:
            print("❌ Failed to start Ollama. Please start manually: 'ollama serve'")
    
    # Show status
    print("\n📊 SYSTEM STATUS")
    print("-" * 30)
    
    # Show available players
    try:
        from enhanced_analyzer import enhanced_analyzer
        players = enhanced_analyzer.get_available_players()
        print(f"Available players: {len(players)}")
        if players:
            print(f"Players: {', '.join(players[:5])}")
            if len(players) > 5:
                print(f"... and {len(players) - 5} more")
    except Exception as e:
        print(f"Error loading players: {e}")
    
    # Interactive menu
    print("\n🎯 QUICK ACTIONS")
    print("=" * 30)
    print("1. 🎨 Start Simple Single-Input UI")
    print("2. 🏛️ Start Open WebUI Backend")
    print("3. 💻 Start Enhanced Web UI")
    print("4. 🖥️ Analyze New Player (CLI)")
    print("5. 📊 View Training Data")
    print("6. 🚀 Launch Quick Start Menu")
    print("7. Exit")
    
    while True:
        choice = input("\nSelect option (1-7): ").strip()
        
        if choice == "1":
            print("🚀 Starting Simple Single-Input UI...")
            os.system("python single_input_ui.py")
            break
        elif choice == "2":
            print("🚀 Starting Open WebUI Backend...")
            os.system("python openwebui_backend.py")
            break
        elif choice == "3":
            print("🚀 Starting Enhanced Web UI...")
            os.system("python enhanced_web_ui.py")
            break
        elif choice == "4":
            username = input("Enter chess username: ").strip()
            if username:
                print(f"🔍 Analyzing {username}...")
                os.system(f"python chess_analyzer.py {username}")
            else:
                print("❌ Please enter a username")
        elif choice == "5":
            print("📊 Viewing training data...")
            os.system("python view_dataset.py")
        elif choice == "6":
            print("🚀 Launching Quick Start Menu...")
            os.system("python quick_start.py")
            break
        elif choice == "7":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-7.")

if __name__ == "__main__":
    main()
