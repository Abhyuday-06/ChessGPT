#!/usr/bin/env python
"""
Chess Strategy AI Launcher for Open WebUI
Starts both the backend and provides instructions for Open WebUI
"""

import subprocess
import time
import webbrowser
import sys
import os
from threading import Thread
import signal

def start_backend():
    """Start the Chess Strategy AI backend"""
    print("🚀 Starting Chess Strategy AI Backend...")
    try:
        subprocess.run([sys.executable, "openwebui_backend.py"])
    except KeyboardInterrupt:
        print("\n👋 Backend stopped by user")
    except Exception as e:
        print(f"❌ Backend error: {e}")

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
        except Exception as e:
            print(f"⚠️ Could not start Ollama: {e}")
            print("Please start Ollama manually: ollama serve")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n👋 Shutting down Chess Strategy AI...")
    sys.exit(0)

def main():
    print("🏛️ Chess Strategy AI - Open WebUI Integration")
    print("=" * 60)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check and start Ollama if needed
    start_ollama()
    
    # Start backend in background
    backend_thread = Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    time.sleep(3)
    
    print("✅ Chess Strategy AI Backend started on http://localhost:8000")
    print()
    print("📋 OPEN WEBUI SETUP INSTRUCTIONS:")
    print("=" * 40)
    print("1. Install Open WebUI (if not already installed):")
    print("   pip install open-webui")
    print()
    print("2. Start Open WebUI:")
    print("   open-webui serve --port 3000")
    print()
    print("3. Open your browser:")
    print("   http://localhost:3000")
    print()
    print("4. In Open WebUI settings:")
    print("   - Go to Admin Panel > Settings > Connections")
    print("   - Add OpenAI API:")
    print("     * API Base URL: http://localhost:8000")
    print("     * API Key: chess-strategy-key")
    print("   - Save and refresh")
    print()
    print("5. Start chatting:")
    print("   - Type: 'Analyze player hikaru'")
    print("   - Watch the real-time analysis!")
    print()
    print("🎯 The Chess Strategy AI is now integrated with Open WebUI!")
    print("💡 You can analyze any chess player and get AI strategies!")
    print()
    print("🔄 Backend is running... Press Ctrl+C to stop")
    
    # Keep the backend running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down Chess Strategy AI...")

if __name__ == "__main__":
    main()
