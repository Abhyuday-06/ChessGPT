"""
Ollama-based Chess Strategy LLM Training and Inference
Uses local Ollama models (Gemma2, Llama3, Mistral) for chess strategy generation
"""

import json
import requests
import os
import subprocess
import time
from typing import Dict, Any, List, Optional

class OllamaChessLLM:
    def __init__(self, model_name: str = None):
        # Load model name from config if available
        if model_name is None:
            model_name = self.load_model_from_config()
        
        self.model_name = model_name
        self.ollama_url = "http://localhost:11434"
        self.training_data_file = "chess_strategy_training_data.json"
        self.system_prompt = """You are a world-class chess strategy expert. Given an opponent's weaknesses and playing patterns, provide specific, actionable chess strategies to exploit those weaknesses. Focus on concrete opening moves, tactical patterns, and strategic plans."""
    
    def load_model_from_config(self) -> str:
        """Load model name from config file"""
        try:
            if os.path.exists("ollama_config.json"):
                with open("ollama_config.json", "r") as f:
                    config = json.load(f)
                return config.get("model_name", "gemma2:2b")
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
        
        return "gemma2:2b"  # Default model
        
    def check_ollama_available(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def check_model_available(self) -> bool:
        """Check if the specified model is available"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return any(model.get('name', '').startswith(self.model_name) for model in models)
            return False
        except:
            return False
    
    def pull_model(self) -> bool:
        """Pull the model if not available"""
        try:
            print(f"🔄 Pulling model {self.model_name}...")
            response = requests.post(
                f"{self.ollama_url}/api/pull",
                json={"name": self.model_name},
                stream=True,
                timeout=300
            )
            
            if response.status_code == 200:
                print(f"✅ Model {self.model_name} pulled successfully")
                return True
            else:
                print(f"❌ Failed to pull model: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error pulling model: {e}")
            return False
    
    def setup_model(self) -> bool:
        """Setup the model (pull if necessary)"""
        if not self.check_ollama_available():
            print("❌ Ollama is not running. Please start Ollama first.")
            return False
        
        if not self.check_model_available():
            print(f"🔄 Model {self.model_name} not found. Pulling...")
            return self.pull_model()
        
        print(f"✅ Model {self.model_name} is available")
        return True
    
    def load_training_data(self) -> List[Dict[str, Any]]:
        """Load training data from JSON file"""
        if not os.path.exists(self.training_data_file):
            return []
        
        try:
            with open(self.training_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            print(f"Error loading training data: {e}")
            return []
    
    def format_training_example(self, entry: Dict[str, Any]) -> Dict[str, str]:
        """Format a training example for the LLM"""
        try:
            if not isinstance(entry, dict):
                return None
            
            # Extract input information
            input_data = entry.get('input', {})
            output_data = entry.get('output', {})
            
            if not input_data or not output_data:
                return None
            
            # Format opponent info
            opponent_profile = input_data.get('opponent_profile', {})
            player_name = opponent_profile.get('player_name', 'Unknown')
            
            # Format weaknesses
            weaknesses = input_data.get('opponent_weaknesses', [])
            weakness_text = ""
            for weakness in weaknesses:
                if isinstance(weakness, dict):
                    weakness_text += f"- {weakness.get('weakness_type', 'Unknown')}: {weakness.get('details', '')}\n"
            
            # Format input prompt
            input_prompt = f"""Chess Player Analysis: {player_name}

Opponent Weaknesses:
{weakness_text}

Provide a comprehensive strategy to exploit these weaknesses."""
            
            # Format output strategy
            recommendations = output_data.get('strategic_recommendations', [])
            opening_suggestions = output_data.get('opening_suggestions', [])
            tactical_advice = output_data.get('tactical_advice', [])
            
            output_strategy = "Strategic Recommendations:\n"
            for rec in recommendations:
                if isinstance(rec, dict):
                    output_strategy += f"• {rec.get('recommendation', '')}\n"
                    if rec.get('rationale'):
                        output_strategy += f"  Rationale: {rec.get('rationale', '')}\n"
            
            output_strategy += "\nOpening Suggestions:\n"
            for opening in opening_suggestions:
                if isinstance(opening, dict):
                    output_strategy += f"• {opening.get('opening', '')}: {opening.get('reason', '')}\n"
            
            output_strategy += "\nTactical Advice:\n"
            for advice in tactical_advice:
                output_strategy += f"• {advice}\n"
            
            return {
                'input': input_prompt,
                'output': output_strategy
            }
        except Exception as e:
            print(f"Error formatting training example: {e}")
            return None
    
    def create_few_shot_prompt(self, opponent_analysis: str, num_examples: int = 3) -> str:
        """Create a few-shot prompt with training examples"""
        training_data = self.load_training_data()
        
        if not training_data:
            return f"{self.system_prompt}\n\n{opponent_analysis}"
        
        # Format examples
        examples = []
        for i, entry in enumerate(training_data[:num_examples]):
            example = self.format_training_example(entry)
            if example:
                examples.append(f"Example {i+1}:\nInput: {example['input']}\nOutput: {example['output']}")
        
        # Create full prompt
        prompt = f"{self.system_prompt}\n\nHere are some examples:\n\n"
        prompt += "\n\n".join(examples)
        prompt += f"\n\nNow analyze this opponent:\n{opponent_analysis}"
        
        return prompt
    
    def generate_strategy(self, opponent_analysis: str) -> str:
        """Generate strategy using Ollama LLM"""
        if not self.setup_model():
            return "Error: Could not setup Ollama model"
        
        try:
            # Create few-shot prompt
            prompt = self.create_few_shot_prompt(opponent_analysis)
            
            # Make request to Ollama
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 1000
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'No response generated')
            else:
                return f"Error: HTTP {response.status_code}"
                
        except Exception as e:
            return f"Error generating strategy: {str(e)}"
    
    def fine_tune_model(self, training_data_file: str = None) -> bool:
        """Fine-tune the model with chess strategy data"""
        if not training_data_file:
            training_data_file = self.training_data_file
        
        if not os.path.exists(training_data_file):
            print(f"❌ Training data file not found: {training_data_file}")
            return False
        
        print(f"🎯 Fine-tuning model {self.model_name} with chess strategy data...")
        
        try:
            # Load training data
            with open(training_data_file, 'r', encoding='utf-8') as f:
                training_data = json.load(f)
            
            if not training_data:
                print("❌ No training data found")
                return False
            
            # Create a Modelfile for fine-tuning
            modelfile_content = f"""FROM {self.model_name}
SYSTEM {self.system_prompt}

# Training examples
"""
            
            # Add training examples to the Modelfile
            for i, entry in enumerate(training_data[:50]):  # Limit to 50 examples
                example = self.format_training_example(entry)
                if example:
                    modelfile_content += f"""
# Example {i+1}
USER {example['input']}
ASSISTANT {example['output']}
"""
            
            # Save Modelfile
            with open("ChessGPT_Modelfile", "w", encoding="utf-8") as f:
                f.write(modelfile_content)
            
            # Create the fine-tuned model
            fine_tuned_model_name = f"chessgpt-{self.model_name}"
            
            print(f"🚀 Creating fine-tuned model: {fine_tuned_model_name}")
            
            # Use ollama create command
            result = subprocess.run([
                "ollama", "create", fine_tuned_model_name, "-f", "ChessGPT_Modelfile"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Fine-tuned model created: {fine_tuned_model_name}")
                # Update the model name to use the fine-tuned version
                self.model_name = fine_tuned_model_name
                return True
            else:
                print(f"❌ Error creating fine-tuned model: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error fine-tuning model: {e}")
            return False
    
    def chat_with_model(self, message: str, use_chess_context: bool = True) -> str:
        """Chat with the model (can be used for general chat or chess-specific)"""
        if not self.setup_model():
            return "Error: Could not setup Ollama model"
        
        try:
            # Prepare the prompt
            if use_chess_context:
                prompt = f"{self.system_prompt}\n\nUser: {message}\nAssistant:"
            else:
                prompt = message
            
            # Make request to Ollama
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 500
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'No response generated')
            else:
                return f"Error: HTTP {response.status_code}"
                
        except Exception as e:
            return f"Error chatting with model: {str(e)}"
    
    def test_model(self) -> bool:
        """Test the model with a simple query"""
        try:
            test_prompt = "What is the best opening move in chess?"
            response = self.chat_with_model(test_prompt, use_chess_context=False)
            
            if response and not response.startswith("Error"):
                print(f"✅ Model test successful: {response[:100]}...")
                return True
            else:
                print(f"❌ Model test failed: {response}")
                return False
                
        except Exception as e:
            print(f"❌ Model test error: {e}")
            return False

# Global LLM instance
chess_llm = OllamaChessLLM()
