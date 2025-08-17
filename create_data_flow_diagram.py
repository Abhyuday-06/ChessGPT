#!/usr/bin/env python3
"""
ChessGPT Data Flow and Format Diagram
Creates a diagram showing data transformations and formats at each stage
"""

import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np

# Configure matplotlib for high-quality output
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 9
plt.rcParams['font.family'] = 'Arial'

def create_data_flow_diagram():
    """Create data flow diagram showing formats and dimensions"""
    
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(16, 10))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Colors for different data types
    colors = {
        'raw_data': '#FFE5CC',      # Light Orange
        'structured': '#CCE5FF',    # Light Blue  
        'numerical': '#E5CCFF',     # Light Purple
        'embeddings': '#CCFFE5',    # Light Green
        'predictions': '#FFCCCC',   # Light Red
        'output': '#FFFFCC'         # Light Yellow
    }
    
    # Title
    ax.text(8, 9.5, 'ChessGPT: Data Flow and Format Transformations', 
            fontsize=16, fontweight='bold', ha='center')
    ax.text(8, 9.1, 'From Raw Player Data to Strategic Recommendations', 
            fontsize=12, ha='center', style='italic')
    
    # Define stages with their data formats
    stages = [
        {
            'title': 'RAW INPUT',
            'position': (1, 8),
            'width': 2.5,
            'height': 1.2,
            'color': colors['raw_data'],
            'data_format': 'String',
            'example': '"thibault"',
            'dimensions': 'N/A',
            'description': 'Player username\nfrom user input'
        },
        {
            'title': 'PGN DATA',
            'position': (4.5, 8),
            'width': 2.5,
            'height': 1.2,
            'color': colors['raw_data'],
            'data_format': 'Text File',
            'example': '[Event "Rated game"]\n1.e4 e5 2.Nf3...',
            'dimensions': '~50 games\n~500KB',
            'description': 'Chess games in\nPortable Game Notation'
        },
        {
            'title': 'PARSED GAMES',
            'position': (8, 8),
            'width': 2.5,
            'height': 1.2,
            'color': colors['structured'],
            'data_format': 'List[Game]',
            'example': '[Game1, Game2, ...]',
            'dimensions': 'len=50',
            'description': 'Python chess.Game\nobjects with metadata'
        },
        {
            'title': 'GAME ANALYSIS',
            'position': (11.5, 8),
            'width': 2.5,
            'height': 1.2,
            'color': colors['structured'],
            'data_format': 'Dict',
            'example': '{"wins": 27, "losses": 21}',
            'dimensions': '~200 fields',
            'description': 'Statistical analysis\nresults per opening'
        },
        {
            'title': 'ENGINE EVALUATION',
            'position': (1, 6),
            'width': 2.5,
            'height': 1.2,
            'color': colors['numerical'],
            'data_format': 'Float Arrays',
            'example': '[+0.3, -1.2, +0.8, ...]',
            'dimensions': '20 evals/game\n1000 total',
            'description': 'Stockfish centipawn\neval per position'
        },
        {
            'title': 'WEAKNESS REPORT',
            'position': (4.5, 6),
            'width': 2.5,
            'height': 1.2,
            'color': colors['structured'],
            'data_format': 'JSON',
            'example': '{"opening_weaknesses": [...]}',
            'dimensions': '~50 weakness\nentries',
            'description': 'Structured weakness\nanalysis with scores'
        },
        {
            'title': 'TRAINING INPUT',
            'position': (8, 6),
            'width': 2.5,
            'height': 1.2,
            'color': colors['structured'],
            'data_format': 'String',
            'example': '"Opponent: ECO C30 50% win rate"',
            'dimensions': '~512 chars\navg length',
            'description': 'Formatted prompt\nfor LLM input'
        },
        {
            'title': 'TOKENIZED INPUT',
            'position': (11.5, 6),
            'width': 2.5,
            'height': 1.2,
            'color': colors['numerical'],
            'data_format': 'Int Array',
            'example': '[101, 15284, 7084, ...]',
            'dimensions': 'max_len=512\nvocab=256k',
            'description': 'Token IDs from\nGemma2 tokenizer'
        },
        {
            'title': 'EMBEDDINGS',
            'position': (1, 4),
            'width': 2.5,
            'height': 1.2,
            'color': colors['embeddings'],
            'data_format': 'Tensor',
            'example': 'torch.FloatTensor',
            'dimensions': '[batch=1, seq=512,\nhidden=2048]',
            'description': 'Dense vector\nrepresentation'
        },
        {
            'title': 'ATTENTION',
            'position': (4.5, 4),
            'width': 2.5,
            'height': 1.2,
            'color': colors['embeddings'],
            'data_format': 'Tensor',
            'example': 'attention_weights',
            'dimensions': '[batch=1, heads=8,\nseq=512, seq=512]',
            'description': 'Multi-head attention\nweights matrix'
        },
        {
            'title': 'HIDDEN STATES',
            'position': (8, 4),
            'width': 2.5,
            'height': 1.2,  
            'color': colors['embeddings'],
            'data_format': 'Tensor',
            'example': 'hidden_states',
            'dimensions': '[batch=1, seq=512,\nhidden=2048]',
            'description': 'Transformer layer\noutput activations'
        },
        {
            'title': 'LOGITS',
            'position': (11.5, 4),
            'width': 2.5,
            'height': 1.2,
            'color': colors['predictions'],
            'data_format': 'Tensor',
            'example': 'model_logits',
            'dimensions': '[batch=1, seq=512,\nvocab=256k]',
            'description': 'Raw prediction\nscores per token'
        },
        {
            'title': 'PROBABILITIES',
            'position': (1, 2),
            'width': 2.5,
            'height': 1.2,
            'color': colors['predictions'],
            'data_format': 'Tensor',
            'example': 'softmax(logits)',
            'dimensions': '[batch=1, seq=512,\nvocab=256k]',
            'description': 'Token probability\ndistribution'
        },
        {
            'title': 'GENERATED TOKENS',
            'position': (4.5, 2),
            'width': 2.5,
            'height': 1.2,
            'color': colors['predictions'],
            'data_format': 'Int Array',
            'example': '[25235, 1402, 15284, ...]',
            'dimensions': 'max_new=512\ntokens',
            'description': 'Selected token IDs\nvia sampling/greedy'
        },
        {
            'title': 'DECODED TEXT',
            'position': (8, 2),
            'width': 2.5,
            'height': 1.2,
            'color': colors['output'],
            'data_format': 'String',
            'example': '"Target ECO C30 opening..."',
            'dimensions': '~300 words\navg response',
            'description': 'Human-readable\nstrategy text'
        },
        {
            'title': 'FINAL OUTPUT',
            'position': (11.5, 2),
            'width': 2.5,
            'height': 1.2,
            'color': colors['output'],
            'data_format': 'JSON/HTML',
            'example': '{"strategy": "...", "pgn": "..."}',
            'dimensions': '~2KB\nstructured',
            'description': 'Formatted response\nwith PGN links'
        }
    ]
    
    # Draw all stages
    for stage in stages:
        x, y = stage['position']
        w, h = stage['width'], stage['height']
        
        # Main box
        box = FancyBboxPatch((x-w/2, y-h/2), w, h, 
                            boxstyle="round,pad=0.05", 
                            facecolor=stage['color'], alpha=0.9,
                            edgecolor='black', linewidth=1)
        ax.add_patch(box)
        
        # Title
        ax.text(x, y+h/2-0.15, stage['title'], 
                fontweight='bold', ha='center', fontsize=10)
        
        # Data format
        ax.text(x, y+0.1, f"Format: {stage['data_format']}", 
                ha='center', fontsize=8, style='italic')
        
        # Dimensions
        ax.text(x, y-0.1, f"Dims: {stage['dimensions']}", 
                ha='center', fontsize=8, color='blue')
        
        # Description
        ax.text(x, y-h/2+0.15, stage['description'], 
                ha='center', fontsize=7, va='top')
    
    # Draw flow arrows
    arrow_props = dict(arrowstyle='->', lw=2, color='#333333')
    
    # Top row arrows
    ax.annotate('', xy=(3.7, 8), xytext=(2.3, 8), arrowprops=arrow_props)
    ax.annotate('', xy=(7.2, 8), xytext=(5.8, 8), arrowprops=arrow_props)
    ax.annotate('', xy=(10.7, 8), xytext=(9.3, 8), arrowprops=arrow_props)
    
    # Vertical down from parsed games
    ax.annotate('', xy=(8, 6.8), xytext=(8, 7.2), arrowprops=arrow_props)
    
    # Second row arrows  
    ax.annotate('', xy=(3.7, 6), xytext=(2.3, 6), arrowprops=arrow_props)
    ax.annotate('', xy=(7.2, 6), xytext=(5.8, 6), arrowprops=arrow_props)
    ax.annotate('', xy=(10.7, 6), xytext=(9.3, 6), arrowprops=arrow_props)
    
    # From analysis to engine evaluation
    ax.annotate('', xy=(2.2, 6.8), xytext=(11, 7.2), 
                arrowprops=dict(arrowstyle='->', lw=2, color='red',
                              connectionstyle="arc3,rad=-0.3"))
    
    # Vertical down from tokenized input
    ax.annotate('', xy=(11.5, 4.8), xytext=(11.5, 5.2), arrowprops=arrow_props)
    
    # To embeddings
    ax.annotate('', xy=(2.2, 4.8), xytext=(10.8, 5.2), 
                arrowprops=dict(arrowstyle='->', lw=2, color='green',
                              connectionstyle="arc3,rad=-0.4"))
    
    # Third row arrows
    ax.annotate('', xy=(3.7, 4), xytext=(2.3, 4), arrowprops=arrow_props)
    ax.annotate('', xy=(7.2, 4), xytext=(5.8, 4), arrowprops=arrow_props)
    ax.annotate('', xy=(10.7, 4), xytext=(9.3, 4), arrowprops=arrow_props)
    
    # Vertical down from logits
    ax.annotate('', xy=(11.5, 2.8), xytext=(11.5, 3.2), arrowprops=arrow_props)
    
    # To probabilities
    ax.annotate('', xy=(2.2, 2.8), xytext=(10.8, 3.2), 
                arrowprops=dict(arrowstyle='->', lw=2, color='purple',
                              connectionstyle="arc3,rad=-0.5"))
    
    # Bottom row arrows
    ax.annotate('', xy=(3.7, 2), xytext=(2.3, 2), arrowprops=arrow_props)
    ax.annotate('', xy=(7.2, 2), xytext=(5.8, 2), arrowprops=arrow_props)
    ax.annotate('', xy=(10.7, 2), xytext=(9.3, 2), arrowprops=arrow_props)
    
    # Add processing stage labels
    stage_labels = [
        ('DATA COLLECTION', 2.75, 8.8),
        ('ANALYSIS PIPELINE', 8, 8.8),
        ('ENGINE PROCESSING', 2.75, 6.8),
        ('LLM PREPROCESSING', 8, 6.8),
        ('MODEL INFERENCE', 6.25, 4.8),
        ('OUTPUT GENERATION', 6.25, 2.8)
    ]
    
    for label, x, y in stage_labels:
        ax.text(x, y, label, fontweight='bold', ha='center', fontsize=11,
               bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
    
    # Performance metrics box
    perf_box = FancyBboxPatch((13.5, 0.2), 2.3, 3.5, 
                             boxstyle="round,pad=0.05", 
                             facecolor='#F0F8FF', alpha=0.95,
                             edgecolor='blue', linewidth=1.5)
    ax.add_patch(perf_box)
    
    ax.text(14.65, 3.5, 'PERFORMANCE', fontweight='bold', ha='center', fontsize=11, color='blue')
    
    perf_text = """
Data Processing:
• PGN Parse: ~0.5s
• Engine Analysis: ~90s
• Weakness Detection: ~5s

Model Inference:
• Tokenization: ~0.1s
• Forward Pass: ~2s
• Decoding: ~1s
• Total Response: ~3s

Memory Usage:
• Model: ~5.2GB
• Inference: ~2GB
• Peak: ~7.5GB

Throughput:
• ~20 tokens/sec
• ~1 strategy/3min
• Batch size: 1
"""
    
    ax.text(14.65, 3.2, perf_text, ha='center', va='top', fontsize=7)
    
    # Data size progression
    size_box = FancyBboxPatch((0.2, 0.2), 2.3, 3.5, 
                             boxstyle="round,pad=0.05", 
                             facecolor='#FFF8DC', alpha=0.95,
                             edgecolor='orange', linewidth=1.5)
    ax.add_patch(size_box)
    
    ax.text(1.35, 3.5, 'DATA SIZES', fontweight='bold', ha='center', fontsize=11, color='orange')
    
    size_text = """
Raw Input: ~20 chars
PGN Data: ~500KB
Parsed Games: ~2MB
Analysis Results: ~50KB
Weakness Report: ~25KB
Training Input: ~1KB
Token IDs: ~2KB
Embeddings: ~4MB
Hidden States: ~8MB
Logits: ~500MB
Probabilities: ~500MB
Generated: ~2KB
Output Text: ~1KB
Final JSON: ~2KB
"""
    
    ax.text(1.35, 3.2, size_text, ha='center', va='top', fontsize=7, family='monospace')
    
    plt.tight_layout()
    return fig

def main():
    """Generate and save the data flow diagram"""
    print("🎨 Generating ChessGPT Data Flow Diagram...")
    
    # Create the diagram
    fig = create_data_flow_diagram()
    
    # Save the diagram
    output_file = 'ChessGPT_Data_Flow_Diagram.png'
    fig.savefig(output_file, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    
    print(f"✅ Data flow diagram saved as: {output_file}")
    print(f"📐 Diagram dimensions: 16x10 inches at 300 DPI")
    print(f"🎯 Shows complete data transformation pipeline:")
    print(f"   • Data formats at each stage")
    print(f"   • Tensor dimensions and shapes")
    print(f"   • Processing times and memory usage")
    print(f"   • Flow between system components")

if __name__ == "__main__":
    main()
