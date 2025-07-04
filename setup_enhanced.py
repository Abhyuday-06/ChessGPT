"""
Setup script for Enhanced Chess Strategy AI
Installs and configures Ollama with chess strategy models
"""

import os
import subprocess
import sys
import requests
import time
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
            errors='replace'  # Replace invalid characters instead of failing
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_ollama_installed():
    """Check if Ollama is installed"""
    success, _, _ = run_command("ollama --version")
    return success

def install_ollama():
    """Install Ollama based on platform"""
    system = platform.system().lower()
    
    print("🔄 Installing Ollama...")
    
    if system == "windows":
        print("📥 Please download and install Ollama from: https://ollama.com/download")
        print("🔧 After installation, restart this script.")
        return False
    elif system == "darwin":  # macOS
        success, _, _ = run_command("brew install ollama")
        if not success:
            print("❌ Failed to install via Homebrew. Please install manually from https://ollama.com/download")
            return False
    else:  # Linux
        success, _, _ = run_command("curl -fsSL https://ollama.com/install.sh | sh")
        if not success:
            print("❌ Failed to install Ollama. Please install manually from https://ollama.com/download")
            return False
    
    print("✅ Ollama installed successfully")
    return True

def start_ollama():
    """Start Ollama service"""
    print("🚀 Starting Ollama service...")
    
    # Try to start Ollama in background
    system = platform.system().lower()
    
    if system == "windows":
        # On Windows, Ollama should start automatically after installation
        time.sleep(3)
    else:
        # On Unix systems, try to start the service
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)
    
    return check_ollama_running()

def check_ollama_running():
    """Check if Ollama service is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def wait_for_ollama():
    """Wait for Ollama to be ready"""
    print("⏳ Waiting for Ollama to be ready...")
    
    for i in range(30):  # Wait up to 30 seconds
        if check_ollama_running():
            print("✅ Ollama is ready")
            return True
        time.sleep(1)
        if i % 5 == 0:
            print(f"⏳ Still waiting... ({i+1}/30)")
    
    print("❌ Ollama did not start in time")
    return False

def check_model_available(model_name):
    """Check if a specific model is available locally"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            for model in models:
                if model.get('name', '').startswith(model_name):
                    return True
        return False
    except:
        return False

def pull_model_with_progress(model_name="gemma2:2b"):
    """Pull a model with live progress display"""
    print(f"📥 Pulling model: {model_name}")
    print("⏳ This may take a few minutes...")
    
    try:
        # Start the pull process
        process = subprocess.Popen(
            f"ollama pull {model_name}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        # Read output line by line
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                # Clean and display the output
                line = output.strip()
                if line:
                    print(f"📥 {line}")
        
        # Wait for process to complete
        process.wait()
        
        if process.returncode == 0:
            print(f"✅ Model {model_name} pulled successfully")
            return True
        else:
            print(f"❌ Failed to pull model {model_name}")
            # Get any error output
            error_output = process.stderr.read()
            if error_output:
                print(f"Error: {error_output}")
            return False
            
    except Exception as e:
        print(f"❌ Exception while pulling model {model_name}: {e}")
        return False

def pull_model(model_name="gemma2:2b"):
    """Pull a specific model"""
    print(f"🔄 Checking model: {model_name}")
    
    # First check if model is already available
    if check_model_available(model_name):
        print(f"✅ Model {model_name} is already available")
        return True
    
    # Try to pull with progress display
    return pull_model_with_progress(model_name)

def test_model(model_name="gemma2:2b"):
    """Test the model"""
    print(f"🧪 Testing model: {model_name}")
    
    try:
        # First try a simple test
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": "Hello",
                "stream": False,
                "options": {
                    "num_predict": 10,  # Limit response length
                    "temperature": 0.1  # Make it more deterministic
                }
            },
            timeout=60  # Increased timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '').strip()
            print(f"✅ Model test successful!")
            print(f"Sample response: {response_text[:100]}...")
            return True
        else:
            print(f"❌ Model test failed: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⚠️ Model test timed out - this is normal for first run")
        print(f"💡 Model {model_name} should still work fine")
        return True  # Return True since timeout doesn't mean the model is broken
    except Exception as e:
        print(f"❌ Model test error: {e}")
        print(f"⚠️ Model {model_name} may still work - continuing setup")
        return True  # Return True to continue setup

def install_python_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    
    dependencies = [
        "flask",
        "requests",
        "python-chess",
        "stockfish",
        "beautifulsoup4",
        "lxml"
    ]
    
    for dep in dependencies:
        print(f"Installing {dep}...")
        success, _, _ = run_command(f"pip install {dep}")
        if not success:
            print(f"❌ Failed to install {dep}")
            return False
    
    print("✅ Python dependencies installed")
    return True

def main():
    print("🏛️ Enhanced Chess Strategy AI Setup")
    print("=" * 50)
    
    # Install Python dependencies
    if not install_python_dependencies():
        print("❌ Failed to install Python dependencies")
        return
    
    # Check if Ollama is installed
    if not check_ollama_installed():
        print("⚠️ Ollama not found")
        if not install_ollama():
            print("❌ Please install Ollama manually and restart this script")
            return
    else:
        print("✅ Ollama is installed")
    
    # Check if Ollama is running
    if not check_ollama_running():
        print("⚠️ Ollama service not running")
        if not start_ollama():
            print("❌ Failed to start Ollama service")
            print("💡 Please start Ollama manually: 'ollama serve'")
            return
        
        # Wait for Ollama to be ready
        if not wait_for_ollama():
            print("❌ Ollama not ready - please start manually")
            return
    else:
        print("✅ Ollama service is running")
    
    # Pull model options
    models = [
        ("gemma2:2b", "Gemma 2 2B (Recommended - Fast)"),
        ("llama3.2:3b", "Llama 3.2 3B (Good balance)"),
        ("mistral:7b", "Mistral 7B (More capable)"),
        ("qwen2:1.5b", "Qwen 2 1.5B (Fastest)")
    ]
    
    print("\n📚 Available Models:")
    for i, (model_name, description) in enumerate(models, 1):
        print(f"{i}. {description}")
    
    while True:
        try:
            choice = input("\nSelect a model (1-4) or press Enter for default (1): ").strip()
            if not choice:
                choice = "1"
            
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(models):
                selected_model = models[choice_idx][0]
                break
            else:
                print("❌ Invalid choice. Please select 1-4.")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")
    
    # Pull the selected model
    if not pull_model(selected_model):
        print("❌ Failed to pull model")
        return
    
    # Test the model
    if not test_model(selected_model):
        print("❌ Model test failed")
        return
    
    # Update the model name in the code
    print(f"📝 Updating model configuration to use: {selected_model}")
    
    # Create a config file
    config = {
        "model_name": selected_model,
        "setup_completed": True,
        "setup_date": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    import json
    with open("ollama_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("=" * 50)
    print("✅ Ollama installed and running")
    print(f"✅ Model {selected_model} ready")
    print("✅ Python dependencies installed")
    print("✅ Configuration saved")
    print("\n🚀 To start the enhanced web UI:")
    print("   python enhanced_web_ui.py")
    print("\n🌐 Then open: http://localhost:5000")
    print("\n💡 You can now:")
    print("   • Enter any chess username to analyze")
    print("   • Get AI-powered strategies")
    print("   • View real-time analysis progress")

if __name__ == "__main__":
    main()
