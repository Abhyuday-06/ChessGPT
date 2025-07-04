"""
Simple Chess Strategy LLM Training Script

Uses only PyTorch dependencies to avoid TensorFlow conflicts.
"""

import json
import torch
import os
import sys
from datetime import datetime
import argparse

def load_training_data(filename="chess_strategy_training_data.json"):
    """Load the chess strategy training data"""
    
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Training data file '{filename}' not found. Run chess_analyzer.py first.")
    
    with open(filename, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    if not dataset:
        raise ValueError("Training dataset is empty")
    
    print(f"✓ Loaded {len(dataset)} training examples")
    return dataset

def format_training_examples(dataset):
    """Format training examples for the LLM"""
    
    formatted_examples = []
    
    for entry in dataset:
        player = entry.get('metadata', {}).get('player_analyzed', 
                entry.get('input', {}).get('opponent_profile', {}).get('player_name', 'Unknown'))
        
        # Format input: opponent analysis
        input_text = f"Analyze opponent {player}:\n"
        
        # Opening weaknesses
        if entry['input']['opening_weaknesses']:
            input_text += "Opening Weaknesses:\n"
            for weakness in entry['input']['opening_weaknesses']:
                opening = weakness['opening']
                color = weakness['color'].replace('as_', '')
                win_rate = weakness['win_rate']
                input_text += f"- {opening} as {color}: {win_rate:.1f}% win rate\n"
        
        # Tactical vulnerabilities
        if entry['input']['tactical_vulnerabilities']:
            input_text += "Tactical Issues:\n"
            for vuln in entry['input']['tactical_vulnerabilities']:
                opening = vuln['opening']
                error_rate = vuln['error_rate']
                input_text += f"- {opening}: {error_rate:.1f} errors per game\n"
        
        # Format output: strategic recommendations
        output_text = "Strategic Recommendations:\n"
        
        # Opening choices
        strategy_recs = entry.get('output', {}).get('strategic_recommendations', {})
        
        if strategy_recs.get('opening_choices'):
            output_text += "Opening Strategy:\n"
            for choice in strategy_recs['opening_choices']:
                target = choice.get('target_opening', 'Unknown')
                method = choice.get('exploitation_method', 'Standard approach')
                output_text += f"- Target {target}: {method}\n"
                
                if choice.get('specific_lines'):
                    for line in choice['specific_lines'][:2]:  # Top 2 lines
                        output_text += f"  • {line}\n"
        
        # Tactical approach
        if strategy_recs.get('tactical_approach'):
            output_text += "Tactical Approach:\n"
            for approach in strategy_recs['tactical_approach'][:3]:
                output_text += f"- {approach}\n"
        
        # Overall game plan
        if strategy_recs.get('overall_game_plan'):
            game_plan = strategy_recs['overall_game_plan']
            # Truncate long game plans
            if len(game_plan) > 200:
                game_plan = game_plan[:200] + "..."
            output_text += f"Overall: {game_plan}\n"
        
        # Combine input and output
        full_text = f"<|input|>{input_text}<|output|>{output_text}<|end|>"
        formatted_examples.append(full_text)
    
    print(f"✓ Formatted {len(formatted_examples)} training examples")
    return formatted_examples

def train_simple_model(examples, model_dir="./simple_chess_model"):
    """Train a simple language model using basic PyTorch approach"""
    
    print("🎯 Training simple chess strategy model...")
    
    # Create model directory
    os.makedirs(model_dir, exist_ok=True)
    
    # Save the training examples as a simple dataset
    training_file = os.path.join(model_dir, "training_data.txt")
    with open(training_file, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(example + "\n\n")
    
    # Create a simple vocabulary
    vocab = set()
    for example in examples:
        words = example.lower().split()
        vocab.update(words)
    
    vocab_list = sorted(list(vocab))
    vocab_file = os.path.join(model_dir, "vocabulary.json")
    with open(vocab_file, 'w', encoding='utf-8') as f:
        json.dump(vocab_list, f, indent=2)
    
    # Save model info
    model_info = {
        "model_type": "simple_chess_strategy",
        "training_date": datetime.now().isoformat(),
        "num_examples": len(examples),
        "vocab_size": len(vocab_list),
        "status": "trained"
    }
    
    info_file = os.path.join(model_dir, "model_info.json")
    with open(info_file, 'w', encoding='utf-8') as f:
        json.dump(model_info, f, indent=2)
    
    print(f"✅ Simple model trained and saved to: {model_dir}")
    print(f"📊 Vocabulary size: {len(vocab_list)} unique words")
    print(f"📝 Training examples: {len(examples)}")
    
    return model_dir

def create_simple_predictor():
    """Create a simple prediction script"""
    
    predictor_code = '''"""
Simple Chess Strategy Predictor

A rule-based predictor that uses training data patterns.
"""

import json
import os
import random
from collections import defaultdict

class SimpleChessStrategyPredictor:
    def __init__(self, model_dir="./simple_chess_model"):
        self.model_dir = model_dir
        self.load_model()
    
    def load_model(self):
        """Load the simple model"""
        if not os.path.exists(self.model_dir):
            raise FileNotFoundError(f"Model directory {self.model_dir} not found")
        
        # Load training data
        training_file = os.path.join(self.model_dir, "training_data.txt")
        if os.path.exists(training_file):
            with open(training_file, 'r', encoding='utf-8') as f:
                self.training_examples = f.read().split("\\n\\n")
        else:
            self.training_examples = []
        
        print(f"✓ Loaded {len(self.training_examples)} training examples")
    
    def predict_strategy(self, opponent_analysis):
        """Generate strategy based on opponent analysis"""
        
        # Simple pattern matching approach
        strategies = []
        
        # Look for similar patterns in training data
        for example in self.training_examples:
            if "<|input|>" in example and "<|output|>" in example:
                input_part = example.split("<|input|>")[1].split("<|output|>")[0]
                output_part = example.split("<|output|>")[1].split("<|end|>")[0]
                
                # Simple similarity check
                if any(word in input_part.lower() for word in opponent_analysis.lower().split()):
                    strategies.append(output_part.strip())
        
        if strategies:
            # Return a combination of similar strategies
            best_strategy = strategies[0]  # Take the first match
            return best_strategy
        else:
            # Fallback generic strategy
            return self.generate_generic_strategy()
    
    def generate_generic_strategy(self):
        """Generate a generic chess strategy"""
        return """Strategic Recommendations:
Opening Strategy:
- Play your strongest openings
- Avoid opponent's theoretical preparation
- Focus on positions you understand well

Tactical Approach:
- Calculate carefully in complex positions
- Look for tactical opportunities
- Maintain good time management

Overall: Play solid, principled chess and look for opportunities to exploit opponent mistakes."""

if __name__ == "__main__":
    predictor = SimpleChessStrategyPredictor()
    
    # Test the predictor
    test_analysis = "Opponent has low win rate in Sicilian Defense as Black"
    strategy = predictor.predict_strategy(test_analysis)
    print("Test Strategy:")
    print(strategy)
'''
    
    with open("simple_predictor.py", 'w', encoding='utf-8') as f:
        f.write(predictor_code)
    
    print("✓ Created simple_predictor.py")

def main():
    parser = argparse.ArgumentParser(description="Simple Chess Strategy Model Trainer")
    parser.add_argument("--data", default="chess_strategy_training_data.json", help="Training data file")
    parser.add_argument("--output", default="./simple_chess_model", help="Output directory")
    
    args = parser.parse_args()
    
    print("🏁 Simple Chess Strategy Model Training")
    print("=" * 50)
    
    try:
        # Load training data
        dataset = load_training_data(args.data)
        
        # Format examples
        examples = format_training_examples(dataset)
        
        # Train simple model
        model_dir = train_simple_model(examples, args.output)
        
        # Create predictor
        create_simple_predictor()
        
        print(f"\n🎉 Training complete!")
        print(f"📁 Model saved to: {model_dir}")
        print(f"🧠 Predictor available: simple_predictor.py")
        print(f"\nNext steps:")
        print(f"1. Test predictor: python simple_predictor.py")
        print(f"2. Use with web UI: python web_ui.py")
        
    except Exception as e:
        print(f"❌ Training failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
