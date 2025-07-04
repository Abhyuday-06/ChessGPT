"""
Chess Strategy LLM Inference Engine
Loads the trained model and generates strategies for opponents
"""

import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import subprocess
import os
from datetime import datetime
import re

class ChessStrategyPredictor:
    def __init__(self, model_path="./chess_strategy_model"):
        """
        Initialize the chess strategy predictor
        
        Args:
            model_path: Path to the fine-tuned model
        """
        self.model_path = model_path
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        print(f"🚀 Loading Chess Strategy Predictor")
        print(f"📁 Model path: {model_path}")
        print(f"💻 Device: {self.device}")
        
        try:
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            self.model.eval()
            print("✅ Model loaded successfully!")
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            print("🔄 Falling back to base model...")
            # Fallback to base model if fine-tuned model not available
            self.tokenizer = AutoTokenizer.from_pretrained("distilgpt2")
            self.model = AutoModelForCausalLM.from_pretrained("distilgpt2")
            
        # Set pad token if not present
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
    
    def analyze_opponent(self, username):
        """
        Analyze an opponent using the chess_analyzer.py script
        
        Args:
            username: Chess.com username to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        print(f"🔍 Analyzing opponent: {username}")
        
        try:
            # Run the chess analyzer script
            result = subprocess.run(
                ["python", "chess_analyzer.py", username],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                print("✅ Analysis completed successfully")
                
                # Load the latest training data (which includes the new analysis)
                with open("chess_strategy_training_data.json", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Find the most recent entry for this player
                opponent_entries = [
                    entry for entry in data 
                    if entry.get('metadata', {}).get('player_analyzed', '').lower() == username.lower()
                ]
                
                if opponent_entries:
                    # Get the most recent analysis
                    latest_entry = max(opponent_entries, key=lambda x: x.get('metadata', {}).get('analysis_timestamp', ''))
                    return latest_entry
                else:
                    print(f"⚠️  No analysis data found for {username}")
                    return None
                    
            else:
                print(f"❌ Analysis failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("⏰ Analysis timed out")
            return None
        except Exception as e:
            print(f"❌ Error during analysis: {e}")
            return None
    
    def format_opponent_input(self, analysis_data):
        """
        Format opponent analysis data for the LLM
        
        Args:
            analysis_data: Analysis data from chess_analyzer.py
            
        Returns:
            Formatted input string
        """
        if not analysis_data:
            return None
            
        opponent_name = analysis_data['input']['opponent_profile']['player_name']
        weaknesses = analysis_data['input']['opening_weaknesses']
        tactical_vulns = analysis_data['input']['tactical_vulnerabilities']
        
        # Format input section
        input_text = f"<OPPONENT_ANALYSIS>\n"
        input_text += f"Opponent: {opponent_name}\n"
        input_text += f"Analysis Summary:\n"
        
        for weakness in weaknesses[:3]:  # Top 3 weaknesses
            input_text += f"- {weakness['opening']} ({weakness['eco']}) as {weakness['color'].replace('as_', '')}: "
            input_text += f"{weakness['win_rate']:.1f}% win rate in {weakness['sample_size']} games\n"
        
        if tactical_vulns:
            input_text += f"Tactical Vulnerabilities:\n"
            for vuln in tactical_vulns[:2]:  # Top 2 tactical issues
                input_text += f"- {vuln['opening']}: {vuln['error_rate']:.1f} errors per game\n"
        
        input_text += "</OPPONENT_ANALYSIS>\n\n<STRATEGY_RECOMMENDATION>\n"
        
        return input_text
    
    def generate_strategy(self, opponent_input, max_length=400, temperature=0.7):
        """
        Generate strategy using the fine-tuned model
        
        Args:
            opponent_input: Formatted opponent analysis
            max_length: Maximum length of generated text
            temperature: Sampling temperature
            
        Returns:
            Generated strategy text
        """
        print("🧠 Generating strategy with LLM...")
        
        try:
            # Tokenize input
            inputs = self.tokenizer.encode(opponent_input, return_tensors="pt")
            
            # Move to device
            inputs = inputs.to(self.device)
            
            # Generate strategy
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=len(inputs[0]) + max_length,
                    temperature=temperature,
                    do_sample=True,
                    top_p=0.9,
                    top_k=50,
                    pad_token_id=self.tokenizer.eos_token_id,
                    num_return_sequences=1
                )
            
            # Decode the generated text
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=False)
            
            # Extract just the strategy part (after the input)
            strategy_start = generated_text.find("<STRATEGY_RECOMMENDATION>")
            if strategy_start != -1:
                strategy_text = generated_text[strategy_start:]
                # Clean up the output
                strategy_text = strategy_text.replace("<eos>", "")
                return strategy_text
            else:
                return generated_text
                
        except Exception as e:
            print(f"❌ Error generating strategy: {e}")
            return None
    
    def parse_strategy_response(self, strategy_text):
        """
        Parse the generated strategy into structured format
        
        Args:
            strategy_text: Raw generated strategy text
            
        Returns:
            Structured strategy dictionary
        """
        try:
            strategy = {
                "opening_recommendations": [],
                "tactical_approach": [],
                "success_rate": None,
                "raw_response": strategy_text
            }
            
            # Extract opening recommendations
            opening_pattern = r"<OPENING>(.*?)</OPENING>"
            openings = re.findall(opening_pattern, strategy_text, re.DOTALL)
            
            for opening in openings:
                opening_info = {}
                # Extract target
                target_match = re.search(r"Target: (.*?)(?:\n|$)", opening)
                if target_match:
                    opening_info["target"] = target_match.group(1).strip()
                
                # Extract method
                method_match = re.search(r"Method: (.*?)(?:\n|$)", opening)
                if method_match:
                    opening_info["method"] = method_match.group(1).strip()
                
                # Extract lines
                lines_match = re.search(r"Lines: (.*?)(?:\n|$)", opening)
                if lines_match:
                    opening_info["lines"] = lines_match.group(1).strip()
                
                # Extract reasoning
                reasoning_match = re.search(r"Reasoning: (.*?)(?:\n|$)", opening)
                if reasoning_match:
                    opening_info["reasoning"] = reasoning_match.group(1).strip()
                
                if opening_info:
                    strategy["opening_recommendations"].append(opening_info)
            
            # Extract tactical approach
            tactic_pattern = r"<TACTIC>(.*?)</TACTIC>"
            tactics = re.findall(tactic_pattern, strategy_text, re.DOTALL)
            
            for tactic in tactics:
                tactic_lines = [line.strip().lstrip("- ") for line in tactic.split("\n") if line.strip()]
                strategy["tactical_approach"].extend(tactic_lines)
            
            # Extract success rate
            success_match = re.search(r"Expected Success Rate: ([\d.]+)", strategy_text)
            if success_match:
                strategy["success_rate"] = float(success_match.group(1))
            
            return strategy
            
        except Exception as e:
            print(f"⚠️  Error parsing strategy: {e}")
            return {"raw_response": strategy_text, "parse_error": str(e)}
    
    def get_strategy_for_opponent(self, username):
        """
        Complete pipeline: analyze opponent and generate strategy
        
        Args:
            username: Chess.com username to analyze
            
        Returns:
            Structured strategy recommendation
        """
        print(f"🎯 Getting strategy for opponent: {username}")
        print("=" * 50)
        
        # Step 1: Analyze opponent
        analysis_data = self.analyze_opponent(username)
        if not analysis_data:
            return {"error": "Failed to analyze opponent"}
        
        # Step 2: Format input for LLM
        opponent_input = self.format_opponent_input(analysis_data)
        if not opponent_input:
            return {"error": "Failed to format opponent data"}
        
        # Step 3: Generate strategy
        strategy_text = self.generate_strategy(opponent_input)
        if not strategy_text:
            return {"error": "Failed to generate strategy"}
        
        # Step 4: Parse strategy
        parsed_strategy = self.parse_strategy_response(strategy_text)
        
        # Add metadata
        parsed_strategy["opponent"] = username
        parsed_strategy["analysis_timestamp"] = datetime.now().isoformat()
        parsed_strategy["analysis_data"] = analysis_data
        
        print("✅ Strategy generation completed!")
        return parsed_strategy

def main():
    """Test the inference engine"""
    print("🎯 Chess Strategy LLM Inference Engine")
    print("=" * 50)
    
    # Initialize predictor
    predictor = ChessStrategyPredictor()
    
    # Test with a sample opponent
    username = input("Enter opponent username to analyze: ").strip()
    if not username:
        username = "hikaru"  # Default
    
    # Generate strategy
    strategy = predictor.get_strategy_for_opponent(username)
    
    # Display results
    print("\n" + "=" * 50)
    print("🎯 STRATEGY RECOMMENDATION")
    print("=" * 50)
    
    if "error" in strategy:
        print(f"❌ Error: {strategy['error']}")
        return
    
    print(f"🎮 Opponent: {strategy['opponent']}")
    
    if strategy.get("opening_recommendations"):
        print("\n📖 Opening Recommendations:")
        for i, opening in enumerate(strategy["opening_recommendations"], 1):
            print(f"  {i}. Target: {opening.get('target', 'N/A')}")
            print(f"     Method: {opening.get('method', 'N/A')}")
            if opening.get('lines'):
                print(f"     Lines: {opening.get('lines')}")
            if opening.get('reasoning'):
                print(f"     Reasoning: {opening.get('reasoning')}")
            print()
    
    if strategy.get("tactical_approach"):
        print("⚔️  Tactical Approach:")
        for tactic in strategy["tactical_approach"]:
            print(f"  • {tactic}")
        print()
    
    if strategy.get("success_rate"):
        print(f"📈 Expected Success Rate: {strategy['success_rate']:.1f}")
    
    print(f"\n⏰ Generated at: {strategy['analysis_timestamp']}")

if __name__ == "__main__":
    main()
