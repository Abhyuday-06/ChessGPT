"""
Simple Chess Strategy Web UI - Basic Version
A basic Flask interface for chess strategy generation without SocketIO
"""

from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime

# Import the simple predictor
try:
    from simple_predictor import SimpleChessStrategyPredictor
    predictor = SimpleChessStrategyPredictor()
    print("✅ Simple chess strategy predictor loaded")
except Exception as e:
    print(f"⚠️ Could not load simple predictor: {e}")
    predictor = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chess_strategy_simple_2025'

def load_existing_analyses():
    """Load existing chess analyses from the training data"""
    try:
        with open("chess_strategy_training_data.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract player names that we have analyses for
        available_players = set()
        for entry in data:
            player_name = entry.get('input', {}).get('opponent_profile', {}).get('player_name', '')
            if player_name:
                available_players.add(player_name.lower())
        
        return list(available_players), data
    except Exception as e:
        print(f"Error loading training data: {e}")
        return [], []

available_players, training_data = load_existing_analyses()

@app.route('/')
def index():
    """Main chat interface"""
    return render_template('simple_chat_basic.html', available_players=available_players)

@app.route('/get_strategy', methods=['POST'])
def get_strategy():
    """Get strategy for a player"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip().lower()
        
        if not username:
            return jsonify({
                'success': False,
                'error': 'Please provide a username'
            })
        
        # Check if we have data for this player
        if username in available_players:
            # Find the player's analysis
            player_data = None
            for entry in training_data:
                player_name = entry.get('input', {}).get('opponent_profile', {}).get('player_name', '').lower()
                if player_name == username:
                    player_data = entry
                    break
            
            if player_data:
                # Generate strategy using the predictor
                if predictor:
                    # Create a summary of the opponent's weaknesses
                    opponent_analysis = f"Player: {username}\n"
                    weaknesses = player_data.get('input', {}).get('opponent_weaknesses', [])
                    for weakness in weaknesses:
                        opponent_analysis += f"Weakness: {weakness.get('weakness_type', 'Unknown')}\n"
                        opponent_analysis += f"Details: {weakness.get('details', '')}\n"
                    
                    strategy = predictor.predict_strategy(opponent_analysis)
                    
                    return jsonify({
                        'success': True,
                        'strategy': strategy,
                        'player': username,
                        'analysis_date': player_data.get('timestamp', 'Unknown')
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Strategy predictor not available'
                    })
            else:
                return jsonify({
                    'success': False,
                    'error': f'No analysis data found for {username}'
                })
        else:
            return jsonify({
                'success': False,
                'error': f'No analysis available for {username}. Available players: {", ".join(available_players)}'
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error generating strategy: {str(e)}'
        })

@app.route('/available_players')
def get_available_players():
    """Get list of available players"""
    return jsonify({
        'players': available_players,
        'count': len(available_players)
    })

if __name__ == '__main__':
    print("🚀 Starting Simple Chess Strategy Web UI...")
    print(f"📊 Available players: {', '.join(available_players)}")
    print("🌐 Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)
