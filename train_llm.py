"""
Chess Strategy LLM Training Pipeline
Fine-tunes a small language model on chess strategy data
"""

import json
import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    TrainingArguments, 
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import Dataset
import os
from datetime import datetime
import numpy as np

class ChessStrategyTrainer:
    def __init__(self, model_name="microsoft/DialoGPT-small", max_length=512):
        """
        Initialize the chess strategy trainer
        
        Args:
            model_name: Hugging Face model to fine-tune (small models <7B)
            max_length: Maximum sequence length for training
        """
        self.model_name = model_name
        self.max_length = max_length
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        print(f"🚀 Initializing Chess Strategy Trainer")
        print(f"📦 Model: {model_name}")
        print(f"💻 Device: {self.device}")
        
        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Add special tokens for chess analysis
        special_tokens = {
            "pad_token": "<pad>",
            "eos_token": "<eos>",
            "additional_special_tokens": [
                "<OPPONENT_ANALYSIS>", 
                "</OPPONENT_ANALYSIS>",
                "<STRATEGY_RECOMMENDATION>", 
                "</STRATEGY_RECOMMENDATION>",
                "<OPENING>", 
                "</OPENING>",
                "<TACTIC>", 
                "</TACTIC>"
            ]
        }
        
        self.tokenizer.add_special_tokens(special_tokens)
        
        # Load model and resize embeddings for new tokens
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None
        )
        self.model.resize_token_embeddings(len(self.tokenizer))
        
        print(f"✅ Model loaded with {self.model.num_parameters():,} parameters")
    
    def format_training_example(self, entry):
        """
        Format a training example from the chess strategy dataset
        
        Args:
            entry: Single entry from chess_strategy_training_data.json
            
        Returns:
            Formatted string for training
        """
        
        # Extract opponent analysis
        opponent_name = entry['input']['opponent_profile']['player_name']
        weaknesses = entry['input']['opening_weaknesses']
        tactical_vulns = entry['input']['tactical_vulnerabilities']
        
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
        
        input_text += "</OPPONENT_ANALYSIS>\n\n"
        
        # Extract strategy recommendations
        strategy = entry['output']['strategic_recommendations']
        output_text = f"<STRATEGY_RECOMMENDATION>\n"
        
        for rec in strategy['opening_choices'][:2]:  # Top 2 recommendations
            output_text += f"<OPENING>\n"
            output_text += f"Target: {rec['target_opening']}\n"
            output_text += f"Method: {rec['exploitation_method']}\n"
            if rec['specific_lines']:
                output_text += f"Lines: {rec['specific_lines'][0]}\n"
            output_text += f"Reasoning: {rec['reasoning']}\n"
            output_text += f"</OPENING>\n"
        
        if strategy['tactical_approach']:
            output_text += f"<TACTIC>\n"
            for tactic in strategy['tactical_approach'][:2]:
                output_text += f"- {tactic}\n"
            output_text += f"</TACTIC>\n"
        
        output_text += f"Expected Success Rate: {entry['output']['expected_success_rate']:.1f}\n"
        output_text += "</STRATEGY_RECOMMENDATION><eos>"
        
        return input_text + output_text
    
    def prepare_dataset(self, json_file="chess_strategy_training_data.json"):
        """
        Prepare the dataset for training
        
        Args:
            json_file: Path to the training data JSON file
            
        Returns:
            Hugging Face Dataset object
        """
        print(f"📊 Preparing dataset from {json_file}")
        
        # Load training data
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📈 Found {len(data)} training examples")
        
        # Format examples
        formatted_examples = []
        for entry in data:
            try:
                formatted_text = self.format_training_example(entry)
                formatted_examples.append(formatted_text)
            except Exception as e:
                print(f"⚠️  Error formatting example: {e}")
                continue
        
        print(f"✅ Successfully formatted {len(formatted_examples)} examples")
        
        # Tokenize the data
        def tokenize_function(examples):
            # Tokenize each example
            tokenized = self.tokenizer(
                examples['text'], 
                truncation=True, 
                padding=True, 
                max_length=self.max_length,
                return_tensors="pt"
            )
            
            # For causal language modeling, labels are the same as input_ids
            tokenized["labels"] = tokenized["input_ids"].clone()
            
            return tokenized
        
        # Create dataset
        dataset = Dataset.from_dict({"text": formatted_examples})
        tokenized_dataset = dataset.map(tokenize_function, batched=True)
        
        print(f"🎯 Dataset prepared with {len(tokenized_dataset)} examples")
        return tokenized_dataset
    
    def train(self, dataset, output_dir="./chess_strategy_model", epochs=3, learning_rate=5e-5):
        """
        Fine-tune the model on chess strategy data
        
        Args:
            dataset: Prepared dataset
            output_dir: Directory to save the trained model
            epochs: Number of training epochs
            learning_rate: Learning rate for training
        """
        print(f"🎯 Starting training...")
        print(f"📁 Output directory: {output_dir}")
        print(f"🔄 Epochs: {epochs}")
        print(f"📈 Learning rate: {learning_rate}")
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            overwrite_output_dir=True,
            num_train_epochs=epochs,
            per_device_train_batch_size=2,  # Small batch size for limited GPU memory
            gradient_accumulation_steps=4,   # Accumulate gradients to simulate larger batch
            warmup_steps=100,
            learning_rate=learning_rate,
            logging_steps=10,
            save_steps=100,
            eval_steps=100,
            save_total_limit=2,
            prediction_loss_only=True,
            remove_unused_columns=False,
            dataloader_pin_memory=False,
            fp16=torch.cuda.is_available(),  # Use mixed precision if CUDA available
        )
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,  # We're doing causal language modeling, not masked LM
        )
        
        # Split dataset for training and validation
        train_size = int(0.9 * len(dataset))
        train_dataset = dataset.select(range(train_size))
        eval_dataset = dataset.select(range(train_size, len(dataset)))
        
        print(f"📊 Training samples: {len(train_dataset)}")
        print(f"📊 Validation samples: {len(eval_dataset)}")
        
        # Initialize trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator,
        )
        
        # Train the model
        print("🚀 Starting training...")
        trainer.train()
        
        # Save the model
        print(f"💾 Saving model to {output_dir}")
        trainer.save_model()
        self.tokenizer.save_pretrained(output_dir)
        
        print("✅ Training completed!")
        
        return trainer

def main():
    """Main training function"""
    print("🏁 Chess Strategy LLM Training Pipeline")
    print("=" * 50)
    
    # Initialize trainer with a small model
    # Options: microsoft/DialoGPT-small, distilgpt2, gpt2
    trainer = ChessStrategyTrainer(model_name="distilgpt2")
    
    # Prepare dataset
    dataset = trainer.prepare_dataset("chess_strategy_training_data.json")
    
    # Train the model
    trainer.train(dataset, epochs=5, learning_rate=5e-5)
    
    print("🎉 Training pipeline completed!")
    print("📁 Model saved to: ./chess_strategy_model")
    print("🔥 Ready for inference!")

if __name__ == "__main__":
    main()
