#!/usr/bin/env python
"""
Chess Strategy AI - All-in-One Launcher
The ultimate launcher that handles setup, verification, and running
"""

import sys
import os
import subprocess
import time
import json
from threading import Thread

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def colored_print(text, color="white"):
    """Print colored text"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, '')}{text}{colors['reset']}")

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

def quick_verify():
    """Quick verification of essential components"""
    print("🔍 Quick system check...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        colored_print("❌ Python 3.8+ required", "red")
        return False
    
    # Check Ollama
    success, _, _ = run_command("ollama --version", timeout=5)
    if not success:
        colored_print("⚠️ Ollama not installed", "yellow")
        return False
    
    # Check if Ollama is running
    success, _, _ = run_command("ollama list", timeout=5)
    if not success:
        colored_print("⚠️ Ollama not running", "yellow")
        return False
    
    # Check core files
    core_files = ["chess_analyzer.py", "ollama_llm.py", "single_input_ui.py"]
    for file in core_files:
        if not os.path.exists(file):
            colored_print(f"❌ Missing {file}", "red")
            return False
    
    colored_print("✅ Basic components ready", "green")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    success, stdout, stderr = run_command("pip install -r requirements.txt", timeout=120)
    
    if success:
        colored_print("✅ Dependencies installed", "green")
        return True
    else:
        colored_print(f"❌ Failed to install dependencies: {stderr}", "red")
        return False

def setup_ollama():
    """Setup Ollama if needed"""
    print("🤖 Setting up Ollama...")
    
    # Check if Ollama is installed
    success, _, _ = run_command("ollama --version")
    if not success:
        colored_print("❌ Ollama not installed", "red")
        colored_print("💡 Please install Ollama from https://ollama.ai/", "yellow")
        return False
    
    # Check if Ollama is running
    success, _, _ = run_command("ollama list")
    if not success:
        print("🔄 Starting Ollama...")
        if os.name == 'nt':  # Windows
            subprocess.Popen(["ollama", "serve"], shell=True)
        else:
            subprocess.Popen(["ollama", "serve"])
        time.sleep(5)
    
    # Check for models
    success, stdout, stderr = run_command("ollama list")
    if success:
        if "llama" in stdout.lower() or "gemma" in stdout.lower() or "mistral" in stdout.lower():
            colored_print("✅ Ollama models available", "green")
            return True
        else:
            print("🔄 No models found. Installing llama3.1:8b...")
            success, _, _ = run_command("ollama pull llama3.1:8b", timeout=300)
            if success:
                colored_print("✅ Model installed", "green")
                return True
            else:
                colored_print("❌ Failed to install model", "red")
                return False
    
    return False

def auto_setup():
    """Automatic setup process"""
    colored_print("🔧 Starting automatic setup...", "cyan")
    
    steps = [
        ("Installing dependencies", install_dependencies),
        ("Setting up Ollama", setup_ollama)
    ]
    
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if not step_func():
            colored_print(f"❌ {step_name} failed", "red")
            return False
    
    colored_print("✅ Automatic setup complete!", "green")
    return True

def launch_interface(choice):
    """Launch the selected interface"""
    interfaces = {
        "1": {
            "name": "Simple Single-Input UI",
            "file": "single_input_ui.py",
            "url": "http://localhost:5001",
            "description": "One input field, real-time progress"
        },
        "2": {
            "name": "Open WebUI Backend",
            "file": "openwebui_backend.py",
            "url": "http://localhost:8000",
            "description": "API for Open WebUI integration"
        },
        "3": {
            "name": "Enhanced Web UI",
            "file": "enhanced_web_ui.py",
            "url": "http://localhost:5000",
            "description": "Full-featured web interface"
        },
        "4": {
            "name": "Simple Launcher",
            "file": "simple_launcher.py",
            "url": "Multiple options",
            "description": "Quick launcher without Open WebUI dependency"
        },
        "5": {
            "name": "Complete Setup",
            "file": "chess_ai_complete.py",
            "url": "http://localhost:3000",
            "description": "Automated Open WebUI setup"
        }
    }
    
    if choice not in interfaces:
        colored_print("❌ Invalid choice", "red")
        return False
    
    interface = interfaces[choice]
    
    if not os.path.exists(interface["file"]):
        colored_print(f"❌ {interface['file']} not found", "red")
        return False
    
    colored_print(f"🚀 Starting {interface['name']}...", "cyan")
    colored_print(f"🌐 Will be available at: {interface['url']}", "blue")
    
    try:
        subprocess.run([sys.executable, interface["file"]])
        return True
    except KeyboardInterrupt:
        colored_print(f"\n👋 {interface['name']} stopped by user", "yellow")
        return True
    except Exception as e:
        colored_print(f"❌ Failed to start {interface['name']}: {e}", "red")
        return False

def main():
    colored_print("🏛️ Chess Strategy AI - All-in-One Launcher", "cyan")
    colored_print("=" * 60, "cyan")
    
    # Quick verification
    if not quick_verify():
        colored_print("⚠️ System needs setup", "yellow")
        
        setup_choice = input("🔧 Run automatic setup? (y/n): ").lower().strip()
        if setup_choice in ['y', 'yes']:
            if not auto_setup():
                colored_print("❌ Setup failed. Please check the errors above.", "red")
                return
        else:
            colored_print("💡 Manual setup required:", "yellow")
            colored_print("   1. Install dependencies: pip install -r requirements.txt", "white")
            colored_print("   2. Install Ollama: https://ollama.ai/", "white")
            colored_print("   3. Start Ollama: ollama serve", "white")
            colored_print("   4. Pull model: ollama pull llama3.1:8b", "white")
            return
    
    # Show interface options
    print("\n🎯 Choose your interface:")
    colored_print("=" * 35, "cyan")
    
    options = [
        ("1", "🎨 Simple Single-Input UI", "One input field, real-time progress", "Recommended"),
        ("2", "🏛️ Open WebUI Backend", "API for Open WebUI integration", "Advanced"),
        ("3", "💻 Enhanced Web UI", "Full-featured web interface", "Power users"),
        ("4", "🚀 Simple Launcher", "Quick launcher without Open WebUI dependency", "Easy"),
        ("5", "🐳 Complete Setup", "Automated Open WebUI setup", "One-click"),
        ("6", "🔧 System Verification", "Run detailed system check", "Diagnostic"),
        ("7", "❓ Help", "Show help and documentation", "Support")
    ]
    
    for opt_num, opt_name, opt_desc, opt_tag in options:
        colored_print(f"{opt_num}. {opt_name}", "white")
        print(f"   {opt_desc}")
        colored_print(f"   [{opt_tag}]", "blue")
        print()
    
    while True:
        choice = input("Select option (1-7): ").strip()
        
        if choice in ["1", "2", "3", "4", "5"]:
            launch_interface(choice)
            break
        elif choice == "6":
            colored_print("🔍 Running system verification...", "cyan")
            try:
                subprocess.run([sys.executable, "verify_setup.py"])
            except Exception as e:
                colored_print(f"❌ Verification failed: {e}", "red")
        elif choice == "7":
            colored_print("📚 Help & Documentation", "cyan")
            colored_print("=" * 30, "cyan")
            colored_print("🎯 Usage:", "white")
            colored_print("   1. Choose interface (Simple UI recommended for beginners)", "white")
            colored_print("   2. Enter any chess username (e.g., 'hikaru', 'magnus')", "white")
            colored_print("   3. Watch real-time analysis and get AI strategies!", "white")
            print()
            colored_print("🔧 Troubleshooting:", "white")
            colored_print("   - Run option 6 for system verification", "white")
            colored_print("   - Check README.md for detailed instructions", "white")
            colored_print("   - Ensure Ollama is running: ollama serve", "white")
            print()
            colored_print("🌐 Interfaces:", "white")
            colored_print("   - Simple UI: http://localhost:5001", "white")
            colored_print("   - Enhanced UI: http://localhost:5000", "white")
            colored_print("   - Open WebUI: http://localhost:3000", "white")
            print()
            colored_print("💡 Quick Start:", "white")
            colored_print("   - Option 1: Simple UI (best for beginners)", "white")
            colored_print("   - Option 4: Simple Launcher (no Open WebUI needed)", "white")
            colored_print("   - Option 5: Complete Setup (if you want Open WebUI)", "white")
            print()
        else:
            colored_print("❌ Invalid choice. Please select 1-7.", "red")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        colored_print("\n👋 Goodbye!", "yellow")
    except Exception as e:
        colored_print(f"\n❌ Unexpected error: {e}", "red")
        colored_print("💡 Please report this issue with the error details above.", "yellow")
