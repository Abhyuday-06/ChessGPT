"""
Open WebUI Integration for Chess Strategy AI
Compatible with Open WebUI framework for better user experience
"""

from flask import Flask, request, jsonify, Response
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

# Global state for progress tracking
analysis_sessions = {}
progress_updates = {}

class AnalysisSession:
    def __init__(self, session_id: str, username: str):
        self.session_id = session_id
        self.username = username
        self.status = "initializing"
        self.progress = 0
        self.current_step = ""
        self.steps_completed = []
        self.total_steps = 6
        self.start_time = time.time()
        self.error = None
        self.result = None

def get_session(session_id: str) -> Optional[AnalysisSession]:
    """Get analysis session by ID"""
    return analysis_sessions.get(session_id)

def update_progress(session_id: str, step: str, progress: int, status: str = "in_progress"):
    """Update progress for a session"""
    session = get_session(session_id)
    if session:
        session.current_step = step
        session.progress = progress
        session.status = status
        if step not in session.steps_completed and status == "completed":
            session.steps_completed.append(step)

@app.route('/api/chat/completions', methods=['POST'])
def chat_completions():
    """OpenAI-compatible chat completions endpoint for Open WebUI"""
    try:
        data = request.get_json()
        messages = data.get('messages', [])
        stream = data.get('stream', False)
        
        if not messages:
            return jsonify({
                'error': 'No messages provided'
            }), 400
        
        # Get the last user message
        user_message = ""
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                user_message = msg.get('content', '')
                break
        
        # Check if this is a chess analysis request
        if any(keyword in user_message.lower() for keyword in ['analyze', 'chess', 'strategy', 'player']):
            # Try to extract username from the message
            username = extract_username(user_message)
            
            if username:
                if stream:
                    # Start analysis session
                    session_id = str(uuid.uuid4())
                    session = AnalysisSession(session_id, username)
                    analysis_sessions[session_id] = session
                    
                    # Start analysis in background
                    threading.Thread(
                        target=analyze_player_with_progress,
                        args=(session_id, username),
                        daemon=True
                    ).start()
                    
                    # Return streaming response
                    return Response(
                        generate_openai_stream(session_id),
                        mimetype='text/plain',
                        headers={
                            'Content-Type': 'text/plain; charset=utf-8',
                            'Cache-Control': 'no-cache',
                            'X-Accel-Buffering': 'no'
                        }
                    )
                else:
                    # Non-streaming response
                    return jsonify({
                        'choices': [{
                            'message': {
                                'role': 'assistant',
                                'content': f'🔍 Starting analysis for player **{username}**... This may take a few minutes.'
                            }
                        }]
                    })
            else:
                return jsonify({
                    'choices': [{
                        'message': {
                            'role': 'assistant',
                            'content': 'Please provide a chess username to analyze. For example: "Analyze player hikaru" or "Generate strategy for magnus"'
                        }
                    }]
                })
        else:
            # Regular chat - use Ollama LLM
            if stream:
                return Response(
                    generate_llm_stream(user_message),
                    mimetype='text/plain',
                    headers={
                        'Content-Type': 'text/plain; charset=utf-8',
                        'Cache-Control': 'no-cache',
                        'X-Accel-Buffering': 'no'
                    }
                )
            else:
                response = chess_llm.generate_strategy(user_message)
                return jsonify({
                    'choices': [{
                        'message': {
                            'role': 'assistant',
                            'content': response
                        }
                    }]
                })
            
    except Exception as e:
        return jsonify({
            'error': f'Internal server error: {str(e)}'
        }), 500

def extract_username(message: str) -> Optional[str]:
    """Extract chess username from user message"""
    import re
    
    # Common patterns for chess usernames
    patterns = [
        r'analyze\s+(?:player\s+)?(\w+)',
        r'strategy\s+(?:for\s+)?(\w+)',
        r'username\s+(\w+)',
        r'player\s+(\w+)',
        r'user\s+(\w+)',
        r'^(\w+)$'  # Just a username
    ]
    
    message_lower = message.lower().strip()
    
    for pattern in patterns:
        match = re.search(pattern, message_lower)
        if match:
            username = match.group(1)
            # Filter out common words that aren't usernames
            if username not in ['player', 'user', 'analyze', 'strategy', 'chess', 'games']:
                return username
    
    return None

def generate_openai_stream(session_id: str):
    """Generate OpenAI-compatible streaming response for analysis progress"""
    session = get_session(session_id)
    if not session:
        yield f"data: {json.dumps({'error': 'Session not found'})}\n\n"
        return
    
    # Initial message
    initial_chunk = {
        "id": f"chatcmpl-{session_id}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": "chess-strategy-ai",
        "choices": [{
            "index": 0,
            "delta": {"role": "assistant", "content": f"🔍 Starting analysis for **{session.username}**...\n\n"},
            "finish_reason": None
        }]
    }
    yield f"data: {json.dumps(initial_chunk)}\n\n"
    
    # Monitor progress
    last_progress = -1
    while session.status in ["initializing", "in_progress"]:
        if session.progress != last_progress:
            if session.current_step:
                step_chunk = {
                    "id": f"chatcmpl-{session_id}",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": "chess-strategy-ai",
                    "choices": [{
                        "index": 0,
                        "delta": {"content": f"{session.current_step}\n"},
                        "finish_reason": None
                    }]
                }
                yield f"data: {json.dumps(step_chunk)}\n\n"
            
            # Progress bar
            progress_bar = "█" * (session.progress // 5) + "░" * (20 - session.progress // 5)
            progress_chunk = {
                "id": f"chatcmpl-{session_id}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": "chess-strategy-ai",
                "choices": [{
                    "index": 0,
                    "delta": {"content": f"Progress: [{progress_bar}] {session.progress}%\n\n"},
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(progress_chunk)}\n\n"
            
            last_progress = session.progress
        
        time.sleep(1)
        
        # Timeout after 10 minutes
        if time.time() - session.start_time > 600:
            session.status = "timeout"
            session.error = "Analysis timed out"
            break
    
    # Final result
    if session.status == "completed" and session.result:
        final_chunk = {
            "id": f"chatcmpl-{session_id}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": "chess-strategy-ai",
            "choices": [{
                "index": 0,
                "delta": {"content": f"\n\n✅ **Analysis Complete!**\n\n{session.result}"},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(final_chunk)}\n\n"
    elif session.error:
        error_chunk = {
            "id": f"chatcmpl-{session_id}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": "chess-strategy-ai",
            "choices": [{
                "index": 0,
                "delta": {"content": f"\n\n❌ **Error:** {session.error}"},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"
    else:
        incomplete_chunk = {
            "id": f"chatcmpl-{session_id}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": "chess-strategy-ai",
            "choices": [{
                "index": 0,
                "delta": {"content": "\n\n⚠️ **Analysis incomplete**"},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(incomplete_chunk)}\n\n"
    
    # End of stream
    yield "data: [DONE]\n\n"

def generate_llm_stream(message: str):
    """Generate OpenAI-compatible streaming response for LLM chat"""
    response = chess_llm.generate_strategy(message)
    
    # Split response into chunks for streaming effect
    words = response.split()
    chunk_size = 3
    
    for i in range(0, len(words), chunk_size):
        chunk_words = words[i:i+chunk_size]
        chunk_text = " ".join(chunk_words) + " "
        
        chunk = {
            "id": f"chatcmpl-{str(uuid.uuid4())}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": "chess-strategy-ai",
            "choices": [{
                "index": 0,
                "delta": {"content": chunk_text},
                "finish_reason": None
            }]
        }
        yield f"data: {json.dumps(chunk)}\n\n"
        time.sleep(0.1)  # Small delay for streaming effect
    
    # End of stream
    final_chunk = {
        "id": f"chatcmpl-{str(uuid.uuid4())}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": "chess-strategy-ai",
        "choices": [{
            "index": 0,
            "delta": {},
            "finish_reason": "stop"
        }]
    }
    yield f"data: {json.dumps(final_chunk)}\n\n"
    yield "data: [DONE]\n\n"

def generate_analysis_stream(session_id: str):
    """Generate streaming response for analysis progress"""
    session = get_session(session_id)
    if not session:
        yield "data: Session not found\n\n"
        return
    
    yield f"data: 🔍 Starting analysis for **{session.username}**...\n\n"
    
    # Monitor progress
    last_progress = -1
    while session.status in ["initializing", "in_progress"]:
        if session.progress != last_progress:
            if session.current_step:
                yield f"data: {session.current_step}\n\n"
            
            # Progress bar
            progress_bar = "█" * (session.progress // 5) + "░" * (20 - session.progress // 5)
            yield f"data: Progress: [{progress_bar}] {session.progress}%\n\n"
            
            last_progress = session.progress
        
        time.sleep(1)
        
        # Timeout after 10 minutes
        if time.time() - session.start_time > 600:
            session.status = "timeout"
            session.error = "Analysis timed out"
            break
    
    # Final result
    if session.status == "completed" and session.result:
        yield f"data: \n\n✅ **Analysis Complete!**\n\n"
        yield f"data: {session.result}\n\n"
    elif session.error:
        yield f"data: \n\n❌ **Error:** {session.error}\n\n"
    else:
        yield f"data: \n\n⚠️ **Analysis incomplete**\n\n"

def analyze_player_with_progress(session_id: str, username: str):
    """Analyze player with detailed progress tracking"""
    session = get_session(session_id)
    if not session:
        return
    
    try:
        session.status = "in_progress"
        
        # Step 1: Check if player already analyzed
        update_progress(session_id, "🔍 Checking existing data...", 10)
        time.sleep(1)
        
        if enhanced_analyzer.is_player_analyzed(username):
            update_progress(session_id, "✅ Player already analyzed, generating strategy...", 80)
            player_data = enhanced_analyzer.get_player_data(username)
            if player_data:
                strategy = generate_strategy_for_player(player_data, username)
                session.result = strategy
                session.status = "completed"
                session.progress = 100
                return
        
        # Step 2: Download games
        update_progress(session_id, "📥 Downloading games from Chess.com and Lichess...", 20)
        time.sleep(2)
        
        # Step 3: Parse games
        update_progress(session_id, "📋 Parsing PGN files and extracting game data...", 35)
        time.sleep(2)
        
        # Step 4: Analyze with Stockfish
        update_progress(session_id, "🔍 Analyzing games with Stockfish engine...", 50)
        time.sleep(3)
        
        # Step 5: Identify weaknesses
        update_progress(session_id, "⚡ Identifying tactical and strategic weaknesses...", 70)
        time.sleep(2)
        
        # Step 6: Run the actual analysis
        update_progress(session_id, "🧠 Running comprehensive analysis...", 85)
        
        # Run the chess analyzer
        result = subprocess.run(
            ["python", "chess_analyzer.py", username],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            # Step 7: Generate strategy
            update_progress(session_id, "🎯 Generating AI-powered strategy...", 95)
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
            opponent_analysis += "🎯 **Identified Weaknesses:**\n"
            for i, weakness in enumerate(weaknesses, 1):
                if isinstance(weakness, dict):
                    opponent_analysis += f"{i}. **{weakness.get('weakness_type', 'Unknown')}**\n"
                    opponent_analysis += f"   Details: {weakness.get('details', '')}\n"
                    if weakness.get('confidence_score'):
                        opponent_analysis += f"   Confidence: {weakness.get('confidence_score')}\n"
                    opponent_analysis += "\n"
        
        opponent_analysis += "\nPlease provide a comprehensive chess strategy to exploit these weaknesses."
        
        # Generate strategy using LLM
        strategy = chess_llm.generate_strategy(opponent_analysis)
        
        # Format the final response
        formatted_strategy = f"""
## 🏆 Chess Strategy for {username.title()}

**Analysis Date:** {player_data.get('timestamp', 'Unknown')}

### 🎯 Key Weaknesses Identified:
"""
        
        for i, weakness in enumerate(weaknesses, 1):
            if isinstance(weakness, dict):
                formatted_strategy += f"**{i}. {weakness.get('weakness_type', 'Unknown')}**\n"
                formatted_strategy += f"   - {weakness.get('details', '')}\n"
        
        formatted_strategy += f"\n### 🧠 AI-Generated Strategy:\n\n{strategy}\n"
        formatted_strategy += f"\n---\n*Generated using {chess_llm.model_name} model*"
        
        return formatted_strategy
        
    except Exception as e:
        return f"Error generating strategy: {str(e)}"

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Chess Strategy AI',
        'ollama_available': chess_llm.check_ollama_available(),
        'model_available': chess_llm.check_model_available()
    })

@app.route('/api/models', methods=['GET'])
def list_models():
    """List available models for Open WebUI compatibility"""
    return jsonify({
        'data': [{
            'id': 'chess-strategy-ai',
            'object': 'model',
            'created': int(time.time()),
            'owned_by': 'chess-ai',
            'permission': [],
            'root': 'chess-strategy-ai',
            'parent': None
        }]
    })

if __name__ == '__main__':
    print("🚀 Starting Chess Strategy AI - Open WebUI Compatible")
    print("🔍 Automatic game analysis enabled")
    print("🤖 Ollama LLM integration enabled")
    print("🌐 Compatible with Open WebUI framework")
    print("📡 Server will run on http://localhost:8000")
    
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
    
    app.run(debug=False, host='0.0.0.0', port=8000)
