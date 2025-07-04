#!/usr/bin/env python
"""
Chess Strategy AI - Command Line Interface
Provides both chess analysis and general chat capabilities
"""

import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chess_analyzer import ChessGameAnalyzer
from ollama_llm import chess_llm

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
    """Print application header"""
    colored_print("🏛️ Chess Strategy AI - CLI Interface", "cyan")
    colored_print("=" * 60, "cyan")
    colored_print("Commands:", "white")
    colored_print("  analyze <username> [platform] - Analyze a chess player", "blue")
    colored_print("  strategy <username>           - Get strategy for analyzed player", "blue")
    colored_print("  train                         - Train/fine-tune the model", "blue")
    colored_print("  chat <message>                - Chat with the AI", "blue")
    colored_print("  list                          - List analyzed players", "blue")
    colored_print("  help                          - Show this help", "blue")
    colored_print("  quit                          - Exit", "blue")
    colored_print("=" * 60, "cyan")

def analyze_player_cmd(args):
    """Analyze a chess player"""
    if len(args) < 1:
        colored_print("❌ Usage: analyze <username> [platform]", "red")
        return
    
    username = args[0]
    platform = args[1] if len(args) > 1 else "auto"
    
    colored_print(f"🔍 Analyzing {username} on {platform}...", "yellow")
    
    analyzer = ChessGameAnalyzer()
    success = analyzer.analyze_player(username, platform)
    
    if success:
        colored_print(f"✅ Analysis completed for {username}!", "green")
        colored_print("💡 Use 'strategy <username>' to get AI recommendations", "blue")
    else:
        colored_print(f"❌ Analysis failed for {username}", "red")

def get_strategy_cmd(args):
    """Get strategy for an analyzed player"""
    if len(args) < 1:
        colored_print("❌ Usage: strategy <username>", "red")
        return
    
    username = args[0]
    
    # Check if training data exists
    if not os.path.exists("chess_strategy_training_data.json"):
        colored_print("❌ No training data found. Please analyze some players first.", "red")
        return
    
    # Load training data to find player
    try:
        with open("chess_strategy_training_data.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        player_data = None
        for entry in data:
            if isinstance(entry, dict):
                player_name = entry.get('input', {}).get('opponent_profile', {}).get('player_name', '')
                if player_name.lower() == username.lower():
                    player_data = entry
                    break
        
        if not player_data:
            colored_print(f"❌ No analysis found for {username}. Use 'analyze {username}' first.", "red")
            return
        
        # Format analysis for LLM
        opponent_profile = player_data.get('input', {}).get('opponent_profile', {})
        weaknesses = player_data.get('input', {}).get('opponent_weaknesses', [])
        
        analysis_text = f"Chess Player Analysis: {username}\n\n"
        analysis_text += f"Player: {opponent_profile.get('player_name', username)}\n"
        analysis_text += f"Platform: {opponent_profile.get('platform', 'Unknown')}\n\n"
        
        analysis_text += "Identified Weaknesses:\n"
        for i, weakness in enumerate(weaknesses, 1):
            analysis_text += f"{i}. {weakness.get('weakness_type', 'Unknown')}\n"
            analysis_text += f"   Details: {weakness.get('details', '')}\n\n"
        
        analysis_text += "Please provide a comprehensive chess strategy to exploit these weaknesses."
        
        # Generate strategy
        colored_print(f"🤖 Generating strategy for {username}...", "yellow")
        strategy = chess_llm.generate_strategy(analysis_text)
        
        if strategy.startswith("Error"):
            colored_print(f"❌ {strategy}", "red")
        else:
            colored_print(f"\n🎯 Strategy for {username}:", "green")
            colored_print("=" * 40, "green")
            print(strategy)
            colored_print("=" * 40, "green")
        
    except Exception as e:
        colored_print(f"❌ Error generating strategy: {e}", "red")

def train_model_cmd():
    """Train/fine-tune the model"""
    colored_print("🎯 Training chess strategy model...", "yellow")
    
    success = chess_llm.fine_tune_model()
    
    if success:
        colored_print("✅ Model training completed!", "green")
    else:
        colored_print("❌ Model training failed", "red")

def chat_cmd(args):
    """Chat with the AI"""
    if not args:
        colored_print("❌ Usage: chat <your message>", "red")
        return
    
    message = " ".join(args)
    colored_print(f"🤖 AI: ", "cyan", end="")
    
    response = chess_llm.chat_with_model(message, use_chess_context=True)
    
    if response.startswith("Error"):
        colored_print(response, "red")
    else:
        print(response)

def list_players_cmd():
    """List analyzed players"""
    if not os.path.exists("chess_strategy_training_data.json"):
        colored_print("❌ No training data found.", "red")
        return
    
    try:
        with open("chess_strategy_training_data.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        players = set()
        for entry in data:
            if isinstance(entry, dict):
                player_name = entry.get('input', {}).get('opponent_profile', {}).get('player_name', '')
                if player_name:
                    players.add(player_name)
        
        if players:
            colored_print("📊 Analyzed Players:", "green")
            for player in sorted(players):
                colored_print(f"  • {player}", "white")
        else:
            colored_print("❌ No players analyzed yet.", "red")
        
    except Exception as e:
        colored_print(f"❌ Error loading player list: {e}", "red")

def check_setup():
    """Check if everything is set up correctly"""
    issues = []
    
    # Check Ollama
    if not chess_llm.check_ollama_available():
        issues.append("Ollama is not running")
    elif not chess_llm.check_model_available():
        issues.append(f"Model {chess_llm.model_name} not available")
    
    # Check Stockfish
    analyzer = ChessGameAnalyzer()
    if not os.path.exists(analyzer.stockfish_path):
        issues.append("Stockfish engine not found")
    
    if issues:
        colored_print("⚠️ Setup Issues:", "yellow")
        for issue in issues:
            colored_print(f"  • {issue}", "red")
        print()
    else:
        colored_print("✅ All components ready!", "green")

def main():
    """Main CLI loop"""
    print_header()
    check_setup()
    
    while True:
        try:
            user_input = input("\n🏛️ ChessGPT> ").strip()
            
            if not user_input:
                continue
            
            parts = user_input.split()
            command = parts[0].lower()
            args = parts[1:]
            
            if command in ['quit', 'exit', 'q']:
                colored_print("👋 Goodbye!", "yellow")
                break
            elif command == 'help':
                print_header()
            elif command == 'analyze':
                analyze_player_cmd(args)
            elif command == 'strategy':
                get_strategy_cmd(args)
            elif command == 'train':
                train_model_cmd()
            elif command == 'chat':
                chat_cmd(args)
            elif command == 'list':
                list_players_cmd()
            else:
                colored_print(f"❌ Unknown command: {command}. Type 'help' for available commands.", "red")
        
        except KeyboardInterrupt:
            colored_print("\n👋 Goodbye!", "yellow")
            break
        except Exception as e:
            colored_print(f"❌ Error: {e}", "red")

if __name__ == "__main__":
    import json
    main()
