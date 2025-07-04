import os
import platform
import requests
import zipfile
from pathlib import Path

def download_stockfish():
    """Download and extract Stockfish engine"""
    print("Setting up Stockfish engine...")
    
    # Create stockfish directory
    stockfish_dir = Path("stockfish")
    stockfish_dir.mkdir(exist_ok=True)
    
    # Determine system and download URL
    system = platform.system().lower()
    
    if system == "windows":
        url = "https://github.com/official-stockfish/Stockfish/releases/download/sf_16.1/stockfish-windows-x86-64-avx2.zip"
        executable_name = "stockfish.exe"
    elif system == "darwin":  # macOS
        url = "https://github.com/official-stockfish/Stockfish/releases/download/sf_16.1/stockfish-macos-x86-64-modern.zip"
        executable_name = "stockfish"
    else:  # Linux
        url = "https://github.com/official-stockfish/Stockfish/releases/download/sf_16.1/stockfish-ubuntu-x86-64-avx2.zip"
        executable_name = "stockfish"
    
    zip_path = stockfish_dir / "stockfish.zip"
    
    # Check if already exists
    executable_path = stockfish_dir / executable_name
    if executable_path.exists():
        print(f"Stockfish already exists at {executable_path}")
        return str(executable_path)
    
    print(f"Downloading Stockfish from {url}...")
    
    try:
        # Download the file
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print("Download complete. Extracting...")
        
        # Extract the zip file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(stockfish_dir)
        
        # Find the executable in the extracted files
        for root, dirs, files in os.walk(stockfish_dir):
            for file in files:
                if file.startswith("stockfish") and (file.endswith(".exe") or "exe" not in file):
                    source_path = Path(root) / file
                    target_path = stockfish_dir / executable_name
                    
                    # Move the executable to the stockfish directory
                    if source_path != target_path:
                        source_path.rename(target_path)
                    
                    # Make it executable on Unix systems
                    if system != "windows":
                        os.chmod(target_path, 0o755)
                    
                    print(f"Stockfish engine ready at {target_path}")
                    
                    # Clean up
                    zip_path.unlink()
                    
                    return str(target_path)
        
        print("Error: Stockfish executable not found in the downloaded archive")
        return None
        
    except Exception as e:
        print(f"Error downloading Stockfish: {e}")
        return None

def test_stockfish(executable_path):
    """Test if Stockfish is working"""
    try:
        from stockfish import Stockfish
        sf = Stockfish(path=executable_path)
        sf.set_position(["e2e4", "e7e5"])
        evaluation = sf.get_evaluation()
        print(f"Stockfish test successful! Evaluation: {evaluation}")
        return True
    except Exception as e:
        print(f"Stockfish test failed: {e}")
        return False

if __name__ == "__main__":
    executable_path = download_stockfish()
    if executable_path and test_stockfish(executable_path):
        print(f"✅ Stockfish setup complete!")
        print(f"Executable path: {executable_path}")
    else:
        print("❌ Stockfish setup failed")
