"""
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
                self.training_examples = f.read().split("\n\n")
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
