#!/usr/bin/env python
"""
Chess Strategy AI - Complete Setup and Launcher
One-stop solution for running the Chess Strategy AI with Open WebUI
"""

import subprocess
import time
import webbrowser
import sys
import os
from threading import Thread
import signal
import json
import platform

def run_command(command, shell=True, timeout=30):
    """Run a command and return success status"""
    try:
        result = subprocess.run(
            command, 
            shell=shell, 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_ollama_running():
    """Check if Ollama is running"""
    success, stdout, stderr = run_command("ollama list", timeout=10)
    return success

def start_ollama():
    """Start Ollama if not running"""
    if not check_ollama_running():
        print("🔄 Starting Ollama...")
        try:
            if os.name == 'nt':  # Windows
                subprocess.Popen(["ollama", "serve"], shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:  # Unix-like
                subprocess.Popen(["ollama", "serve"])
            time.sleep(8)
            
            # Verify it started
            if check_ollama_running():
                print("✅ Ollama is running")
            else:
                print("⚠️ Ollama may not have started properly")
        except Exception as e:
            print(f"⚠️ Could not start Ollama: {e}")
            print("Please start Ollama manually: ollama serve")

def install_open_webui():
    """Install Open WebUI if not already installed"""
    print("📦 Checking Open WebUI installation...")
    
    # Check if open-webui is installed
    success, stdout, stderr = run_command("open-webui --version", timeout=10)
    
    if not success:
        print("🔄 Installing Open WebUI...")
        
        # Try multiple installation methods
        install_commands = [
            "pip install open-webui",
            "pip install --upgrade pip && pip install open-webui",
            "pip install open-webui --no-cache-dir",
            "pip install git+https://github.com/open-webui/open-webui.git"
        ]
        
        for i, cmd in enumerate(install_commands):
            print(f"   Trying method {i+1}/4: {cmd.split('&&')[-1].strip()}")
            success, stdout, stderr = run_command(cmd, timeout=300)
            
            if success:
                print("✅ Open WebUI installed successfully")
                return True
            else:
                print(f"   ❌ Method {i+1} failed: {stderr[:100]}...")
        
        print("❌ All installation methods failed")
        print("💡 Manual installation options:")
        print("   1. Docker: docker run -d -p 3000:8080 ghcr.io/open-webui/open-webui:main")
        print("   2. Manual pip: pip install --upgrade pip setuptools wheel && pip install open-webui")
        print("   3. Use the simple UI instead (option 1 in main menu)")
        return False
    else:
        print("✅ Open WebUI is already installed")
    
    return True

def start_backend():
    """Start the Chess Strategy AI backend"""
    print("🚀 Starting Chess Strategy AI Backend...")
    try:
        subprocess.run([sys.executable, "openwebui_backend.py"])
    except KeyboardInterrupt:
        print("\n👋 Backend stopped by user")
    except Exception as e:
        print(f"❌ Backend error: {e}")

def start_open_webui():
    """Start Open WebUI in a separate process"""
    print("🌐 Starting Open WebUI...")
    try:
        if os.name == 'nt':  # Windows
            subprocess.Popen(
                ["open-webui", "serve", "--port", "3000"],
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:  # Unix-like
            subprocess.Popen(["open-webui", "serve", "--port", "3000"])
        
        print("✅ Open WebUI started on http://localhost:3000")
        return True
    except Exception as e:
        print(f"❌ Failed to start Open WebUI: {e}")
        return False

def open_browser():
    """Open the browser after a delay"""
    time.sleep(10)
    try:
        webbrowser.open("http://localhost:3000")
        print("🌐 Browser opened to http://localhost:3000")
    except Exception as e:
        print(f"⚠️ Could not open browser: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n👋 Shutting down Chess Strategy AI...")
    sys.exit(0)

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def main():
    print("🏛️ Chess Strategy AI - Complete Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🔍 Checking system requirements...")
    
    # Check and start Ollama
    start_ollama()
    
    # Install Open WebUI if needed
    if not install_open_webui():
        print("\n⚠️ Open WebUI installation failed, but you can still use the Chess Strategy AI!")
        print("🎯 Alternative options:")
        print("   1. Use Simple Single-Input UI: python single_input_ui.py")
        print("   2. Use Enhanced Web UI: python enhanced_web_ui.py")
        print("   3. Use OpenWebUI Backend only: python openwebui_backend.py")
        print("   4. Try Docker: docker run -d -p 3000:8080 ghcr.io/open-webui/open-webui:main")
        
        choice = input("\n🔧 Start Simple UI instead? (y/n): ").lower().strip()
        if choice in ['y', 'yes']:
            print("🚀 Starting Simple Single-Input UI...")
            try:
                subprocess.run([sys.executable, "single_input_ui.py"])
            except KeyboardInterrupt:
                print("\n👋 Simple UI stopped by user")
        return
    
    print("\n🚀 Starting services...")
    
    # Start backend in background
    backend_thread = Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    time.sleep(5)
    print("✅ Chess Strategy AI Backend started on http://localhost:8000")
    
    # Start Open WebUI
    if start_open_webui():
        time.sleep(3)
        
        # Open browser in background
        browser_thread = Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        print("\n" + "=" * 50)
        print("🎉 SETUP COMPLETE!")
        print("=" * 50)
        print("🌐 Open WebUI: http://localhost:3000")
        print("🔧 Backend API: http://localhost:8000")
        print()
        print("📋 CONFIGURATION STEPS:")
        print("1. Open your browser (should open automatically)")
        print("2. In Open WebUI settings:")
        print("   - Go to Admin Panel > Settings > Connections")
        print("   - Add OpenAI API:")
        print("     * API Base URL: http://localhost:8000")
        print("     * API Key: chess-strategy-key")
        print("   - Save and refresh")
        print()
        print("🎯 USAGE:")
        print("   - Type: 'Analyze player hikaru'")
        print("   - Type: 'Generate strategy for magnus'")
        print("   - Watch the real-time analysis!")
        print()
        print("🔄 Services are running... Press Ctrl+C to stop")
    else:
        print("❌ Failed to start Open WebUI")
        return
    
    # Keep the services running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down Chess Strategy AI...")

if __name__ == "__main__":
    main()
