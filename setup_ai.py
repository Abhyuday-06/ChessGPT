#!/usr/bin/env python3
"""
Chess Strategy AI Setup and Training Script
Complete pipeline for training and deploying the chess strategy AI
"""

import subprocess
import sys
import os
from datetime import datetime

def install_requirements():
    """Install required packages"""
    print("📦 Installing requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def check_training_data():
    """Check if training data exists and is sufficient"""
    print("📊 Checking training data...")
    
    if not os.path.exists("chess_strategy_training_data.json"):
        print("❌ No training data found!")
        print("📝 Please run chess_analyzer.py with different usernames to generate training data")
        return False
    
    try:
        import json
        with open("chess_strategy_training_data.json", 'r') as f:
            data = json.load(f)
        
        if len(data) < 5:
            print(f"⚠️  Only {len(data)} training examples found")
            print("📝 Recommend at least 10+ examples for better training")
            print("📝 Run: python chess_analyzer.py <username> for more players")
            
            response = input("Continue with limited data? (y/n): ").lower()
            if response != 'y':
                return False
        else:
            print(f"✅ Found {len(data)} training examples")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading training data: {e}")
        return False

def train_model():
    """Train the chess strategy model"""
    print("🎯 Starting model training...")
    try:
        subprocess.check_call([sys.executable, "train_llm.py"])
        print("✅ Model training completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Training failed: {e}")
        return False

def test_inference():
    """Test the inference engine"""
    print("🧪 Testing inference engine...")
    try:
        from inference_engine import ChessStrategyPredictor
        predictor = ChessStrategyPredictor()
        print("✅ Inference engine loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Inference engine test failed: {e}")
        return False

def start_web_ui():
    """Start the web UI"""
    print("🌐 Starting Chess Strategy Web UI...")
    try:
        subprocess.check_call([sys.executable, "web_ui.py"])
    except KeyboardInterrupt:
        print("\n👋 Web UI stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Web UI failed: {e}")

def main():
    """Main setup and training pipeline"""
    print("🏁 Chess Strategy AI Setup")
    print("=" * 50)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Install requirements
    if not install_requirements():
        return
    
    # Step 2: Check training data
    if not check_training_data():
        print("\n📝 To generate training data:")
        print("   python chess_analyzer.py hikaru")
        print("   python chess_analyzer.py magnus") 
        print("   python chess_analyzer.py levy")
        print("   python chess_analyzer.py <other_username>")
        return
    
    # Step 3: Ask user what they want to do
    print("\n🎯 What would you like to do?")
    print("1. Train the model (recommended for first time)")
    print("2. Skip training and start web UI (if model already trained)")
    print("3. Train model and start web UI")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        if train_model():
            print("\n🎉 Training completed! Run the script again and choose option 2 to start the web UI.")
        
    elif choice == "2":
        if test_inference():
            start_web_ui()
        else:
            print("❌ Please train the model first (option 1)")
    
    elif choice == "3":
        if train_model() and test_inference():
            start_web_ui()
    
    elif choice == "4":
        print("👋 Goodbye!")
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
