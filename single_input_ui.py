"""
Simple Single-Input Chess Strategy Web UI
One input field for chess usernames with automatic analysis
"""

from flask import Flask, render_template, request, jsonify, Response
import json
import time
import threading
import uuid
import subprocess
import os
from enhanced_analyzer import enhanced_analyzer
from ollama_llm import chess_llm

app = Flask(__name__)

# Global sessions
analysis_sessions = {}

class AnalysisSession:
    def __init__(self, session_id: str, username: str):
        self.session_id = session_id
        self.username = username
        self.status = "initializing"
        self.progress = 0
        self.current_step = ""
        self.start_time = time.time()
        self.error = None
        self.result = None

def update_progress(session_id: str, step: str, progress: int, status: str = "in_progress"):
    """Update progress for a session"""
    session = analysis_sessions.get(session_id)
    if session:
        session.current_step = step
        session.progress = progress
        session.status = status

def analyze_player_background(session_id: str, username: str):
    """Run player analysis in background"""
    try:
        session = analysis_sessions.get(session_id)
        if not session:
            return
        
        # Check if player already analyzed
        update_progress(session_id, "🔍 Checking existing data...", 10)
        time.sleep(1)
        
        if enhanced_analyzer.is_player_analyzed(username):
            update_progress(session_id, "✅ Player already analyzed, generating strategy...", 80)
            player_data = enhanced_analyzer.get_player_data(username)
            if player_data:
                # Generate strategy
                update_progress(session_id, "🧠 Generating AI strategy...", 90)
                strategy = generate_strategy_for_player(player_data, username)
                session.result = strategy
                session.status = "completed"
                session.progress = 100
                return
        
        # Run full analysis
        update_progress(session_id, "📥 Downloading games...", 20)
        time.sleep(2)
        
        update_progress(session_id, "📋 Parsing games...", 35)
        time.sleep(2)
        
        update_progress(session_id, "🔍 Analyzing with Stockfish...", 50)
        time.sleep(3)
        
        update_progress(session_id, "⚡ Identifying weaknesses...", 70)
        time.sleep(2)
        
        update_progress(session_id, "🧠 Running analysis...", 85)
        
        # Run the analyzer
        result = subprocess.run(
            ["python", "chess_analyzer.py", username],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=300
        )
        
        if result.returncode == 0:
            update_progress(session_id, "🎯 Generating strategy...", 95)
            
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
            
    except Exception as e:
        session.error = f"Error during analysis: {str(e)}"
        session.status = "error"

def generate_strategy_for_player(player_data: dict, username: str) -> str:
    """Generate strategy using the LLM"""
    try:
        weaknesses = player_data.get('weaknesses', [])
        if not weaknesses:
            return f"No specific weaknesses found for {username.title()}. Player appears to be well-rounded."
        
        # Create prompt for LLM
        prompt = f"Generate a chess strategy to exploit these weaknesses of player {username}:\\n"
        for weakness in weaknesses:
            if isinstance(weakness, dict):
                prompt += f"- {weakness.get('weakness_type', 'Unknown')}: {weakness.get('details', '')}\\n"
            else:
                prompt += f"- {weakness}\\n"
        
        # Get strategy from LLM
        strategy = chess_llm.generate_strategy(prompt)
        
        # Format the response
        formatted_strategy = f"""## 🏆 Chess Strategy for {username.title()}

**Analysis Date:** {player_data.get('timestamp', 'Unknown')}

### 🎯 Key Weaknesses Identified:
"""
        
        for i, weakness in enumerate(weaknesses, 1):
            if isinstance(weakness, dict):
                formatted_strategy += f"**{i}. {weakness.get('weakness_type', 'Unknown')}**\\n"
                formatted_strategy += f"   - {weakness.get('details', '')}\\n"
        
        formatted_strategy += f"\\n### 🧠 AI-Generated Strategy:\\n\\n{strategy}\\n"
        formatted_strategy += f"\\n---\\n*Generated using {chess_llm.model_name} model*"
        
        return formatted_strategy
        
    except Exception as e:
        return f"Error generating strategy: {str(e)}"

@app.route('/')
def index():
    """Main page with single input"""
    return render_template('single_input.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Start analysis for a username"""
    data = request.get_json()
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({'error': 'Username is required'}), 400
    
    # Create session
    session_id = str(uuid.uuid4())
    session = AnalysisSession(session_id, username)
    analysis_sessions[session_id] = session
    
    # Start analysis in background
    threading.Thread(
        target=analyze_player_background,
        args=(session_id, username),
        daemon=True
    ).start()
    
    return jsonify({'session_id': session_id, 'username': username})

@app.route('/progress/<session_id>')
def get_progress(session_id):
    """Get progress for a session"""
    session = analysis_sessions.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    return jsonify({
        'status': session.status,
        'progress': session.progress,
        'current_step': session.current_step,
        'error': session.error,
        'result': session.result
    })

@app.route('/stream/<session_id>')
def stream_progress(session_id):
    """Stream progress updates"""
    def generate():
        session = analysis_sessions.get(session_id)
        if not session:
            yield "data: Session not found\\n\\n"
            return
        
        last_progress = -1
        while session.status in ["initializing", "in_progress"]:
            if session.progress != last_progress:
                data = {
                    'status': session.status,
                    'progress': session.progress,
                    'current_step': session.current_step
                }
                yield f"data: {json.dumps(data)}\\n\\n"
                last_progress = session.progress
            
            time.sleep(1)
            
            # Timeout
            if time.time() - session.start_time > 600:
                session.status = "timeout"
                session.error = "Analysis timed out"
                break
        
        # Final result
        final_data = {
            'status': session.status,
            'progress': session.progress,
            'current_step': session.current_step,
            'error': session.error,
            'result': session.result
        }
        yield f"data: {json.dumps(final_data)}\\n\\n"
    
    return Response(generate(), mimetype='text/event-stream')

# Create the template
template_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chess Strategy AI</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            max-width: 600px;
            width: 100%;
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        .input-section {
            margin-bottom: 30px;
        }
        .input-group {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        input[type="text"] {
            flex: 1;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            padding: 15px 30px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
            transition: background 0.3s;
        }
        button:hover {
            background: #5a6fd8;
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .progress-section {
            display: none;
            margin-top: 30px;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #f0f0f0;
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 10px;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            width: 0%;
            transition: width 0.5s ease;
        }
        .progress-text {
            text-align: center;
            font-weight: bold;
            color: #333;
        }
        .result-section {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            display: none;
        }
        .result-content {
            line-height: 1.6;
        }
        .error {
            color: #dc3545;
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
        }
        .step {
            margin: 10px 0;
            padding: 10px;
            background: #e3f2fd;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏛️ Chess Strategy AI</h1>
        
        <div class="input-section">
            <div class="input-group">
                <input type="text" id="username" placeholder="Enter chess username (e.g., hikaru, magnus)" />
                <button onclick="startAnalysis()">Analyze</button>
            </div>
            <p style="text-align: center; color: #666; margin: 0;">
                Works with Chess.com and Lichess usernames
            </p>
        </div>
        
        <div class="progress-section" id="progressSection">
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div class="progress-text" id="progressText">Starting analysis...</div>
            <div id="currentStep" class="step" style="display: none;"></div>
        </div>
        
        <div class="result-section" id="resultSection">
            <div class="result-content" id="resultContent"></div>
        </div>
    </div>

    <script>
        let currentSession = null;
        let eventSource = null;

        function startAnalysis() {
            const username = document.getElementById('username').value.trim();
            if (!username) {
                alert('Please enter a username');
                return;
            }

            // Show progress section
            document.getElementById('progressSection').style.display = 'block';
            document.getElementById('resultSection').style.display = 'none';
            
            // Disable button
            document.querySelector('button').disabled = true;

            // Start analysis
            fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({username: username})
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showError(data.error);
                    return;
                }
                
                currentSession = data.session_id;
                startProgressStream(data.session_id);
            })
            .catch(error => {
                showError('Failed to start analysis: ' + error.message);
            });
        }

        function startProgressStream(sessionId) {
            if (eventSource) {
                eventSource.close();
            }

            eventSource = new EventSource(`/stream/${sessionId}`);
            
            eventSource.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateProgress(data);
                
                if (data.status === 'completed' || data.status === 'error' || data.status === 'timeout') {
                    eventSource.close();
                    document.querySelector('button').disabled = false;
                    
                    if (data.status === 'completed' && data.result) {
                        showResult(data.result);
                    } else if (data.error) {
                        showError(data.error);
                    }
                }
            };

            eventSource.onerror = function() {
                eventSource.close();
                document.querySelector('button').disabled = false;
                showError('Connection lost. Please try again.');
            };
        }

        function updateProgress(data) {
            const progressFill = document.getElementById('progressFill');
            const progressText = document.getElementById('progressText');
            const currentStep = document.getElementById('currentStep');
            
            progressFill.style.width = data.progress + '%';
            progressText.textContent = `Progress: ${data.progress}%`;
            
            if (data.current_step) {
                currentStep.textContent = data.current_step;
                currentStep.style.display = 'block';
            }
        }

        function showResult(result) {
            document.getElementById('progressSection').style.display = 'none';
            document.getElementById('resultSection').style.display = 'block';
            
            // Convert markdown-like formatting to HTML
            const html = result
                .replace(/##\\s*(.*)/g, '<h2>$1</h2>')
                .replace(/###\\s*(.*)/g, '<h3>$1</h3>')
                .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
                .replace(/\\*(.*?)\\*/g, '<em>$1</em>')
                .replace(/\\n/g, '<br>');
            
            document.getElementById('resultContent').innerHTML = html;
        }

        function showError(error) {
            document.getElementById('progressSection').style.display = 'none';
            document.getElementById('resultSection').style.display = 'block';
            document.getElementById('resultContent').innerHTML = `<div class="error">❌ ${error}</div>`;
        }

        // Allow Enter key to start analysis
        document.getElementById('username').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                startAnalysis();
            }
        });
    </script>
</body>
</html>"""

# Ensure templates directory exists
os.makedirs('templates', exist_ok=True)

# Write template
with open('templates/single_input.html', 'w', encoding='utf-8') as f:
    f.write(template_content)

if __name__ == '__main__':
    print("🚀 Starting Single-Input Chess Strategy Web UI")
    print("🎯 Simple interface - just enter a username!")
    print("🔍 Automatic analysis detection")
    print("🤖 AI-powered strategy generation")
    print("🌐 Access at: http://localhost:5001")
    
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
    
    app.run(debug=True, host='0.0.0.0', port=5001)
