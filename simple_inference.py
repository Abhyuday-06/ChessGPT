"""
Simple Chess Strategy Inference Engine

This script uses the simple chess strategy predictor to generate strategies based on opponent analysis.
"""

import json
import os
import sys
import subprocess
from datetime import datetime
import argparse

# Import the simple predictor
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from simple_predictor import SimpleChessStrategyPredictor
except ImportError:
    print("⚠️ Simple predictor not found. Run simple_train.py first.")
    SimpleChessStrategyPredictor = None

class ChessStrategyInference:
    def __init__(self, model_path="./simple_chess_model"):
        """Initialize the inference engine"""
        self.model_path = model_path
        self.predictor = None
        
        self.load_model()
    
    def load_model(self):
        """Load the simple chess strategy predictor"""
        if SimpleChessStrategyPredictor is None:
            raise ImportError("Simple predictor not available. Run simple_train.py first.")
        
        try:
            self.predictor = SimpleChessStrategyPredictor(self.model_path)
            print("✅ Simple chess strategy predictor loaded successfully!")
            
        except Exception as e:
            print(f"❌ Error loading predictor: {e}")
            print("Make sure you've run simple_train.py first to create the model.")
            raise
    
    def analyze_opponent(self, username):
        """Run chess analysis on the opponent"""
        print(f"🔍 Analyzing opponent: {username}")
        
        try:
            # Run the chess analyzer
            result = subprocess.run([
                sys.executable, "chess_analyzer.py", username
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                print(f"❌ Chess analysis failed: {result.stderr}")
                return None
            
            print("✅ Chess analysis completed")
            
            # Load the latest analysis from the training data
            if os.path.exists("chess_strategy_training_data.json"):
                with open("chess_strategy_training_data.json", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Find the most recent analysis for this user
                user_analyses = []
                for entry in data:
                    player_name = entry.get('input', {}).get('opponent_profile', {}).get('player_name', '').lower()
                    if player_name == username.lower():
                        user_analyses.append(entry)
                
                if user_analyses:
                    # Get the most recent analysis
                    latest_analysis = user_analyses[-1]  # Take the last one
                    return latest_analysis
                else:
                    print(f"⚠️ No analysis found for user: {username}")
                    return None
            else:
                print("⚠️ No training data file found")
                return None
                
        except subprocess.TimeoutExpired:
            print("❌ Chess analysis timed out")
            return None
        except Exception as e:
            print(f"❌ Error during chess analysis: {e}")
            return None
    
    def format_input_for_predictor(self, analysis_data):
        """Format the analysis data for the simple predictor"""
        if not analysis_data:
            return None
        
        # Extract opponent profile
        opponent_profile = analysis_data.get('input', {}).get('opponent_profile', {})
        player_name = opponent_profile.get('player_name', 'Unknown')
        
        # Extract opening weaknesses
        opening_weaknesses = analysis_data.get('input', {}).get('opening_weaknesses', [])
        
        # Format input text
        input_text = f"Analyze opponent {player_name}:\n"
        
        if opening_weaknesses:
            input_text += "Opening Weaknesses:\n"
            for weakness in opening_weaknesses:
                opening = weakness.get('opening', 'Unknown')
                color = weakness.get('color', 'unknown').replace('as_', '')
                win_rate = weakness.get('win_rate', 0)
                input_text += f"- {opening} as {color}: {win_rate:.1f}% win rate\n"
        
        # Extract tactical vulnerabilities
        tactical_vulns = analysis_data.get('input', {}).get('tactical_vulnerabilities', [])
        if tactical_vulns:
            input_text += "Tactical Issues:\n"
            for vuln in tactical_vulns:
                opening = vuln.get('opening', 'Unknown')
                error_rate = vuln.get('error_rate', 0)
                input_text += f"- {opening}: {error_rate:.1f} errors per game\n"
        
        return input_text
    
    def generate_strategy(self, opponent_analysis):
        """Generate chess strategy using the simple predictor"""
        if not opponent_analysis:
            return "Unable to generate strategy: No input provided"
        
        if not self.predictor:
            return "Error: Predictor not loaded"
        
        try:
            strategy = self.predictor.predict_strategy(opponent_analysis)
            return strategy
                
        except Exception as e:
            return f"Error generating strategy: {e}"
    
    def get_strategy_for_opponent(self, username):
        """Complete pipeline: analyze opponent and generate strategy"""
        print(f"🎯 Generating strategy for opponent: {username}")
        
        # Step 1: Analyze opponent
        analysis_data = self.analyze_opponent(username)
        if not analysis_data:
            return {
                "error": f"Could not analyze opponent: {username}",
                "strategy": "Please check that the username is correct and try again.",
                "success": False
            }
        
        # Step 2: Format input for predictor
        predictor_input = self.format_input_for_predictor(analysis_data)
        if not predictor_input:
            return {
                "error": "Could not format analysis data for predictor",
                "strategy": "Analysis data formatting failed.",
                "success": False
            }
        
        # Step 3: Generate strategy
        strategy = self.generate_strategy(predictor_input)
        
        # Step 4: Return results
        analysis_date = datetime.now().strftime('%Y-%m-%d')
        
        return {
            "opponent": username,
            "analysis_date": analysis_date,
            "strategy": strategy,
            "success": True,
            "analysis_summary": {
                "input": predictor_input[:200] + "..." if len(predictor_input) > 200 else predictor_input
            }
        }

def main():
    parser = argparse.ArgumentParser(description="Generate chess strategies using simple predictor")
    parser.add_argument("--model", default="./simple_chess_model", help="Path to trained model")
    parser.add_argument("--username", help="Opponent username to analyze")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    
    args = parser.parse_args()
    
    # Initialize inference engine
    try:
        inference_engine = ChessStrategyInference(args.model)
    except Exception as e:
        print(f"❌ Failed to initialize inference engine: {e}")
        return
    
    if args.interactive:
        print("🎮 Interactive Chess Strategy Generator")
        print("Enter opponent usernames to get strategies. Type 'quit' to exit.")
        
        while True:
            username = input("\nEnter opponent username (or 'quit'): ").strip()
            
            if username.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not username:
                print("⚠️ Please enter a valid username")
                continue
            
            # Generate strategy
            result = inference_engine.get_strategy_for_opponent(username)
            
            if result.get("success"):
                print(f"\n🎯 Strategy for {result['opponent']}:")
                print(f"📅 Analysis Date: {result['analysis_date']}")
                print(f"🧠 Strategy:")
                print(result['strategy'])
            else:
                print(f"\n❌ {result.get('error', 'Unknown error')}")
                print(f"💡 {result.get('strategy', 'No strategy available')}")
    
    elif args.username:
        # Single username mode
        result = inference_engine.get_strategy_for_opponent(args.username)
        
        if result.get("success"):
            print(f"\n🎯 Strategy for {result['opponent']}:")
            print(f"📅 Analysis Date: {result['analysis_date']}")
            print(f"🧠 Strategy:")
            print(result['strategy'])
        else:
            print(f"\n❌ {result.get('error', 'Unknown error')}")
            print(f"💡 {result.get('strategy', 'No strategy available')}")
    
    else:
        print("Please specify --username or use --interactive mode")
        print("Example: python simple_inference.py --username hikaru")
        print("Example: python simple_inference.py --interactive")

if __name__ == "__main__":
    main()
