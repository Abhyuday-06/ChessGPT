#!/usr/bin/env python
"""
Chess Strategy AI - Quick Start
Choose your preferred interface to analyze chess players
"""

import subprocess
import sys
import os
import time
import webbrowser
from threading import Thread

def check_ollama_running():
    """Check if Ollama is running"""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False

def start_ollama():
    """Start Ollama if not running"""
    if not check_ollama_running():
        print("🔄 Starting Ollama...")
        try:
            if os.name == 'nt':  # Windows
                subprocess.Popen(["ollama", "serve"], shell=True)
            else:  # Unix-like
                subprocess.Popen(["ollama", "serve"])
            time.sleep(5)
            print("✅ Ollama started")
        except Exception as e:
            print(f"⚠️ Could not start Ollama: {e}")
            print("Please start Ollama manually: ollama serve")

def open_browser_delayed(url, delay=5):
    """Open browser after delay"""
    time.sleep(delay)
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"⚠️ Could not open browser: {e}")

def run_single_input_ui():
    """Run the single input UI"""
    print("🚀 Starting Single-Input Chess UI...")
    print("🌐 Opening http://localhost:5001")
    
    # Open browser in background
    Thread(target=open_browser_delayed, args=("http://localhost:5001",), daemon=True).start()
    
    try:
        subprocess.run([sys.executable, "single_input_ui.py"])
    except KeyboardInterrupt:
        print("\n👋 Single-Input UI stopped")

def run_openwebui_backend():
    """Run the OpenWebUI backend"""
    print("🚀 Starting OpenWebUI Backend...")
    print("📡 API available at http://localhost:8000")
    print("🔧 Configure Open WebUI to use: http://localhost:8000")
    
    try:
        subprocess.run([sys.executable, "openwebui_backend.py"])
    except KeyboardInterrupt:
        print("\n👋 OpenWebUI Backend stopped")

def run_complete_setup():
    """Run the complete setup with Open WebUI"""
    print("🚀 Starting Complete Setup...")
    
    try:
        subprocess.run([sys.executable, "chess_ai_complete.py"])
    except KeyboardInterrupt:
        print("\n👋 Complete Setup stopped")

def run_enhanced_ui():
    """Run the enhanced web UI"""
    print("🚀 Starting Enhanced Web UI...")
    print("🌐 Opening http://localhost:5000")
    
    # Open browser in background
    Thread(target=open_browser_delayed, args=("http://localhost:5000",), daemon=True).start()
    
    try:
        subprocess.run([sys.executable, "enhanced_web_ui.py"])
    except KeyboardInterrupt:
        print("\n👋 Enhanced UI stopped")

def run_cli_analysis():
    """Run CLI analysis"""
    username = input("Enter chess username: ").strip()
    if username:
        print(f"🔍 Analyzing {username}...")
        try:
            subprocess.run([sys.executable, "chess_analyzer.py", username])
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
    else:
        print("❌ Please enter a username")

def main():
    print("🏛️ Chess Strategy AI - Quick Start")
    print("=" * 50)
    
    # Check Ollama
    if not check_ollama_running():
        start_ollama()
    else:
        print("✅ Ollama is running")
    
    print()
    print("🎯 Choose your preferred interface:")
    print("=" * 35)
    print("1. 🎨 Simple Single-Input UI (Recommended)")
    print("   - One input field")
    print("   - Real-time progress")
    print("   - Beautiful interface")
    print()
    print("2. 🏛️ Open WebUI Integration")
    print("   - Professional chat interface")
    print("   - Streaming responses")
    print("   - Advanced features")
    print()
    print("3. 🔧 OpenWebUI Backend Only")
    print("   - For existing Open WebUI setup")
    print("   - API endpoint only")
    print()
    print("4. 💻 Enhanced Web UI")
    print("   - Multi-step interface")
    print("   - Detailed progress")
    print("   - Full-featured")
    print()
    print("5. 🖥️ Command Line Analysis")
    print("   - Direct username input")
    print("   - Terminal output")
    print()
    print("6. 🚀 Complete Automated Setup")
    print("   - Installs Open WebUI")
    print("   - Configures everything")
    print("   - One-click solution")
    print()
    
    while True:
        choice = input("Select option (1-6): ").strip()
        
        if choice == "1":
            run_single_input_ui()
            break
        elif choice == "2":
            print("\n📋 Open WebUI Integration Steps:")
            print("1. Install Open WebUI: pip install open-webui")
            print("2. Start this backend (will start automatically)")
            print("3. Start Open WebUI: open-webui serve --port 3000")
            print("4. Configure API: http://localhost:8000")
            print("5. Start analyzing players!")
            print()
            run_openwebui_backend()
            break
        elif choice == "3":
            run_openwebui_backend()
            break
        elif choice == "4":
            run_enhanced_ui()
            break
        elif choice == "5":
            run_cli_analysis()
            break
        elif choice == "6":
            run_complete_setup()
            break
        else:
            print("❌ Invalid choice. Please select 1-6.")

if __name__ == "__main__":
    main()
