"""
Enhanced Chess Strategy Web UI
Integrated with automatic analysis and Ollama LLM
"""

from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime
import threading
import time

# Import our enhanced components
from enhanced_analyzer import enhanced_analyzer
from ollama_llm import chess_llm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chess_strategy_enhanced_2025'

@app.route('/')
def index():
    """Main interface"""
    available_players = enhanced_analyzer.get_available_players()
    return render_template('enhanced_chat.html', available_players=available_players)

@app.route('/api/analyze', methods=['POST'])
def start_analysis():
    """Start analysis for a new player"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        platform = data.get('platform', 'auto').lower()
        
        if not username:
            return jsonify({
                'success': False,
                'error': 'Please provide a username'
            })
        
        # Check if already analyzed
        if enhanced_analyzer.is_player_analyzed(username):
            return jsonify({
                'success': True,
                'message': f'Player {username} already analyzed',
                'status': 'completed'
            })
        
        # Start analysis with platform preference
        result = enhanced_analyzer.start_analysis(username, platform)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'status': 'started'
            })
        else:
            return jsonify({
                'success': False,
                'error': result['message']
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error starting analysis: {str(e)}'
        })

@app.route('/api/status/<username>')
def get_analysis_status(username):
    """Get analysis status for a player"""
    try:
        status = enhanced_analyzer.get_progress(username)
        return jsonify({
            'success': True,
            'status': status['status'],
            'message': status['message'],
            'progress': status.get('progress', 0)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error getting status: {str(e)}'
        })

@app.route('/api/strategy', methods=['POST'])
def get_strategy():
    """Get strategy for a player using Ollama LLM"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        
        if not username:
            return jsonify({
                'success': False,
                'error': 'Please provide a username'
            })
        
        # Check if player is analyzed
        if not enhanced_analyzer.is_player_analyzed(username):
            return jsonify({
                'success': False,
                'error': f'Player {username} not analyzed yet. Please analyze first.',
                'needs_analysis': True
            })
        
        # Get player data
        player_data = enhanced_analyzer.get_player_data(username)
        if not player_data:
            return jsonify({
                'success': False,
                'error': f'No data found for {username}. Please re-analyze this player.'
            })
        
        # Check if Ollama is available
        if not chess_llm.check_ollama_available():
            return jsonify({
                'success': False,
                'error': 'Ollama is not running. Please start Ollama to generate strategies.'
            })
        
        # Format opponent analysis for LLM
        opponent_analysis = format_opponent_analysis(player_data, username)
        
        # Generate strategy using Ollama LLM
        print(f"🤖 Generating strategy for {username}...")
        strategy = chess_llm.generate_strategy(opponent_analysis)
        
        # Check if strategy generation was successful
        if strategy.startswith("Error:"):
            return jsonify({
                'success': False,
                'error': strategy
            })
        
        return jsonify({
            'success': True,
            'strategy': strategy,
            'player': username,
            'analysis_date': player_data.get('timestamp', 'Unknown'),
            'model_used': chess_llm.model_name
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error generating strategy: {str(e)}'
        })

@app.route('/api/players')
def get_available_players():
    """Get list of available players"""
    try:
        players = enhanced_analyzer.get_available_players()
        return jsonify({
            'success': True,
            'players': players,
            'count': len(players)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error getting players: {str(e)}'
        })

@app.route('/api/ollama/status')
def get_ollama_status():
    """Check Ollama status"""
    try:
        is_available = chess_llm.check_ollama_available()
        model_available = chess_llm.check_model_available() if is_available else False
        
        return jsonify({
            'success': True,
            'ollama_running': is_available,
            'model_available': model_available,
            'model_name': chess_llm.model_name
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error checking Ollama: {str(e)}'
        })

@app.route('/api/ollama/setup', methods=['POST'])
def setup_ollama():
    """Setup Ollama model"""
    try:
        success = chess_llm.setup_model()
        return jsonify({
            'success': success,
            'message': 'Model setup completed' if success else 'Model setup failed'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error setting up model: {str(e)}'
        })

@app.route('/api/train', methods=['POST'])
def train_model():
    """Fine-tune the model with current training data"""
    try:
        success = chess_llm.fine_tune_model()
        return jsonify({
            'success': success,
            'message': 'Model training completed' if success else 'Model training failed'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error training model: {str(e)}'
        })

def format_opponent_analysis(player_data: dict, username: str) -> str:
    """Format player data for LLM analysis"""
    try:
        opponent_analysis = f"Chess Player Analysis: {username}\n\n"
        
        # Add opponent profile info
        opponent_profile = player_data.get('input', {}).get('opponent_profile', {})
        if opponent_profile:
            opponent_analysis += f"Player: {opponent_profile.get('player_name', username)}\n"
            opponent_analysis += f"Platform: {opponent_profile.get('platform', 'Unknown')}\n"
            opponent_analysis += f"Games Analyzed: {opponent_profile.get('games_analyzed', 'Unknown')}\n\n"
        
        # Add weaknesses
        weaknesses = player_data.get('input', {}).get('opponent_weaknesses', [])
        if weaknesses:
            opponent_analysis += "Identified Weaknesses:\n"
            for i, weakness in enumerate(weaknesses, 1):
                opponent_analysis += f"{i}. {weakness.get('weakness_type', 'Unknown')}\n"
                opponent_analysis += f"   Details: {weakness.get('details', '')}\n"
                if weakness.get('confidence'):
                    opponent_analysis += f"   Confidence: {weakness.get('confidence')}\n"
                opponent_analysis += "\n"
        
        opponent_analysis += "\nPlease provide a comprehensive chess strategy to exploit these weaknesses."
        
        return opponent_analysis
        
    except Exception as e:
        return f"Error formatting analysis for {username}: {str(e)}"

if __name__ == '__main__':
    print("🚀 Starting Enhanced Chess Strategy Web UI...")
    print("🔍 Automatic game analysis enabled")
    print("🤖 Ollama LLM integration enabled")
    print("🌐 Open http://localhost:5000 in your browser")
    
    # Check Ollama status on startup
    if chess_llm.check_ollama_available():
        print("✅ Ollama is running")
        if chess_llm.check_model_available():
            print(f"✅ Model {chess_llm.model_name} is available")
        else:
            print(f"⚠️ Model {chess_llm.model_name} not found - will pull on first use")
    else:
        print("⚠️ Ollama not running - please start Ollama for LLM features")
    
    available_players = enhanced_analyzer.get_available_players()
    print(f"📊 Available players: {', '.join(available_players) if available_players else 'None'}")
    
    app.run(debug=False, host='0.0.0.0', port=5000)
