"""
Setup Open WebUI for Chess Strategy AI
Installs and configures Open WebUI with our chess analysis backend
"""

import os
import subprocess
import sys
import time
import json
import platform

def run_command(command, shell=True):
    """Run a command and return success status"""
    try:
        result = subprocess.run(
            command, 
            shell=shell, 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_docker_installed():
    """Check if Docker is installed"""
    success, _, _ = run_command("docker --version")
    return success

def check_node_installed():
    """Check if Node.js is installed"""
    success, _, _ = run_command("node --version")
    return success

def install_openwebui_docker():
    """Install Open WebUI using Docker"""
    print("🐳 Installing Open WebUI using Docker...")
    
    # Pull the Open WebUI image
    print("📥 Pulling Open WebUI Docker image...")
    success, stdout, stderr = run_command("docker pull ghcr.io/open-webui/open-webui:main")
    
    if not success:
        print(f"❌ Failed to pull Docker image: {stderr}")
        return False
    
    print("✅ Open WebUI Docker image pulled successfully")
    return True

def create_openwebui_config():
    """Create configuration for Open WebUI"""
    config = {
        "chess_ai_backend": {
            "url": "http://localhost:8000",
            "name": "Chess Strategy AI",
            "description": "AI-powered chess strategy generation"
        },
        "setup_date": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open("openwebui_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("✅ Open WebUI configuration created")

def create_docker_compose():
    """Create docker-compose.yml for easy setup"""
    docker_compose_content = """version: '3.8'

services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: chess-strategy-webui
    ports:
      - "3000:8080"
    environment:
      - OLLAMA_BASE_URL=http://host.docker.internal:11434
      - WEBUI_SECRET_KEY=chess-strategy-secret-key-2025
      - ENABLE_COMMUNITY_SHARING=false
      - ENABLE_ADMIN_EXPORT=true
    volumes:
      - chess-webui-data:/app/backend/data
    extra_hosts:
      - "host.docker.internal:host-gateway"
    restart: unless-stopped
    networks:
      - chess-ai-network

  chess-backend:
    build: .
    container_name: chess-strategy-backend
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_URL=http://host.docker.internal:11434
    volumes:
      - .:/app
    working_dir: /app
    command: python openwebui_backend.py
    depends_on:
      - open-webui
    extra_hosts:
      - "host.docker.internal:host-gateway"
    restart: unless-stopped
    networks:
      - chess-ai-network

volumes:
  chess-webui-data:

networks:
  chess-ai-network:
    driver: bridge
"""
    
    with open("docker-compose.yml", "w") as f:
        f.write(docker_compose_content)
    
    print("✅ Docker Compose configuration created")

def create_dockerfile():
    """Create Dockerfile for the chess backend"""
    dockerfile_content = """FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "openwebui_backend.py"]
"""
    
    with open("Dockerfile", "w") as f:
        f.write(dockerfile_content)
    
    print("✅ Dockerfile created")

def setup_openwebui_standalone():
    """Setup Open WebUI as standalone (without Docker)"""
    print("🔧 Setting up Open WebUI standalone...")
    
    # Create a simple launcher script
    launcher_content = f"""#!/usr/bin/env python
\"\"\"
Chess Strategy AI Launcher
Starts both the backend and provides instructions for Open WebUI
\"\"\"

import subprocess
import time
import webbrowser
from threading import Thread

def start_backend():
    print("🚀 Starting Chess Strategy AI Backend...")
    subprocess.run(["python", "openwebui_backend.py"])

def main():
    print("🏛️ Chess Strategy AI - Open WebUI Integration")
    print("=" * 60)
    
    # Start backend in background
    backend_thread = Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    time.sleep(3)
    
    print("✅ Backend started on http://localhost:8000")
    print()
    print("📋 OPEN WEBUI SETUP INSTRUCTIONS:")
    print("=" * 40)
    print("1. Install Open WebUI:")
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
    
    # Keep the backend running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\\n👋 Shutting down Chess Strategy AI...")

if __name__ == "__main__":
    main()
"""
    
    with open("launch_openwebui.py", "w") as f:
        f.write(launcher_content)
    
    print("✅ Open WebUI launcher created")

def main():
    print("🏛️ Chess Strategy AI - Open WebUI Setup")
    print("=" * 50)
    
    # Create necessary files
    create_openwebui_config()
    create_dockerfile()
    create_docker_compose()
    setup_openwebui_standalone()
    
    print("\n🔍 Checking system requirements...")
    
    docker_available = check_docker_installed()
    node_available = check_node_installed()
    
    print(f"Docker: {'✅ Available' if docker_available else '❌ Not found'}")
    print(f"Node.js: {'✅ Available' if node_available else '❌ Not found'}")
    
    print("\n📋 SETUP OPTIONS:")
    print("=" * 30)
    print("1. Docker Setup (Recommended)")
    print("2. Standalone Setup")
    print("3. Manual Setup")
    
    while True:
        choice = input("\nSelect setup option (1-3): ").strip()
        
        if choice == "1":
            if docker_available:
                print("\n🐳 Docker Setup Selected")
                if install_openwebui_docker():
                    print("\n" + "=" * 50)
                    print("🎉 Docker Setup Complete!")
                    print("=" * 50)
                    print("🚀 To start the system:")
                    print("   docker-compose up -d")
                    print()
                    print("🌐 Open your browser:")
                    print("   http://localhost:3000")
                    print()
                    print("🔧 In Open WebUI settings:")
                    print("   - Add API connection:")
                    print("   - URL: http://chess-backend:8000")
                    print("   - Key: chess-strategy-key")
                    print()
                    print("💡 Then type: 'Analyze player magnus'")
                break
            else:
                print("❌ Docker not available. Please install Docker first.")
                
        elif choice == "2":
            print("\n🔧 Standalone Setup Selected")
            print("\n" + "=" * 50)
            print("🎉 Standalone Setup Complete!")
            print("=" * 50)
            print("🚀 To start the system:")
            print("   python launch_openwebui.py")
            print()
            print("💡 Follow the instructions shown by the launcher")
            break
            
        elif choice == "3":
            print("\n📖 Manual Setup Instructions")
            print("=" * 30)
            print("1. Install Open WebUI:")
            print("   pip install open-webui")
            print()
            print("2. Start Chess AI Backend:")
            print("   python openwebui_backend.py")
            print()
            print("3. Start Open WebUI:")
            print("   open-webui serve --port 3000")
            print()
            print("4. Configure API in Open WebUI:")
            print("   - URL: http://localhost:8000")
            print("   - Key: chess-strategy-key")
            print()
            print("5. Start analyzing players!")
            break
            
        else:
            print("❌ Invalid choice. Please select 1-3.")
    
    print("\n🏆 Open WebUI integration ready!")
    print("Now you can analyze any chess player with a modern interface!")

if __name__ == "__main__":
    main()
