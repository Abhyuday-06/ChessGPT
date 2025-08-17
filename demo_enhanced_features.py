#!/usr/bin/env python3
"""
Demonstration of the enhanced PGN and analysis link functionality
"""

import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_pgn_generation():
    """Demonstrate the new PGN and analysis link generation"""
    
    # Import the functions from the enhanced chess analyzer
    from chess_analyzer_complete import generate_opening_pgn_and_links, create_analysis_links, enhance_opening_recommendations
    
    print("🎯 DEMO: Enhanced Chess Strategy Recommendations with PGN & Analysis Links")
    print("=" * 80)
    
    # Example opening recommendations (similar to what the analyzer generates)
    sample_recommendations = [
        {
            'target_opening': 'Sicilian Defense',
            'opponent_color': 'black',
            'exploitation_method': 'Force opponent into uncomfortable defensive positions',
            'specific_lines': [
                'Play Sicilian Dragon variation for sharp tactical play',
                'Consider Sicilian Najdorf for complex middlegame positions',
                'Choose sharp attacking variations like Yugoslav Attack'
            ],
            'reasoning': 'Opponent has only 35.2% win rate as Black in this opening'
        }
    ]
    
    print("\n1️⃣ ORIGINAL RECOMMENDATION FORMAT:")
    print(f"   Target: {sample_recommendations[0]['target_opening']}")
    print(f"   Strategy: {sample_recommendations[0]['exploitation_method']}")
    print(f"   Lines: {', '.join(sample_recommendations[0]['specific_lines'])}")
    
    # Enhance the recommendations with PGN and links
    enhanced = enhance_opening_recommendations(sample_recommendations)
    
    print(f"\n2️⃣ ENHANCED RECOMMENDATION FORMAT:")
    rec = enhanced[0]
    print(f"   Target: {rec['target_opening']}")
    print(f"   Strategy: {rec['exploitation_method']}")
    print(f"   Enhanced Lines:")
    
    for i, line in enumerate(rec['specific_lines'], 1):
        print(f"\n   {i}. {line['description']}")
        print(f"      PGN: {line['pgn']}")
        print(f"      🔗 Lichess Analysis: {line['analysis_links']['lichess_analysis']}")
        print(f"      🔗 Chess.com Analysis: {line['analysis_links']['chesscom_analysis']}")
    
    print(f"\n3️⃣ BENEFITS OF ENHANCEMENT:")
    print("   ✅ Complete PGN notation for each recommended line")
    print("   ✅ Direct links to interactive analysis boards")
    print("   ✅ Immediate access to study materials")
    print("   ✅ Click-to-analyze functionality")
    print("   ✅ Master the recommended openings faster")
    
    print(f"\n4️⃣ SAMPLE PGN GENERATION:")
    
    test_openings = ['Sicilian Dragon', 'French Defense', 'Caro-Kann Defense', 'English Opening']
    
    for opening in test_openings:
        pgn = generate_opening_pgn_and_links(opening)
        links = create_analysis_links(pgn, opening)
        print(f"\n   {opening}:")
        print(f"   PGN: {pgn}")
        print(f"   Lichess: {links['lichess_analysis']}")
    
    print(f"\n🎉 DEMO COMPLETE!")
    print("The enhanced chess analyzer now provides actionable, clickable recommendations!")

if __name__ == "__main__":
    demo_pgn_generation()
