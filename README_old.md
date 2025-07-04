# 🏛️ Enhanced Chess Strategy AI

An advanced chess strategy generation system that automatically analyzes any chess player's games and provides AI-powered counter-strategies using local LLMs.

## 🚀 Features

- **🔍 Automatic Game Analysis**: Enter any Chess.com or Lichess username for instant analysis
- **🤖 AI-Powered Strategies**: Uses local LLMs (Gemma2, Llama3, Mistral) via Ollama
- **🌐 Modern Web Interface**: ChatGPT-like interface with real-time progress
- **📊 Real-time Analysis**: Watch game analysis progress in real-time
- **💾 Persistent Storage**: All analyses saved for future reference
- **🎯 Weakness Exploitation**: Identifies and targets opponent weaknesses
- **🔧 Easy Setup**: Automated setup with model selection

## 📋 Requirements

- Python 3.8+
- Ollama (for LLM inference)
- Stockfish (chess engine)
- 4GB+ RAM (for running local LLMs)

## 🛠️ Installation

### 1. Quick Setup (Recommended)
```bash
# Clone/download the project
cd ChessGPT

# Install Python dependencies
pip install -r requirements.txt

# Run enhanced setup (installs Ollama + models)
python setup_enhanced.py

# Start the system
python main_enhanced.py
```

### 2. Manual Setup
```bash
# Install Ollama
# Windows: Download from https://ollama.com/download
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve

# Pull a model (choose one)
ollama pull gemma2:2b      # Fast, 2B parameters
ollama pull llama3.2:3b    # Balanced, 3B parameters  
ollama pull mistral:7b     # Most capable, 7B parameters

# Install Python dependencies
pip install -r requirements.txt

# Setup Stockfish
python setup_stockfish.py

# Start the enhanced web UI
python enhanced_web_ui.py
```

## 🎯 Usage

### Web Interface
1. Start the system: `python main_enhanced.py`
2. Open http://localhost:5000 in your browser
3. Enter any chess username to analyze
4. Wait for analysis to complete
5. Generate AI strategies instantly

### Command Line Interface
```bash
# Interactive CLI
python chess_strategy_cli.py

# Direct analysis
python chess_analyzer.py <username>

# View training data
python view_dataset.py
```

## 🏗️ Architecture

```
Enhanced Chess Strategy AI
├── 🔍 Analysis Layer
│   ├── enhanced_analyzer.py      # Automatic game analysis
│   ├── chess_analyzer.py         # Core analysis engine
│   └── stockfish/                # Chess engine
│
├── 🤖 AI Layer  
│   ├── ollama_llm.py             # Local LLM integration
│   ├── chess_strategy_training_data.json # Training data
│   └── simple_predictor.py       # Fallback predictor
│
├── 🌐 Interface Layer
│   ├── enhanced_web_ui.py        # Main web interface
│   ├── templates/enhanced_chat.html # Modern UI
│   └── chess_strategy_cli.py     # Command line interface
│
└── 🔧 Setup Layer
    ├── setup_enhanced.py         # Automated setup
    ├── main_enhanced.py          # System integration
    └── requirements.txt          # Dependencies
```

## 🤖 Supported Models

| Model | Size | Speed | Quality | Recommended For |
|-------|------|-------|---------|-----------------|
| Gemma2 2B | 2B | ⚡ Fast | Good | Quick analysis |
| Llama 3.2 3B | 3B | 🔥 Balanced | Better | General use |
| Mistral 7B | 7B | 🐌 Slow | Best | Deep analysis |
| Qwen2 1.5B | 1.5B | ⚡⚡ Fastest | Basic | Speed priority |

## 🎮 How It Works

1. **Game Fetching**: Downloads recent games from Chess.com/Lichess
2. **Analysis**: Stockfish analyzes games for tactical patterns
3. **Weakness Identification**: AI identifies recurring weaknesses
4. **Strategy Generation**: LLM creates personalized counter-strategies
5. **Continuous Learning**: New analyses improve the training data

## 📊 Example Output

```
🎯 STRATEGY FOR MAGNUS

Opening Weaknesses:
• Struggles with Sicilian Defense variations
• Weak pawn structures in French Defense

Tactical Recommendations:
• Focus on central control in opening
• Exploit kingside weaknesses in middlegame
• Apply pressure on isolated pawns

Endgame Strategy:
• Force queen trades when ahead
• Create passed pawns on queenside
```

## 🔧 Configuration

### Model Selection
Edit `ollama_config.json` to change the model:
```json
{
  "model_name": "gemma2:2b",
  "setup_completed": true
}
```

### Analysis Settings
Modify `chess_analyzer.py` for custom analysis parameters:
- Number of games to analyze
- Time controls to include
- Minimum game length

## 🚀 API Endpoints

- `POST /api/analyze` - Start player analysis
- `GET /api/status/<username>` - Check analysis progress
- `POST /api/strategy` - Generate strategy
- `GET /api/players` - List available players
- `GET /api/ollama/status` - Check Ollama status

## 🔮 Future Enhancements

- [ ] Opening book integration
- [ ] Real-time game analysis
- [ ] Multi-language support
- [ ] Docker containerization
- [ ] Cloud deployment
- [ ] Mobile app
- [ ] Tournament analysis
- [ ] Rating prediction

## 🐛 Troubleshooting

### Ollama Issues
```bash
# Check if Ollama is running
ollama list

# Restart Ollama
ollama serve

# Pull model again
ollama pull gemma2:2b
```

### Analysis Failures
- Check internet connection
- Verify username exists on Chess.com/Lichess
- Ensure user has public games

### Performance Issues
- Use smaller models (gemma2:2b)
- Reduce analysis game count
- Close other applications

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Stockfish chess engine
- Ollama for local LLM inference
- Chess.com and Lichess for providing game data
- The chess community for inspiration

---

**Ready to dominate your chess games? Start analyzing! 🏆**
