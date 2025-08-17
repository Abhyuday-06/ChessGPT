# 🏛️ Chess Strategy AI

A comprehensive AI-powered chess strategy generator that analyzes players and provides personalized strategies to exploit their weaknesses.

## ✨ Features

- **🔍 Automatic Game Analysis**: Downloads and analyzes games from Chess.com and Lichess
- **🧠 AI-Powered Strategy Generation**: Uses local LLM (Ollama) to generate personalized strategies
- **📊 Weakness Detection**: Identifies tactical and strategic weaknesses using Stockfish
- **🎨 Multiple Interfaces**: Choose from simple single-input UI, Open WebUI integration, or enhanced web interface
- **⚡ Real-time Progress**: Live progress tracking during analysis
- **🌐 Modern UI**: Beautiful, responsive web interfaces

## 🚀 Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup Ollama** (if not installed):
   ```bash
   # Install Ollama from https://ollama.ai/
   # Then pull a model:
   ollama pull llama3.1:8b
   ```

3. **Start the Application**:
   ```bash
   python quick_start.py
   ```

4. **Choose Your Interface**:
   - **Option 1**: Simple Single-Input UI (Recommended for beginners)
   - **Option 2**: Open WebUI Integration (Professional chat interface)
   - **Option 3**: Enhanced Web UI (Full-featured interface)
   - **Option 4**: Command Line (Direct terminal usage)

## 🎯 Usage

### Simple Single-Input UI
```bash
python quick_start.py
# Select option 1
# Enter any chess username (e.g., "hikaru", "magnus")
# Watch real-time analysis and get AI strategies!
```

### Open WebUI Integration
```bash
python quick_start.py
# Select option 2 or 6 for complete setup
# Configure Open WebUI with API endpoint
# Chat naturally: "Analyze player hikaru"
```

### Command Line
```bash
python chess_analyzer.py [username]
# Direct analysis of any chess player
```

## 📁 Project Structure

```
ChessGPT/
├── 🚀 quick_start.py           # Main launcher (START HERE)
├── 🎨 single_input_ui.py       # Simple single-input interface
├── 🏛️ openwebui_backend.py     # Open WebUI compatible backend
├── 💻 enhanced_web_ui.py       # Full-featured web interface
├── 🔍 chess_analyzer.py        # Core analysis engine
├── 🤖 ollama_llm.py            # Local LLM integration
├── 📊 enhanced_analyzer.py     # Enhanced analysis with progress
├── ⚙️ setup_enhanced.py        # Automated setup script
├── 🐳 chess_ai_complete.py     # Complete automated setup
└── 📋 requirements.txt         # Dependencies
```

## 🔧 Configuration

### Ollama Models
The system supports various Ollama models:
- `llama3.1:8b` (Recommended)
- `llama3:8b`
- `gemma2:9b`
- `mistral:7b`
- `codellama:7b`

### Stockfish Engine
- Stockfish is included in the `stockfish/` directory
- Automatically configured for game analysis

## 🌟 Interfaces

### 1. Single-Input UI (Recommended)
- **URL**: http://localhost:5001
- **Features**: One input field, real-time progress, beautiful design
- **Best for**: Quick analysis, beginners

### 2. Open WebUI Integration
- **URL**: http://localhost:3000 (Open WebUI) + http://localhost:8000 (Backend)
- **Features**: Professional chat interface, streaming responses
- **Best for**: Advanced users, conversational analysis

### 3. Enhanced Web UI
- **URL**: http://localhost:5000
- **Features**: Multi-step interface, detailed progress
- **Best for**: Detailed analysis, power users

## 🎮 Example Usage

### Analyze a Player
```
Input: "hikaru"
Output: 
🔍 Analyzing hikaru...
📥 Downloading games...
🧠 AI Strategy Generated!

Key Weaknesses:
1. Time pressure in endgames
2. Occasional tactical oversights in complex positions

Strategy: Focus on creating complex middlegame positions...
```

### Chat with AI
```
User: "Analyze player magnus"
AI: 🔍 Starting analysis for magnus...
    📥 Downloading games from Chess.com and Lichess...
    🧠 Generating personalized strategy...
    
    Strategy: Magnus is exceptionally strong in endgames...
```

## 📊 Analysis Features

- **Game Download**: Automatically fetches recent games from Chess.com and Lichess
- **Stockfish Analysis**: Deep engine evaluation of critical positions
- **Weakness Detection**: Identifies patterns in:
  - Tactical mistakes
  - Time management issues
  - Opening preparation gaps
  - Endgame technique weaknesses
- **AI Strategy**: Personalized recommendations based on detected weaknesses

## 🔧 Advanced Setup

### Manual Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup Ollama
ollama serve
ollama pull llama3.1:8b

# 3. Start specific interface
python single_input_ui.py      # Simple UI
python openwebui_backend.py    # Open WebUI backend
python enhanced_web_ui.py      # Enhanced UI
```

### Docker Setup (Optional)
```bash
# Build and run with Docker Compose
docker-compose up -d
```

## 🎯 Supported Players

- **Chess.com**: Any public username
- **Lichess**: Any public username
- **Automatic Detection**: System automatically determines platform

## 📈 Performance

- **Analysis Time**: 1-5 minutes per player
- **Memory Usage**: ~500MB - 2GB (depending on model)
- **Storage**: ~100MB per analyzed player

## 🛠️ Troubleshooting

### Common Issues

1. **Ollama not running**:
   ```bash
   ollama serve
   ```

2. **Model not found**:
   ```bash
   ollama pull llama3.1:8b
   ```

3. **Port already in use**:
   - Check if another instance is running
   - Try different ports in the scripts

4. **Analysis fails**:
   - Check if username exists on Chess.com/Lichess
   - Verify internet connection
   - Check Stockfish installation

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Stockfish**: Chess engine for position analysis
- **Ollama**: Local LLM infrastructure
- **Chess.com & Lichess**: Game data sources
- **python-chess**: Chess library for Python

## 🚀 Get Started Now!

```bash
python quick_start.py
```

Choose your preferred interface and start analyzing chess players in minutes!
