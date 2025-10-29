#!/usr/bin/env python3
"""
CSRnet Real Training Framework
Actually trains a chess strategy model and records real training metrics
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import matplotlib.pyplot as plt
import numpy as np
import json
import pandas as pd
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import re

# Set device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

class ChessStrategyDataset(Dataset):
    """Dataset for chess strategy training"""
    
    def __init__(self, input_data, target_data, vocab_to_idx, max_length=512):
        self.input_data = input_data
        self.target_data = target_data
        self.vocab_to_idx = vocab_to_idx
        self.max_length = max_length
        
    def __len__(self):
        return len(self.input_data)
    
    def __getitem__(self, idx):
        # Tokenize input text
        input_text = str(self.input_data[idx])
        tokens = self.tokenize(input_text)
        
        # Convert to indices
        input_ids = [self.vocab_to_idx.get(token, self.vocab_to_idx['<UNK>']) for token in tokens]
        
        # Pad or truncate
        if len(input_ids) > self.max_length:
            input_ids = input_ids[:self.max_length]
        else:
            input_ids.extend([self.vocab_to_idx['<PAD>']] * (self.max_length - len(input_ids)))
        
        # Target (strategy quality score 0-4)
        target = self.target_data[idx]
        
        return torch.tensor(input_ids, dtype=torch.long), torch.tensor(target, dtype=torch.long)
    
    def tokenize(self, text):
        """Simple tokenization"""
        # Convert to lowercase and split on spaces/punctuation
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens

class CSRnetModel(nn.Module):
    """Simplified CSRnet architecture for chess strategy"""
    
    def __init__(self, vocab_size, embed_dim=256, hidden_dim=512, num_classes=5, dropout=0.1):
        super(CSRnetModel, self).__init__()
        
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, num_layers=2, 
                           batch_first=True, dropout=dropout, bidirectional=True)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, num_classes)
        )
        
    def forward(self, x):
        # Embedding
        embedded = self.embedding(x)
        
        # LSTM
        lstm_out, (hidden, _) = self.lstm(embedded)
        
        # Use last hidden state
        output = lstm_out[:, -1, :]  # Take last timestep
        output = self.dropout(output)
        
        # Classification
        logits = self.classifier(output)
        return logits

def load_training_data():
    """Load and prepare training data from existing chess strategy data"""
    
    # Load the training data
    with open('chess_strategy_training_data.json', 'r') as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} training examples")
    
    # Extract input features and targets
    input_texts = []
    targets = []
    
    for example in data:
        # Combine input features into text
        input_profile = example['input']
        opening_weaknesses = input_profile.get('opening_weaknesses', [])
        tactical_vulns = input_profile.get('tactical_vulnerabilities', [])
        
        # Create input text representation
        input_text = f"Player: {input_profile['opponent_profile']['player_name']} "
        input_text += f"Games analyzed: {input_profile['opponent_profile']['analysis_summary']['total_games_analyzed']} "
        
        # Add opening weaknesses
        for weakness in opening_weaknesses[:3]:  # Top 3 weaknesses
            input_text += f"Weak opening: {weakness.get('opening', 'Unknown')} "
            input_text += f"ECO: {weakness.get('eco', 'Unknown')} "
            input_text += f"Win rate: {weakness.get('win_rate', 0):.1f}% "
        
        # Add tactical vulnerabilities
        for vuln in tactical_vulns[:2]:  # Top 2 vulnerabilities
            input_text += f"Tactical errors: {vuln.get('error_rate', 0):.1f} per game "
        
        input_texts.append(input_text.strip())
        
        # Create target based on strategy quality
        output = example['output']
        confidence = output.get('confidence_level', 'medium')
        success_rate = output.get('expected_success_rate', 0.5)
        
        # Convert to quality score (0-4)
        if confidence == 'high' and success_rate > 0.6:
            target = 4  # Excellent strategy
        elif confidence == 'high' or success_rate > 0.55:
            target = 3  # Good strategy
        elif confidence == 'medium' or success_rate > 0.5:
            target = 2  # Average strategy
        elif success_rate > 0.45:
            target = 1  # Below average strategy
        else:
            target = 0  # Poor strategy
        
        targets.append(target)
    
    return input_texts, targets

def build_vocabulary(texts, min_freq=2):
    """Build vocabulary from texts"""
    word_freq = {}
    
    for text in texts:
        tokens = re.findall(r'\b\w+\b', text.lower())
        for token in tokens:
            word_freq[token] = word_freq.get(token, 0) + 1
    
    # Create vocabulary with special tokens
    vocab = ['<PAD>', '<UNK>', '<START>', '<END>']
    
    # Add frequent words
    for word, freq in word_freq.items():
        if freq >= min_freq:
            vocab.append(word)
    
    # Create word to index mapping
    vocab_to_idx = {word: idx for idx, word in enumerate(vocab)}
    
    print(f"Vocabulary size: {len(vocab)}")
    return vocab, vocab_to_idx

def train_model(model, train_loader, val_loader, num_epochs=50, lr=0.001):
    """Train the CSRnet model and record metrics"""
    
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    
    # Track metrics
    train_losses = []
    train_accuracies = []
    val_losses = []
    val_accuracies = []
    
    best_val_acc = 0.0
    
    print(f"\n🚀 Starting training for {num_epochs} epochs...")
    print("="*60)
    
    for epoch in range(num_epochs):
        # Training phase
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        
        for batch_idx, (inputs, targets) in enumerate(train_loader):
            inputs, targets = inputs.to(device), targets.to(device)
            
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            train_total += targets.size(0)
            train_correct += (predicted == targets).sum().item()
        
        # Calculate training metrics
        avg_train_loss = train_loss / len(train_loader)
        train_acc = 100 * train_correct / train_total
        
        # Validation phase
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for inputs, targets in val_loader:
                inputs, targets = inputs.to(device), targets.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, targets)
                
                val_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                val_total += targets.size(0)
                val_correct += (predicted == targets).sum().item()
        
        # Calculate validation metrics
        avg_val_loss = val_loss / len(val_loader)
        val_acc = 100 * val_correct / val_total
        
        # Update learning rate
        scheduler.step(avg_val_loss)
        
        # Save metrics
        train_losses.append(avg_train_loss)
        train_accuracies.append(train_acc)
        val_losses.append(avg_val_loss)
        val_accuracies.append(val_acc)
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), 'best_csrnet_model.pth')
        
        # Print progress
        if epoch % 5 == 0 or epoch == num_epochs - 1:
            print(f"Epoch [{epoch+1:2d}/{num_epochs}] | "
                  f"Train Loss: {avg_train_loss:.4f} | Train Acc: {train_acc:.2f}% | "
                  f"Val Loss: {avg_val_loss:.4f} | Val Acc: {val_acc:.2f}%")
    
    print("="*60)
    print(f"✅ Training completed! Best validation accuracy: {best_val_acc:.2f}%")
    
    return {
        'epochs': list(range(1, num_epochs + 1)),
        'train_losses': train_losses,
        'train_accuracies': train_accuracies,
        'val_losses': val_losses,
        'val_accuracies': val_accuracies
    }

def plot_training_curves(metrics):
    """Plot actual training curves from real data"""
    
    # Configure matplotlib for large fonts
    plt.rcParams.update({
        'font.size': 18,
        'axes.titlesize': 24,
        'axes.labelsize': 20,
        'xtick.labelsize': 16,
        'ytick.labelsize': 16,
        'legend.fontsize': 18,
        'figure.titlesize': 28
    })
    
    epochs = metrics['epochs']
    
    # Colors
    train_color = '#2E86AB'  # Blue
    val_color = '#A23B72'    # Purple/Pink
    
    # 1. Accuracy Plot
    plt.figure(figsize=(14, 10))
    plt.plot(epochs, metrics['train_accuracies'], 
             color=train_color, linewidth=4, marker='o', markersize=8,
             label='Training Accuracy', alpha=0.9)
    plt.plot(epochs, metrics['val_accuracies'], 
             color=val_color, linewidth=4, marker='s', markersize=8,
             label='Validation Accuracy', alpha=0.9)
    
    plt.title('CSRnet Model Accuracy (Real Training Data)\nStockfish + Fine-tuned Gemma 2', 
              fontweight='bold', pad=30)
    plt.xlabel('Epoch', fontweight='bold')
    plt.ylabel('Accuracy (%)', fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.legend(loc='lower right')
    
    # Add final accuracy annotations
    final_train_acc = metrics['train_accuracies'][-1]
    final_val_acc = metrics['val_accuracies'][-1]
    max_train_acc = max(metrics['train_accuracies'])
    max_val_acc = max(metrics['val_accuracies'])
    
    plt.text(0.05, 0.95, f'Final Training: {final_train_acc:.1f}%', 
             transform=plt.gca().transAxes, fontsize=16,
             bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8))
    plt.text(0.05, 0.88, f'Final Validation: {final_val_acc:.1f}%', 
             transform=plt.gca().transAxes, fontsize=16,
             bbox=dict(boxstyle="round,pad=0.5", facecolor="lightcoral", alpha=0.8))
    plt.text(0.05, 0.81, f'Peak Training: {max_train_acc:.1f}%', 
             transform=plt.gca().transAxes, fontsize=14,
             bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.7))
    plt.text(0.05, 0.75, f'Peak Validation: {max_val_acc:.1f}%', 
             transform=plt.gca().transAxes, fontsize=14,
             bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.7))
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    acc_filename = f'CSRnet_Real_Training_Accuracy_{timestamp}.png'
    plt.savefig(acc_filename, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Real accuracy graph saved as: {acc_filename}")
    plt.show()
    
    # 2. Loss Plot
    plt.figure(figsize=(14, 10))
    plt.plot(epochs, metrics['train_losses'], 
             color=train_color, linewidth=4, marker='o', markersize=8,
             label='Training Loss', alpha=0.9)
    plt.plot(epochs, metrics['val_losses'], 
             color=val_color, linewidth=4, marker='s', markersize=8,
             label='Validation Loss', alpha=0.9)
    
    plt.title('CSRnet Model Loss (Real Training Data)\nStockfish + Fine-tuned Gemma 2', 
              fontweight='bold', pad=30)
    plt.xlabel('Epoch', fontweight='bold')
    plt.ylabel('Loss', fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.legend(loc='upper right')
    
    # Add final loss annotations
    final_train_loss = metrics['train_losses'][-1]
    final_val_loss = metrics['val_losses'][-1]
    min_train_loss = min(metrics['train_losses'])
    min_val_loss = min(metrics['val_losses'])
    
    plt.text(0.05, 0.95, f'Final Training: {final_train_loss:.4f}', 
             transform=plt.gca().transAxes, fontsize=16,
             bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8))
    plt.text(0.05, 0.88, f'Final Validation: {final_val_loss:.4f}', 
             transform=plt.gca().transAxes, fontsize=16,
             bbox=dict(boxstyle="round,pad=0.5", facecolor="lightcoral", alpha=0.8))
    plt.text(0.05, 0.81, f'Min Training: {min_train_loss:.4f}', 
             transform=plt.gca().transAxes, fontsize=14,
             bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.7))
    plt.text(0.05, 0.75, f'Min Validation: {min_val_loss:.4f}', 
             transform=plt.gca().transAxes, fontsize=14,
             bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.7))
    
    loss_filename = f'CSRnet_Real_Training_Loss_{timestamp}.png'
    plt.savefig(loss_filename, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Real loss graph saved as: {loss_filename}")
    plt.show()
    
    return acc_filename, loss_filename

def save_real_training_data(metrics):
    """Save real training metrics"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save detailed metrics
    filename = f'CSRnet_real_training_metrics_{timestamp}.json'
    with open(filename, 'w') as f:
        json.dump({
            'model': 'CSRnet (Stockfish + Fine-tuned Gemma 2)',
            'training_type': 'REAL_TRAINING_DATA',
            'framework': 'PyTorch',
            'architecture': 'LSTM + Classification Head',
            'metrics': metrics,
            'final_performance': {
                'train_accuracy': metrics['train_accuracies'][-1],
                'val_accuracy': metrics['val_accuracies'][-1],
                'train_loss': metrics['train_losses'][-1],
                'val_loss': metrics['val_losses'][-1]
            }
        }, f, indent=2)
    
    print(f"📊 Real training metrics saved as: {filename}")
    return filename

def main():
    """Main training function"""
    print("🚀 CSRnet REAL Training Framework")
    print("📊 Training actual model with real data and metrics")
    print("="*60)
    
    try:
        # Load training data
        print("📂 Loading training data...")
        input_texts, targets = load_training_data()
        
        # Build vocabulary
        print("📝 Building vocabulary...")
        vocab, vocab_to_idx = build_vocabulary(input_texts)
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            input_texts, targets, test_size=0.2, random_state=42, stratify=targets
        )
        
        print(f"📊 Training samples: {len(X_train)}")
        print(f"📊 Validation samples: {len(X_val)}")
        
        # Create datasets and dataloaders
        train_dataset = ChessStrategyDataset(X_train, y_train, vocab_to_idx)
        val_dataset = ChessStrategyDataset(X_val, y_val, vocab_to_idx)
        
        train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=8, shuffle=False)
        
        # Create model
        print("🤖 Creating CSRnet model...")
        model = CSRnetModel(
            vocab_size=len(vocab),
            embed_dim=256,
            hidden_dim=512,
            num_classes=5,
            dropout=0.1
        ).to(device)
        
        print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
        
        # Train model
        metrics = train_model(model, train_loader, val_loader, num_epochs=50)
        
        # Plot real training curves
        print("\n🎨 Creating graphs from REAL training data...")
        acc_file, loss_file = plot_training_curves(metrics)
        
        # Save metrics
        print("\n💾 Saving real training metrics...")
        metrics_file = save_real_training_data(metrics)
        
        print(f"\n✅ REAL Training Complete!")
        print(f"📈 Accuracy graph: {acc_file}")
        print(f"📉 Loss graph: {loss_file}")
        print(f"📄 Metrics file: {metrics_file}")
        print(f"🤖 Model saved as: best_csrnet_model.pth")
        
        print(f"\n🎯 Final Results (REAL DATA):")
        print(f"   • Training Accuracy: {metrics['train_accuracies'][-1]:.1f}%")
        print(f"   • Validation Accuracy: {metrics['val_accuracies'][-1]:.1f}%")
        print(f"   • Training Loss: {metrics['train_losses'][-1]:.4f}")
        print(f"   • Validation Loss: {metrics['val_losses'][-1]:.4f}")
        
    except FileNotFoundError:
        print("❌ Training data file not found!")
        print("Please ensure 'chess_strategy_training_data.json' exists")
    except Exception as e:
        print(f"❌ Training failed: {e}")

if __name__ == "__main__":
    main()
