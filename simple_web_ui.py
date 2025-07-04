"""
Simple Chess Strategy Web UI
A ChatGPT-like interface for chess strategy generation using the simple predictor
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import json
import os
from datetime import datetime
import threading

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
socketio = SocketIO(app, cors_allowed_origins="*")

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
    return render_template('simple_chat.html', available_players=available_players)

@socketio.on('get_strategy')
def handle_get_strategy(data):
    """Handle strategy generation requests"""
    try:
        username = data.get('username', '').strip().lower()
        
        if not username:
            emit('error', {'message': 'Username is required'})
            return
        
        if not predictor:
            emit('error', {'message': 'Strategy predictor not available'})
            return
        
        emit('status', {'message': f'🔍 Looking for analysis of {username}...', 'stage': 'searching'})
        
        # Find existing analysis for this player
        player_analysis = None
        for entry in training_data:
            player_name = entry.get('input', {}).get('opponent_profile', {}).get('player_name', '').lower()
            if player_name == username:
                player_analysis = entry
                break
        
        if not player_analysis:
            emit('error', {'message': f'No analysis found for {username}. Available players: {", ".join(available_players)}'})
            return
        
        emit('status', {'message': '🧠 Generating strategy with AI...', 'stage': 'generating'})
        
        # Format input for predictor
        opponent_profile = player_analysis.get('input', {}).get('opponent_profile', {})
        player_name = opponent_profile.get('player_name', username)
        opening_weaknesses = player_analysis.get('input', {}).get('opening_weaknesses', [])
        
        input_text = f"Analyze opponent {player_name}:\\n"
        
        if opening_weaknesses:
            input_text += "Opening Weaknesses:\\n"
            for weakness in opening_weaknesses:
                opening = weakness.get('opening', 'Unknown')
                color = weakness.get('color', 'unknown').replace('as_', '')
                win_rate = weakness.get('win_rate', 0)
                input_text += f"- {opening} as {color}: {win_rate:.1f}% win rate\\n"
        
        # Generate strategy
        strategy = predictor.predict_strategy(input_text)
        
        # Format response
        response = {
            "opponent": player_name,
            "analysis_date": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "strategy": strategy,
            "weaknesses_analyzed": len(opening_weaknesses),
            "success": True
        }
        
        emit('strategy_complete', response)
        
    except Exception as e:
        emit('error', {'message': f'Strategy generation failed: {str(e)}'})

@socketio.on('list_players')
def handle_list_players():
    """Return list of available players"""
    emit('available_players', {'players': available_players})

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {'message': 'Connected to Chess Strategy AI'})
    print(f"🔗 Client connected")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print("🔌 Client disconnected")

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    print("🚀 Starting Simple Chess Strategy Web UI")
    print(f"📊 Available players: {', '.join(available_players)}")
    print("🌐 Access the interface at: http://localhost:5000")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
