#!/usr/bin/env python
"""
Chess Strategy AI - Quick Start Guide
Your complete Chess Strategy AI system is now ready!
"""

import os
import sys
import json
import subprocess
from datetime import datetime

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

def print_header():
    """Print header"""
    colored_print("🏛️ Chess Strategy AI - READY TO USE!", "cyan")
    colored_print("=" * 60, "cyan")
    
def show_system_status():
    """Show system status"""
    colored_print("\n📊 SYSTEM STATUS", "cyan")
    colored_print("-" * 30, "cyan")
    
    # Check training data
    if os.path.exists("chess_strategy_training_data.json"):
        try:
            with open("chess_strategy_training_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            colored_print(f"✅ Training data: {len(data)} entries", "green")
        except:
            colored_print("⚠️ Training data: Error loading", "yellow")
    else:
        colored_print("❌ Training data: Not found", "red")
    
    # Check PGN files
    pgn_files = ["chess_com_games.pgn", "lichess_games.pgn"]
    for pgn_file in pgn_files:
        if os.path.exists(pgn_file):
            size = os.path.getsize(pgn_file)
            colored_print(f"✅ {pgn_file}: {size} bytes", "green")
        else:
            colored_print(f"⚠️ {pgn_file}: Not found", "yellow")
    
    # Check Ollama
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if result.returncode == 0:
            colored_print("✅ Ollama: Running", "green")
        else:
            colored_print("⚠️ Ollama: Not running", "yellow")
    except:
        colored_print("❌ Ollama: Not installed", "red")
    
    # Check Stockfish
    stockfish_paths = ["stockfish/stockfish.exe", "stockfish/stockfish"]
    stockfish_found = False
    for path in stockfish_paths:
        if os.path.exists(path):
            colored_print(f"✅ Stockfish: Found at {path}", "green")
            stockfish_found = True
            break
    
    if not stockfish_found:
        colored_print("⚠️ Stockfish: Not found", "yellow")

def show_usage_guide():
    """Show usage guide"""
    colored_print("\n🎯 HOW TO USE", "cyan")
    colored_print("-" * 30, "cyan")
    
    colored_print("\n1. 🌐 WEB INTERFACE (Recommended)", "blue")
    colored_print("   • Start: python enhanced_web_ui.py", "white")
    colored_print("   • Open: http://localhost:5000", "white")
    colored_print("   • Features: Full GUI, real-time progress, strategy generation", "white")
    
    colored_print("\n2. 💻 COMMAND LINE INTERFACE", "blue")
    colored_print("   • Interactive: python chess_cli.py", "white")
    colored_print("   • Direct analysis: python chess_analyzer.py <username>", "white")
    colored_print("   • Get strategy: python chess_cli.py strategy <username>", "white")
    
    colored_print("\n3. 📊 ANALYSIS WORKFLOW", "blue")
    colored_print("   Step 1: Enter username (e.g., 'hikaru', 'magnus')", "white")
    colored_print("   Step 2: Select platform (Chess.com/Lichess/Auto)", "white")
    colored_print("   Step 3: Wait for download & analysis", "white")
    colored_print("   Step 4: Get AI-generated strategy", "white")

def show_examples():
    """Show example commands"""
    colored_print("\n📝 EXAMPLES", "cyan")
    colored_print("-" * 30, "cyan")
    
    colored_print("# Analyze a new player", "blue")
    colored_print("python chess_analyzer.py hikaru", "white")
    
    colored_print("\n# Get strategy for analyzed player", "blue")
    colored_print("python chess_cli.py strategy hikaru", "white")
    
    colored_print("\n# Start web interface", "blue")
    colored_print("python enhanced_web_ui.py", "white")
    
    colored_print("\n# Interactive CLI", "blue")
    colored_print("python chess_cli.py", "white")

def show_features():
    """Show system features"""
    colored_print("\n✨ FEATURES", "cyan")
    colored_print("-" * 30, "cyan")
    
    features = [
        "🔍 Auto-download games from Chess.com & Lichess",
        "🧠 Stockfish analysis (up to 20 ply/10 moves)",
        "📊 Weakness detection & pattern recognition",
        "🤖 AI strategy generation using Ollama Gemma2",
        "📝 Training data creation for fine-tuning",
        "🌐 Modern web interface with real-time updates",
        "💻 Command-line interface for power users",
        "🎯 Personalized counter-strategies",
        "📈 Continuous learning from new players"
    ]
    
    for feature in features:
        colored_print(f"  {feature}", "white")

def main():
    """Main function"""
    print_header()
    show_system_status()
    show_usage_guide()
    show_examples()
    show_features()
    
    colored_print("\n🚀 GETTING STARTED", "cyan")
    colored_print("-" * 30, "cyan")
    colored_print("1. Start the web UI: python enhanced_web_ui.py", "yellow")
    colored_print("2. Open http://localhost:5000 in your browser", "yellow")
    colored_print("3. Enter a chess username to analyze", "yellow")
    colored_print("4. Get AI-powered strategies!", "yellow")
    
    colored_print("\n🎉 Your Chess Strategy AI is ready!", "green")
    colored_print("For help, run: python chess_cli.py help", "blue")

if __name__ == "__main__":
    main()
