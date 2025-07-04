"""
Simplified Chess Strategy Web UI
Single input field - automatically handles new/existing players
"""

from flask import Flask, render_template, request, jsonify, Response
import json
import os
import time
import threading
from datetime import datetime
import subprocess
import uuid
from typing import Dict, Any, Optional

# Import our enhanced components
from enhanced_analyzer import enhanced_analyzer
from ollama_llm import chess_llm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chess_strategy_simplified_2025'

# Global state for progress tracking
analysis_sessions = {}

class AnalysisSession:
    def __init__(self, session_id: str, username: str):
        self.session_id = session_id
        self.username = username
        self.status = "initializing"
        self.progress = 0
        self.current_step = ""
        self.steps = [
            "Checking existing data",
            "Downloading games",
            "Parsing PGN files", 
            "Stockfish analysis",
            "Identifying weaknesses",
            "Generating strategy"
        ]
        self.current_step_index = 0
        self.start_time = time.time()
        self.error = None
        self.result = None

@app.route('/')
def index():
    """Main interface"""
    available_players = enhanced_analyzer.get_available_players()
    return render_template('simplified_chat.html', available_players=available_players)

@app.route('/api/analyze', methods=['POST'])
def analyze_player():
    """Analyze any player (new or existing)"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        
        if not username:
            return jsonify({
                'success': False,
                'error': 'Please provide a username'
            })
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        session = AnalysisSession(session_id, username)
        analysis_sessions[session_id] = session
        
        # Start analysis in background
        threading.Thread(
            target=analyze_player_background,
            args=(session_id, username),
            daemon=True
        ).start()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': f'Started analysis for {username}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error starting analysis: {str(e)}'
        })

@app.route('/api/progress/<session_id>')
def get_progress(session_id):
    """Get analysis progress"""
    session = analysis_sessions.get(session_id)
    
    if not session:
        return jsonify({
            'success': False,
            'error': 'Session not found'
        })
    
    return jsonify({
        'success': True,
        'status': session.status,
        'progress': session.progress,
        'current_step': session.current_step,
        'current_step_index': session.current_step_index,
        'total_steps': len(session.steps),
        'steps': session.steps,
        'error': session.error,
        'result': session.result
    })

@app.route('/api/result/<session_id>')
def get_result(session_id):
    """Get final result"""
    session = analysis_sessions.get(session_id)
    
    if not session:
        return jsonify({
            'success': False,
            'error': 'Session not found'
        })
    
    if session.status == 'completed' and session.result:
        return jsonify({
            'success': True,
            'result': session.result,
            'username': session.username
        })
    elif session.error:
        return jsonify({
            'success': False,
            'error': session.error
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Analysis not complete'
        })

def analyze_player_background(session_id: str, username: str):
    """Analyze player with detailed progress tracking"""
    session = analysis_sessions.get(session_id)
    if not session:
        return
    
    try:
        session.status = "in_progress"
        
        # Step 1: Check existing data
        update_session_progress(session, 0, "Checking existing data...")
        time.sleep(1)
        
        if enhanced_analyzer.is_player_analyzed(username):
            update_session_progress(session, 5, "Player already analyzed, generating strategy...")
            player_data = enhanced_analyzer.get_player_data(username)
            if player_data:
                strategy = generate_strategy_for_player(player_data, username)
                session.result = strategy
                session.status = "completed"
                session.progress = 100
                return
        
        # Step 2: Download games
        update_session_progress(session, 1, "Downloading games from Chess.com and Lichess...")
        time.sleep(2)
        
        # Step 3: Parse PGN files
        update_session_progress(session, 2, "Parsing PGN files and extracting game data...")
        time.sleep(1)
        
        # Step 4: Stockfish analysis  
        update_session_progress(session, 3, "Analyzing games with Stockfish engine...")
        time.sleep(2)
        
        # Step 5: Identify weaknesses
        update_session_progress(session, 4, "Identifying tactical and strategic weaknesses...")
        time.sleep(1)
        
        # Run the actual analysis
        result = subprocess.run(
            ["python", "chess_analyzer.py", username],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            # Step 6: Generate strategy
            update_session_progress(session, 5, "Generating AI-powered strategy...")
            time.sleep(1)
            
            # Get the analyzed data and generate strategy
            player_data = enhanced_analyzer.get_player_data(username)
            if player_data:
                strategy = generate_strategy_for_player(player_data, username)
                session.result = strategy
                session.status = "completed"
                session.progress = 100
            else:
                session.error = "Analysis completed but no data found"
                session.status = "error"
        else:
            session.error = f"Analysis failed: {result.stderr}"
            session.status = "error"
            
    except subprocess.TimeoutExpired:
        session.error = "Analysis timed out - the player might have too many games"
        session.status = "error"
    except Exception as e:
        session.error = f"Analysis error: {str(e)}"
        session.status = "error"

def update_session_progress(session, step_index, message):
    """Update session progress"""
    session.current_step_index = step_index
    session.current_step = message
    session.progress = int((step_index + 1) / len(session.steps) * 100)

def generate_strategy_for_player(player_data: dict, username: str) -> str:
    """Generate strategy using the LLM"""
    try:
        # Format opponent analysis for LLM
        opponent_analysis = f"Chess Player Analysis: {username}\n\n"
        
        # Add opponent profile info
        opponent_profile = player_data.get('input', {}).get('opponent_profile', {})
        if opponent_profile:
            opponent_analysis += f"Player: {opponent_profile.get('player_name', username)}\n"
            opponent_analysis += f"Platform: {opponent_profile.get('platform', 'Unknown')}\n\n"
        
        # Add weaknesses
        weaknesses = player_data.get('input', {}).get('opponent_weaknesses', [])
        if weaknesses:
            opponent_analysis += "Identified Weaknesses:\n"
            for i, weakness in enumerate(weaknesses, 1):
                if isinstance(weakness, dict):
                    opponent_analysis += f"{i}. {weakness.get('weakness_type', 'Unknown')}\n"
                    opponent_analysis += f"   Details: {weakness.get('details', '')}\n"
                    if weakness.get('confidence_score'):
                        opponent_analysis += f"   Confidence: {weakness.get('confidence_score')}\n"
                    opponent_analysis += "\n"
        
        opponent_analysis += "\nPlease provide a comprehensive chess strategy to exploit these weaknesses."
        
        # Generate strategy using LLM
        strategy = chess_llm.generate_strategy(opponent_analysis)
        
        return strategy
        
    except Exception as e:
        return f"Error generating strategy: {str(e)}"

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

@app.route('/api/status')
def get_system_status():
    """Get system status"""
    try:
        return jsonify({
            'success': True,
            'ollama_running': chess_llm.check_ollama_available(),
            'model_available': chess_llm.check_model_available(),
            'model_name': chess_llm.model_name,
            'available_players': enhanced_analyzer.get_available_players()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error getting status: {str(e)}'
        })

if __name__ == '__main__':
    print("🚀 Starting Simplified Chess Strategy Web UI...")
    print("🔍 Single input interface - handles new/existing players automatically")
    print("🤖 Ollama LLM integration enabled")
    print("📊 Real-time progress tracking enabled")
    print("🌐 Open http://localhost:5000 in your browser")
    
    # Check system status
    if chess_llm.check_ollama_available():
        print("✅ Ollama is running")
        if chess_llm.check_model_available():
            print(f"✅ Model {chess_llm.model_name} is available")
        else:
            print(f"⚠️ Model {chess_llm.model_name} not found")
    else:
        print("⚠️ Ollama not running - please start Ollama")
    
    available_players = enhanced_analyzer.get_available_players()
    print(f"📊 Available players: {', '.join(available_players) if available_players else 'None'}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
