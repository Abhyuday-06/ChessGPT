#!/usr/bin/env python3
"""
Gemma2 Model Architecture Detailed Diagram
Creates a detailed technical diagram of the Gemma2:2B model architecture
showing all layers, dimensions, and data transformations.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, FancyArrowPatch
import numpy as np

# Configure matplotlib for high-quality output
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['font.family'] = 'Arial'

def create_detailed_model_diagram():
    """Create detailed Gemma2:2B model architecture diagram"""
    
    # Create figure with appropriate size
    fig, ax = plt.subplots(1, 1, figsize=(14, 16))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 16)
    ax.axis('off')
    
    # Define colors for different layer types
    colors = {
        'embedding': '#FFE5B4',    # Light Orange
        'attention': '#E6E6FA',    # Lavender  
        'feedforward': '#98FB98',  # Pale Green
        'normalization': '#FFB6C1', # Light Pink
        'output': '#87CEEB',       # Sky Blue
        'data_flow': '#F0F8FF',    # Alice Blue
        'parameters': '#FFEFD5'    # Papaya Whip
    }
    
    # Title
    ax.text(7, 15.5, 'Gemma2:2B Model Architecture', 
            fontsize=18, fontweight='bold', ha='center')
    ax.text(7, 15.1, 'Transformer-based Chess Strategy Language Model', 
            fontsize=12, ha='center', style='italic')
    
    # ===== INPUT LAYER =====
    y_pos = 14
    
    # Input Text Box
    input_box = FancyBboxPatch((1, y_pos-0.3), 12, 0.6, 
                              boxstyle="round,pad=0.05", 
                              facecolor=colors['data_flow'], alpha=0.9,
                              edgecolor='black', linewidth=1)
    ax.add_patch(input_box)
    ax.text(7, y_pos, 'INPUT: "Chess Player Analysis: thibault. Opponent Weaknesses: ECO C30..."', 
            fontweight='bold', ha='center', fontsize=11)
    
    # Arrow down
    ax.annotate('', xy=(7, y_pos-0.7), xytext=(7, y_pos-0.4), 
                arrowprops=dict(arrowstyle='->', lw=2, color='black'))
    
    # ===== TOKENIZATION =====
    y_pos = 13
    
    tokenize_box = FancyBboxPatch((2, y_pos-0.3), 10, 0.6, 
                                 boxstyle="round,pad=0.05", 
                                 facecolor=colors['embedding'], alpha=0.9)
    ax.add_patch(tokenize_box)
    ax.text(7, y_pos, 'TOKENIZATION', fontweight='bold', ha='center', fontsize=12)
    ax.text(7, y_pos-0.15, 'Vocabulary: 256,000 tokens | Max Length: 8,192 tokens', 
            ha='center', fontsize=9)
    
    # Token sequence visualization
    token_y = y_pos - 0.8
    tokens = ['[CLS]', 'Chess', 'Player', 'Analysis', ':', 'thibault', '...', '[SEP]']
    token_width = 1.2
    start_x = 7 - (len(tokens) * token_width) / 2
    
    for i, token in enumerate(tokens):
        token_box = Rectangle((start_x + i * token_width, token_y - 0.2), 
                             token_width - 0.1, 0.4, 
                             facecolor='white', edgecolor='gray')
        ax.add_patch(token_box)
        ax.text(start_x + i * token_width + token_width/2, token_y, token, 
                ha='center', va='center', fontsize=8)
    
    ax.text(7, token_y - 0.5, 'Token Sequence: Input IDs [101, 15284, 7084, ...]', 
            ha='center', fontsize=9, style='italic')
    
    # Arrow down
    ax.annotate('', xy=(7, y_pos-1.3), xytext=(7, y_pos-1.0), 
                arrowprops=dict(arrowstyle='->', lw=2, color='black'))
    
    # ===== INPUT EMBEDDINGS =====
    y_pos = 11.5
    
    embed_box = FancyBboxPatch((1.5, y_pos-0.4), 11, 0.8, 
                              boxstyle="round,pad=0.05", 
                              facecolor=colors['embedding'], alpha=0.9)
    ax.add_patch(embed_box)
    ax.text(7, y_pos+0.1, 'INPUT EMBEDDINGS', fontweight='bold', ha='center', fontsize=12)
    ax.text(7, y_pos-0.1, 'Token Embeddings + Position Embeddings', 
            ha='center', fontsize=10)
    ax.text(7, y_pos-0.25, 'Dimension: [sequence_length, 2048]', 
            ha='center', fontsize=9, style='italic')
    
    # Embedding matrix visualization
    embed_matrix = Rectangle((3, y_pos-0.8), 8, 0.3, 
                           facecolor='#FFF8DC', edgecolor='black', alpha=0.7)
    ax.add_patch(embed_matrix)
    ax.text(7, y_pos-0.65, 'Embedding Matrix: [vocab_size=256k, hidden_size=2048]', 
            ha='center', fontsize=9)
    
    # Arrow down
    ax.annotate('', xy=(7, y_pos-1.2), xytext=(7, y_pos-0.9), 
                arrowprops=dict(arrowstyle='->', lw=2, color='black'))
    
    # ===== TRANSFORMER LAYERS =====
    y_start = 10
    layer_height = 0.4
    layer_spacing = 0.1
    
    ax.text(7, y_start + 0.3, 'TRANSFORMER DECODER LAYERS (18 Layers)', 
            fontweight='bold', ha='center', fontsize=12)
    
    # Show 3 representative layers
    layer_labels = ['Layer 1', 'Layer 9', 'Layer 18']
    for i, label in enumerate(layer_labels):
        y_layer = y_start - i * 2.5
        
        # Layer container
        layer_container = FancyBboxPatch((0.5, y_layer-2.2), 13, 2.1, 
                                        boxstyle="round,pad=0.05", 
                                        facecolor='white', alpha=0.3,
                                        edgecolor='blue', linewidth=1.5)
        ax.add_patch(layer_container)
        
        ax.text(1, y_layer-0.1, label, fontweight='bold', fontsize=11, color='blue')
        
        # Multi-Head Self-Attention
        attn_box = FancyBboxPatch((1.5, y_layer-0.8), 4, 0.6, 
                                 boxstyle="round,pad=0.03", 
                                 facecolor=colors['attention'], alpha=0.9)
        ax.add_patch(attn_box)
        ax.text(3.5, y_layer-0.5, 'Multi-Head Self-Attention', 
                fontweight='bold', ha='center', fontsize=10)
        ax.text(3.5, y_layer-0.65, '8 Heads | Head Dim: 256', 
                ha='center', fontsize=8)
        
        # Add & Norm 1
        norm1_box = FancyBboxPatch((6, y_layer-0.8), 2, 0.6, 
                                  boxstyle="round,pad=0.03", 
                                  facecolor=colors['normalization'], alpha=0.9)
        ax.add_patch(norm1_box)
        ax.text(7, y_layer-0.5, 'Add & Norm', 
                fontweight='bold', ha='center', fontsize=9)
        
        # Feed Forward Network
        ffn_box = FancyBboxPatch((1.5, y_layer-1.6), 4, 0.6, 
                                boxstyle="round,pad=0.03", 
                                facecolor=colors['feedforward'], alpha=0.9)
        ax.add_patch(ffn_box)
        ax.text(3.5, y_layer-1.3, 'Feed Forward Network', 
                fontweight='bold', ha='center', fontsize=10)
        ax.text(3.5, y_layer-1.45, 'Hidden: 5504 | Activation: GELU', 
                ha='center', fontsize=8)
        
        # Add & Norm 2
        norm2_box = FancyBboxPatch((6, y_layer-1.6), 2, 0.6, 
                                  boxstyle="round,pad=0.03", 
                                  facecolor=colors['normalization'], alpha=0.9)
        ax.add_patch(norm2_box)
        ax.text(7, y_layer-1.3, 'Add & Norm', 
                fontweight='bold', ha='center', fontsize=9)
        
        # Dimensions box
        dim_box = FancyBboxPatch((8.5, y_layer-1.6), 4.5, 1.4, 
                                boxstyle="round,pad=0.03", 
                                facecolor=colors['parameters'], alpha=0.9)
        ax.add_patch(dim_box)
        ax.text(10.75, y_layer-0.5, 'DIMENSIONS', 
                fontweight='bold', ha='center', fontsize=10)
        ax.text(10.75, y_layer-0.8, f'Input: [batch, seq, 2048]\nQ,K,V: [batch, seq, 2048]\nOutput: [batch, seq, 2048]\nFFN Hidden: [batch, seq, 5504]', 
                ha='center', fontsize=8, va='center')
        
        # Internal arrows
        if i == 0:  # Only show arrows for first layer to avoid clutter
            # Attention flow
            ax.annotate('', xy=(6, y_layer-0.5), xytext=(5.5, y_layer-0.5), 
                       arrowprops=dict(arrowstyle='->', lw=1.5, color='blue'))
            # FFN flow  
            ax.annotate('', xy=(6, y_layer-1.3), xytext=(5.5, y_layer-1.3), 
                       arrowprops=dict(arrowstyle='->', lw=1.5, color='green'))
            # Between layers
            ax.annotate('', xy=(3.5, y_layer-1.7), xytext=(3.5, y_layer-0.9), 
                       arrowprops=dict(arrowstyle='->', lw=1.5, color='red'))
        
        # Layer output arrow
        if i < len(layer_labels) - 1:
            ax.annotate('', xy=(7, y_layer-2.4), xytext=(7, y_layer-2.1), 
                       arrowprops=dict(arrowstyle='->', lw=2, color='black'))
    
    # ===== OUTPUT HEAD =====
    y_pos = 2.5
    
    output_box = FancyBboxPatch((1.5, y_pos-0.4), 11, 0.8, 
                               boxstyle="round,pad=0.05", 
                               facecolor=colors['output'], alpha=0.9)
    ax.add_patch(output_box)
    ax.text(7, y_pos+0.1, 'OUTPUT HEAD', fontweight='bold', ha='center', fontsize=12)
    ax.text(7, y_pos-0.1, 'Linear Layer: [2048] → [256,000]', 
            ha='center', fontsize=10)
    ax.text(7, y_pos-0.25, 'Softmax → Token Probabilities', 
            ha='center', fontsize=9, style='italic')
    
    # Arrow down
    ax.annotate('', xy=(7, y_pos-0.7), xytext=(7, y_pos-0.4), 
                arrowprops=dict(arrowstyle='->', lw=2, color='black'))
    
    # ===== OUTPUT =====
    y_pos = 1.5
    
    output_text_box = FancyBboxPatch((1, y_pos-0.3), 12, 0.6, 
                                    boxstyle="round,pad=0.05", 
                                    facecolor=colors['data_flow'], alpha=0.9,
                                    edgecolor='black', linewidth=1)
    ax.add_patch(output_text_box)
    ax.text(7, y_pos, 'OUTPUT: "Strategic Recommendations: Target ECO C30 opening..."', 
            fontweight='bold', ha='center', fontsize=11)
    
    # ===== MODEL SPECIFICATIONS =====
    spec_box = FancyBboxPatch((0.2, 3.5), 3.5, 6, 
                             boxstyle="round,pad=0.05", 
                             facecolor='#F5F5F5', alpha=0.95,
                             edgecolor='black', linewidth=1.5)
    ax.add_patch(spec_box)
    
    ax.text(2, 9.2, 'MODEL SPECIFICATIONS', 
            fontweight='bold', ha='center', fontsize=12, color='black')
    
    specs_text = """
📊 ARCHITECTURE:
• Type: Transformer Decoder
• Layers: 18
• Parameters: 2.6 Billion
• Hidden Size: 2048
• Intermediate Size: 5504

🧠 ATTENTION:
• Heads: 8 per layer
• Head Dimension: 256
• Max Position: 8192

🔧 TRAINING:
• Pre-training: General text
• Fine-tuning: Chess strategy
• Examples: 63 chess patterns
• Context Window: 8K tokens

⚡ INFERENCE:
• Precision: FP16
• Temperature: 0.7
• Max New Tokens: 512
• Beam Search: 1

💾 STORAGE:
• Model Size: ~5.2 GB
• Quantized: ~2.6 GB
• Checkpoint: PyTorch/Safetensors
"""
    
    ax.text(2, 8.8, specs_text, ha='center', va='top', fontsize=8,
           linespacing=1.2)
    
    # ===== ATTENTION MECHANISM DETAIL =====
    attn_detail_box = FancyBboxPatch((10.5, 6), 3.3, 3.5, 
                                    boxstyle="round,pad=0.05", 
                                    facecolor='#E6E6FA', alpha=0.95,
                                    edgecolor='blue', linewidth=1.5)
    ax.add_patch(attn_detail_box)
    
    ax.text(12.15, 9.3, 'ATTENTION DETAIL', 
            fontweight='bold', ha='center', fontsize=11, color='blue')
    
    attn_text = """
Q = XW_Q  [seq, 2048]
K = XW_K  [seq, 2048]  
V = XW_V  [seq, 2048]

Attention(Q,K,V) = 
    softmax(QK^T/√d_k)V

Multi-Head:
• Heads: 8
• d_k = d_v = 256
• Concat all heads
• Linear projection

Self-Attention Matrix:
[seq × seq] attention weights
showing token relationships
"""
    
    ax.text(12.15, 8.9, attn_text, ha='center', va='top', fontsize=8,
           linespacing=1.1, family='monospace')
    
    plt.tight_layout()
    return fig

def main():
    """Generate and save the detailed model architecture diagram"""
    print("🎨 Generating Detailed Gemma2 Model Architecture Diagram...")
    
    # Create the diagram
    fig = create_detailed_model_diagram()
    
    # Save the diagram
    output_file = 'Gemma2_Model_Architecture_Detailed.png'
    fig.savefig(output_file, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    
    print(f"✅ Detailed model architecture diagram saved as: {output_file}")
    print(f"📐 Diagram dimensions: 14x16 inches at 300 DPI")
    print(f"🎯 Shows detailed Gemma2:2B architecture including:")
    print(f"   • Complete transformer layer structure")
    print(f"   • Attention mechanism details")
    print(f"   • Dimension transformations")
    print(f"   • Model specifications")
    print(f"   • Data flow through all layers")

if __name__ == "__main__":
    main()
