"""
Command Line Interface for Chess Strategy AI
Simple CLI to test the chess strategy generation system
"""

import json
from simple_predictor import SimpleChessStrategyPredictor

def load_training_data():
    """Load the training data to see available players"""
    try:
        with open("chess_strategy_training_data.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract player names
        available_players = set()
        for entry in data:
            player_name = entry.get('input', {}).get('opponent_profile', {}).get('player_name', '')
            if player_name:
                available_players.add(player_name.lower())
        
        return list(available_players), data
    except Exception as e:
        print(f"Error loading training data: {e}")
        return [], []

def main():
    print("🏛️ Chess Strategy AI - Command Line Interface")
    print("=" * 50)
    
    # Load predictor
    try:
        predictor = SimpleChessStrategyPredictor()
        print("✅ Strategy predictor loaded successfully")
    except Exception as e:
        print(f"❌ Error loading predictor: {e}")
        return
    
    # Load available players
    available_players, training_data = load_training_data()
    print(f"📊 Available players: {', '.join(available_players)}")
    print("-" * 50)
    
    while True:
        print("\n🎯 Enter a chess player username (or 'quit' to exit):")
        username = input("> ").strip().lower()
        
        if username in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        
        if not username:
            print("❌ Please enter a username")
            continue
        
        if username not in available_players:
            print(f"❌ Player '{username}' not found. Available: {', '.join(available_players)}")
            continue
        
        # Find player data
        player_data = None
        for entry in training_data:
            player_name = entry.get('input', {}).get('opponent_profile', {}).get('player_name', '').lower()
            if player_name == username:
                player_data = entry
                break
        
        if not player_data:
            print(f"❌ No data found for player '{username}'")
            continue
        
        print(f"\n🔍 Analyzing player: {username}")
        print("-" * 30)
        
        # Show player's weaknesses
        weaknesses = player_data.get('input', {}).get('opponent_weaknesses', [])
        print(f"📋 Found {len(weaknesses)} weaknesses:")
        for i, weakness in enumerate(weaknesses, 1):
            print(f"  {i}. {weakness.get('weakness_type', 'Unknown')}")
            print(f"     {weakness.get('details', '')}")
        
        # Generate strategy
        print("\n🧠 Generating strategy...")
        opponent_analysis = f"Player: {username}\n"
        for weakness in weaknesses:
            opponent_analysis += f"Weakness: {weakness.get('weakness_type', 'Unknown')}\n"
            opponent_analysis += f"Details: {weakness.get('details', '')}\n"
        
        strategy = predictor.predict_strategy(opponent_analysis)
        
        print("\n🎯 RECOMMENDED STRATEGY:")
        print("=" * 40)
        print(strategy)
        print("=" * 40)
        
        print(f"\n📅 Analysis date: {player_data.get('timestamp', 'Unknown')}")

if __name__ == "__main__":
    main()
