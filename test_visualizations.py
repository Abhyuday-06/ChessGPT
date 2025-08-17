"""
Test script for chess analysis visualizations
Run this to verify all visualization functions work properly
"""

import sys
import os
from collections import defaultdict
import random

# Mock data for testing
def create_mock_data():
    """Create mock data for testing visualizations"""
    
    # Mock player stats
    player_stats = {
        'as_white': defaultdict(list),
        'as_black': defaultdict(list),
        'total_games': 50,
        'wins': 25,
        'losses': 20,
        'draws': 5
    }
    
    # Add some mock opening data
    eco_codes = ['B01', 'C55', 'E90', 'D35', 'B22', 'A10']
    opening_names = ['Scandinavian Defense', 'Italian Game', 'King\'s Indian Defense', 
                    'Queen\'s Gambit Declined', 'Sicilian Alapin', 'English Opening']
    
    for i, (eco, opening) in enumerate(zip(eco_codes, opening_names)):
        # Create mock games for each opening
        for color in ['as_white', 'as_black']:
            num_games = random.randint(3, 8)
            for j in range(num_games):
                result = random.choice(['win', 'loss', 'draw'])
                player_stats[color][eco].append({
                    'result': result,
                    'opening': opening,
                    'opponent': f'opponent_{j}'
                })
    
    # Mock weakness report
    weakness_report = {
        'opening_weaknesses': [
            {
                'eco': 'B01',
                'opening': 'Scandinavian Defense',
                'color': 'as_black',
                'win_rate': 35.0,
                'total_games': 6,
                'wins': 2,
                'losses': 4,
                'draws': 0,
                'weakness_score': 75.0
            },
            {
                'eco': 'C55',
                'opening': 'Italian Game',
                'color': 'as_black',
                'win_rate': 42.0,
                'total_games': 5,
                'wins': 2,
                'losses': 3,
                'draws': 0,
                'weakness_score': 68.0
            }
        ],
        'tactical_patterns': {
            'quick_losses': [
                {'eco': 'B01', 'opening': 'Scandinavian Defense', 'moves': 22}
            ]
        },
        'experience_gaps': {
            'inexperienced': [
                {'eco': 'E90', 'opening': 'King\'s Indian Defense', 'color': 'as_black', 'games': 2}
            ]
        }
    }
    
    # Mock tactical analysis
    tactical_analysis = {
        'total_analyzed': 30,
        'blunder_count': 8,
        'mistake_count': 15,
        'inaccuracy_count': 12,
        'avg_centipawn_loss': 35.5,
        'opening_errors': {
            'B01': {'blunders': 3, 'mistakes': 2, 'inaccuracies': 1, 'games': 4},
            'C55': {'blunders': 2, 'mistakes': 4, 'inaccuracies': 3, 'games': 5},
            'E90': {'blunders': 1, 'mistakes': 3, 'inaccuracies': 2, 'games': 3}
        }
    }
    
    return player_stats, weakness_report, tactical_analysis

def test_visualizations():
    """Test all visualization functions"""
    
    print("🧪 Testing Chess Analysis Visualizations")
    print("=" * 50)
    
    try:
        # Import visualization modules
        from visualization_generator import generate_all_visualizations
        
        # Create mock data
        player_stats, weakness_report, tactical_analysis = create_mock_data()
        all_games = []  # Mock empty games list
        target_username = "TestPlayer"
        
        print("📊 Testing standard visualizations...")
        generate_all_visualizations(all_games, player_stats, weakness_report, tactical_analysis, target_username)
        
        print("\n✅ ALL TESTS PASSED!")
        print("Check the 'visualizations' folder for generated test charts")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required packages are installed:")
        print("pip install -r visualization_requirements.txt")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_visualizations()
