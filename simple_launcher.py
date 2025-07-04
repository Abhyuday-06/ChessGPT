#!/usr/bin/env python
"""
Chess Strategy AI - Simple Launcher
Quick launcher for the most common use cases
"""

import subprocess
import sys
import os
import time
import webbrowser
from threading import Thread

def check_ollama():
    """Check if Ollama is available"""
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
    if not check_ollama():
        print("🔄 Starting Ollama...")
        try:
            if os.name == 'nt':  # Windows
                subprocess.Popen(["ollama", "serve"], shell=True)
            else:
                subprocess.Popen(["ollama", "serve"])
            time.sleep(5)
            print("✅ Ollama started")
        except Exception as e:
            print(f"⚠️ Could not start Ollama: {e}")
            print("💡 Please start Ollama manually: ollama serve")

def open_browser_delayed(url, delay=5):
    """Open browser after delay"""
    time.sleep(delay)
    try:
        webbrowser.open(url)
    except:
        pass

def main():
    print("🏛️ Chess Strategy AI - Simple Launcher")
    print("=" * 50)
    
    # Check and start Ollama
    if not check_ollama():
        start_ollama()
    else:
        print("✅ Ollama is running")
    
    print("\n🎯 Choose your interface:")
    print("=" * 30)
    print("1. 🎨 Simple Single-Input UI (Recommended)")
    print("   • One input field")
    print("   • Real-time progress")
    print("   • Perfect for beginners")
    print()
    print("2. 💻 Enhanced Web UI")
    print("   • Full-featured interface")
    print("   • Multiple options")
    print("   • Advanced features")
    print()
    print("3. 🔧 OpenWebUI Backend Only")
    print("   • For existing Open WebUI setup")
    print("   • API endpoint")
    print("   • Advanced users")
    print()
    print("4. 📊 Direct Analysis (CLI)")
    print("   • Command line interface")
    print("   • Quick analysis")
    print("   • Terminal output")
    print()
    
    while True:
        choice = input("Select option (1-4): ").strip()
        
        if choice == "1":
            print("🚀 Starting Simple Single-Input UI...")
            print("🌐 Will open at: http://localhost:5001")
            
            # Open browser after delay
            Thread(target=open_browser_delayed, args=("http://localhost:5001",), daemon=True).start()
            
            try:
                subprocess.run([sys.executable, "single_input_ui.py"])
            except KeyboardInterrupt:
                print("\n👋 Simple UI stopped")
            break
            
        elif choice == "2":
            print("🚀 Starting Enhanced Web UI...")
            print("🌐 Will open at: http://localhost:5000")
            
            # Open browser after delay
            Thread(target=open_browser_delayed, args=("http://localhost:5000",), daemon=True).start()
            
            try:
                subprocess.run([sys.executable, "enhanced_web_ui.py"])
            except KeyboardInterrupt:
                print("\n👋 Enhanced UI stopped")
            break
            
        elif choice == "3":
            print("🚀 Starting OpenWebUI Backend...")
            print("🔧 API available at: http://localhost:8000")
            print("💡 Configure Open WebUI to use this endpoint")
            
            try:
                subprocess.run([sys.executable, "openwebui_backend.py"])
            except KeyboardInterrupt:
                print("\n👋 Backend stopped")
            break
            
        elif choice == "4":
            username = input("Enter chess username: ").strip()
            if username:
                print(f"🔍 Analyzing {username}...")
                try:
                    subprocess.run([sys.executable, "chess_analyzer.py", username])
                except Exception as e:
                    print(f"❌ Analysis failed: {e}")
            else:
                print("❌ Please enter a username")
            break
            
        else:
            print("❌ Invalid choice. Please select 1-4.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("💡 Try running: python start_here.py")
