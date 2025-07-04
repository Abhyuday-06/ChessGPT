#!/usr/bin/env python
"""
Enhanced Web UI Launcher
Starts the Enhanced Web UI with proper error handling
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("🚀 Starting Enhanced Chess Strategy Web UI...")
    print("🔍 Automatic game analysis enabled")
    print("🤖 Ollama LLM integration enabled")
    print("🌐 Open http://localhost:5000 in your browser")
    print("=" * 60)
    
    try:
        from enhanced_web_ui import app
        from enhanced_analyzer import enhanced_analyzer
        from ollama_llm import chess_llm
        
        # Check components
        print("✅ Enhanced analyzer loaded")
        
        # Check Ollama status
        if chess_llm.check_ollama_available():
            print("✅ Ollama is running")
            if chess_llm.check_model_available():
                print(f"✅ Model {chess_llm.model_name} is available")
            else:
                print(f"⚠️ Model {chess_llm.model_name} not found - will pull on first use")
        else:
            print("⚠️ Ollama not running - please start Ollama for LLM features")
        
        # Show available players
        available_players = enhanced_analyzer.get_available_players()
        print(f"📊 Available players: {', '.join(available_players) if available_players else 'None'}")
        
        print("\n🌐 Starting web server...")
        app.run(debug=False, host='0.0.0.0', port=5000)
        
    except KeyboardInterrupt:
        print("\n👋 Enhanced Web UI stopped by user")
    except Exception as e:
        print(f"❌ Error starting Enhanced Web UI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
