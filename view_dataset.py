#!/usr/bin/env python3
"""
Simple script to view training dataset statistics without running full analysis
"""

import json
import os

def display_dataset_statistics(filename="chess_strategy_training_data.json"):
    """Display statistics about the current training dataset"""
    
    try:
        if not os.path.exists(filename):
            print(f"⚠ No training dataset found at '{filename}'")
            return
        
        with open(filename, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        if not dataset:
            print("⚠ Training dataset is empty")
            return
        
        print(f"### Chess Strategy Training Dataset Statistics ###")
        print(f"Total training entries: {len(dataset)}")
        
        # Group by player
        players = {}
        for entry in dataset:
            player = entry.get('metadata', {}).get('player_analyzed', 'Unknown')
            if player not in players:
                players[player] = []
            players[player].append(entry)
        
        print(f"Players analyzed: {len(players)}")
        
        for player, entries in players.items():
            print(f"\n📊 {player}:")
            print(f"    - Training entries: {len(entries)}")
            
            # Count different analysis types
            analysis_types = {}
            for entry in entries:
                analysis_type = entry.get('metadata', {}).get('analysis_type', 'Unknown')
                analysis_types[analysis_type] = analysis_types.get(analysis_type, 0) + 1
            
            for analysis_type, count in analysis_types.items():
                type_name = analysis_type.replace('_', ' ').title()
                print(f"      • {type_name}: {count} entries")
            
            # Show latest analysis date
            latest_date = max([entry.get('metadata', {}).get('analysis_date', '') for entry in entries])
            print(f"      • Latest analysis: {latest_date}")
            
            # Count weaknesses and recommendations
            total_weaknesses = sum(len(entry['input']['opening_weaknesses']) for entry in entries)
            total_recommendations = sum(len(entry['output']['strategic_recommendations']['opening_choices']) for entry in entries)
            print(f"      • Total weaknesses identified: {total_weaknesses}")
            print(f"      • Total recommendations: {total_recommendations}")
            
            # Show sample weaknesses
            if entries:
                sample_entry = entries[0]
                if sample_entry['input']['opening_weaknesses']:
                    worst_opening = sample_entry['input']['opening_weaknesses'][0]
                    print(f"      • Example weakness: {worst_opening['opening']} ({worst_opening['win_rate']:.1f}% win rate)")
        
        print(f"\n🎯 Dataset ready for LLM training with {len(dataset)} diverse examples!")
        print(f"💡 To add more players, run: python chess_analyzer.py <username>")
        
    except Exception as e:
        print(f"✗ Error reading dataset statistics: {e}")

if __name__ == "__main__":
    display_dataset_statistics()
