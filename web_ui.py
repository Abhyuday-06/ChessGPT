"""
Chess Strategy Web UI
A ChatGPT-like interface for chess strategy generation
"""

from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import uuid
import json
from datetime import datetime
import threading
import os
from inference_engine import ChessStrategyPredictor

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chess_strategy_secret_key_2025'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global predictor instance
predictor = None

def initialize_predictor():
    """Initialize the chess strategy predictor"""
    global predictor
    try:
        predictor = ChessStrategyPredictor()
        print("✅ Chess Strategy Predictor initialized")
    except Exception as e:
        print(f"❌ Failed to initialize predictor: {e}")
        predictor = None

# Initialize predictor in a separate thread to avoid blocking startup
threading.Thread(target=initialize_predictor, daemon=True).start()

@app.route('/')
def index():
    """Main chat interface"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return render_template('chat.html')

@app.route('/api/analyze', methods=['POST'])
def analyze_opponent():
    """API endpoint to analyze an opponent"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        
        if not username:
            return jsonify({'error': 'Username is required'}), 400
        
        if not predictor:
            return jsonify({'error': 'Strategy engine not initialized'}), 503
        
        # Generate strategy
        strategy = predictor.get_strategy_for_opponent(username)
        
        return jsonify(strategy)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('analyze_opponent')
def handle_analyze_opponent(data):
    """Socket.IO handler for real-time opponent analysis"""
    try:
        username = data.get('username', '').strip()
        session_id = data.get('session_id')
        
        if not username:
            emit('error', {'message': 'Username is required'})
            return
        
        if not predictor:
            emit('error', {'message': 'Strategy engine not initialized'})
            return
        
        # Emit status updates during analysis
        emit('status', {'message': f'🔍 Analyzing opponent: {username}...', 'stage': 'analyzing'})
        
        # Analyze opponent (this will take some time)
        analysis_data = predictor.analyze_opponent(username)
        if not analysis_data:
            emit('error', {'message': 'Failed to analyze opponent'})
            return
        
        emit('status', {'message': '🧠 Generating strategy with AI...', 'stage': 'generating'})
        
        # Format input for LLM
        opponent_input = predictor.format_opponent_input(analysis_data)
        if not opponent_input:
            emit('error', {'message': 'Failed to format opponent data'})
            return
        
        # Generate strategy
        strategy_text = predictor.generate_strategy(opponent_input)
        if not strategy_text:
            emit('error', {'message': 'Failed to generate strategy'})
            return
        
        # Parse strategy
        parsed_strategy = predictor.parse_strategy_response(strategy_text)
        
        # Add metadata
        parsed_strategy["opponent"] = username
        parsed_strategy["analysis_timestamp"] = datetime.now().isoformat()
        parsed_strategy["session_id"] = session_id
        
        # Emit the complete strategy
        emit('strategy_complete', parsed_strategy)
        
    except Exception as e:
        emit('error', {'message': f'Analysis failed: {str(e)}'})

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    session_id = str(uuid.uuid4())
    emit('connected', {'session_id': session_id})
    print(f"🔗 Client connected: {session_id}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print("🔌 Client disconnected")

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    print("🚀 Starting Chess Strategy Web UI")
    print("🌐 Access the interface at: http://localhost:5000")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
