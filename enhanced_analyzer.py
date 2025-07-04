"""
Enhanced Chess Analyzer with Web Integration
Automatically fetches, analyzes, and trains on new players
"""

import json
import os
import subprocess
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
import threading

class ChessAnalyzer:
    """Wrapper for the chess analyzer script"""
    
    def analyze_player(self, username: str, platform: str = "auto") -> bool:
        """Analyze a player using the chess_analyzer.py script"""
        try:
            # Import the analyzer class
            from chess_analyzer import ChessGameAnalyzer
            
            analyzer = ChessGameAnalyzer()
            success = analyzer.analyze_player(username, platform)
            
            if success:
                print(f"✅ Analysis completed for {username}")
                return True
            else:
                print(f"❌ Analysis failed for {username}")
                return False
                
        except Exception as e:
            print(f"Error running chess analyzer: {e}")
            return False

class EnhancedChessAnalyzer:
    def __init__(self):
        self.analyzer = ChessAnalyzer()
        self.training_data_file = "chess_strategy_training_data.json"
        self.analysis_in_progress = set()
        self.analysis_results = {}
        
    def load_existing_data(self) -> Dict[str, Any]:
        """Load existing training data"""
        if os.path.exists(self.training_data_file):
            try:
                with open(self.training_data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading training data: {e}")
                return []
        return []
    
    def get_available_players(self) -> list:
        """Get list of already analyzed players"""
        try:
            data = self.load_existing_data()
            if not isinstance(data, list):
                return []
            
            players = set()
            for entry in data:
                if isinstance(entry, dict):
                    player_name = entry.get('input', {}).get('opponent_profile', {}).get('player_name', '')
                    if player_name:
                        players.add(player_name.lower())
            
            return sorted(list(players))
        except Exception as e:
            print(f"Error getting available players: {e}")
            return []
    
    def is_player_analyzed(self, username: str) -> bool:
        """Check if player is already analyzed"""
        return username.lower() in self.get_available_players()
    
    def is_analysis_in_progress(self, username: str) -> bool:
        """Check if analysis is currently in progress"""
        return username.lower() in self.analysis_in_progress
    
    def get_analysis_status(self, username: str) -> Dict[str, Any]:
        """Get current analysis status"""
        username_lower = username.lower()
        
        if self.is_player_analyzed(username_lower):
            return {
                'status': 'completed',
                'message': f'Analysis already available for {username}'
            }
        elif self.is_analysis_in_progress(username_lower):
            return {
                'status': 'in_progress',
                'message': f'Analysis in progress for {username}'
            }
        else:
            return {
                'status': 'not_started',
                'message': f'No analysis available for {username}'
            }
    
    def start_analysis(self, username: str, platform: str = "auto") -> Dict[str, Any]:
        """Start analysis for a new player"""
        username_lower = username.lower()
        
        if self.is_player_analyzed(username_lower):
            return {
                'success': False,
                'message': f'Player {username} already analyzed'
            }
        
        if self.is_analysis_in_progress(username_lower):
            return {
                'success': False,
                'message': f'Analysis already in progress for {username}'
            }
        
        # Start analysis in background thread
        self.analysis_in_progress.add(username_lower)
        thread = threading.Thread(
            target=self._analyze_player_background,
            args=(username, platform),
            daemon=True
        )
        thread.start()
        
        return {
            'success': True,
            'message': f'Started analysis for {username}'
        }
    
    def _analyze_player_background(self, username: str, platform: str = "auto"):
        """Background analysis function"""
        username_lower = username.lower()
        
        try:
            print(f"🔍 Starting analysis for {username} on {platform}")
            
            # Update status - Starting
            self.analysis_results[username_lower] = {
                'status': 'starting',
                'message': f'Starting analysis for {username}...',
                'progress': 5
            }
            
            # Update status - Downloading
            self.analysis_results[username_lower] = {
                'status': 'downloading',
                'message': f'Downloading games from {platform}...',
                'progress': 20
            }
            
            # Update status - Analyzing
            self.analysis_results[username_lower] = {
                'status': 'analyzing',
                'message': f'Analyzing games for weaknesses...',
                'progress': 60
            }
            
            # Try to analyze the player
            success = self.analyzer.analyze_player(username, platform)
            
            if success:
                self.analysis_results[username_lower] = {
                    'status': 'completed',
                    'message': f'Analysis completed for {username}',
                    'progress': 100
                }
                print(f"✅ Analysis completed for {username}")
            else:
                self.analysis_results[username_lower] = {
                    'status': 'failed',
                    'message': f'Analysis failed for {username}. Please check username and platform.',
                    'progress': 0
                }
                print(f"❌ Analysis failed for {username}")
                
        except Exception as e:
            self.analysis_results[username_lower] = {
                'status': 'failed',
                'message': f'Error analyzing {username}: {str(e)}',
                'progress': 0
            }
            print(f"❌ Error analyzing {username}: {e}")
        
        finally:
            # Remove from in-progress set
            self.analysis_in_progress.discard(username_lower)
    
    def get_progress(self, username: str) -> Dict[str, Any]:
        """Get analysis progress"""
        username_lower = username.lower()
        
        if username_lower in self.analysis_results:
            return self.analysis_results[username_lower]
        elif self.is_analysis_in_progress(username_lower):
            return {
                'status': 'in_progress',
                'message': f'Analysis in progress for {username}',
                'progress': 50
            }
        elif self.is_player_analyzed(username_lower):
            return {
                'status': 'completed',
                'message': f'Analysis completed for {username}',
                'progress': 100
            }
        else:
            return {
                'status': 'not_started',
                'message': f'No analysis for {username}',
                'progress': 0
            }
    
    def get_player_data(self, username: str) -> Optional[Dict[str, Any]]:
        """Get analysis data for a player"""
        data = self.load_existing_data()
        if not isinstance(data, list):
            return None
        
        for entry in data:
            if isinstance(entry, dict):
                player_name = entry.get('input', {}).get('opponent_profile', {}).get('player_name', '')
                if player_name.lower() == username.lower():
                    return entry
        
        return None

# Global analyzer instance
enhanced_analyzer = EnhancedChessAnalyzer()

class EnhancedChessAnalyzer:
    def __init__(self):
        self.analyzer = ChessAnalyzer()
        self.training_data_file = "chess_strategy_training_data.json"
        self.analysis_in_progress = set()
        self.analysis_results = {}
        
    def load_existing_data(self) -> Dict[str, Any]:
        """Load existing training data"""
        if os.path.exists(self.training_data_file):
            try:
                with open(self.training_data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading training data: {e}")
                return []
        return []
    
    def get_available_players(self) -> list:
        """Get list of already analyzed players"""
        try:
            data = self.load_existing_data()
            if not isinstance(data, list):
                return []
            
            players = set()
            for entry in data:
                if isinstance(entry, dict):
                    player_name = entry.get('input', {}).get('opponent_profile', {}).get('player_name', '')
                    if player_name:
                        players.add(player_name.lower())
            
            return sorted(list(players))
        except Exception as e:
            print(f"Error getting available players: {e}")
            return []
    
    def is_player_analyzed(self, username: str) -> bool:
        """Check if player is already analyzed"""
        return username.lower() in self.get_available_players()
    
    def is_analysis_in_progress(self, username: str) -> bool:
        """Check if analysis is currently in progress"""
        return username.lower() in self.analysis_in_progress
    
    def get_analysis_status(self, username: str) -> Dict[str, Any]:
        """Get current analysis status"""
        username_lower = username.lower()
        
        if self.is_player_analyzed(username_lower):
            return {
                'status': 'completed',
                'message': f'Analysis already available for {username}'
            }
        elif self.is_analysis_in_progress(username_lower):
            return {
                'status': 'in_progress',
                'message': f'Analysis in progress for {username}'
            }
        else:
            return {
                'status': 'not_started',
                'message': f'No analysis available for {username}'
            }
    
    def start_analysis(self, username: str, platform: str = "auto") -> Dict[str, Any]:
        """Start analysis for a new player"""
        username_lower = username.lower()
        
        if self.is_player_analyzed(username_lower):
            return {
                'success': False,
                'message': f'Player {username} already analyzed'
            }
        
        if self.is_analysis_in_progress(username_lower):
            return {
                'success': False,
                'message': f'Analysis already in progress for {username}'
            }
        
        # Start analysis in background thread
        self.analysis_in_progress.add(username_lower)
        thread = threading.Thread(
            target=self._analyze_player_background,
            args=(username, platform),
            daemon=True
        )
        thread.start()
        
        return {
            'success': True,
            'message': f'Started analysis for {username}'
        }
    
    def _analyze_player_background(self, username: str, platform: str = "auto"):
        """Background analysis function"""
        username_lower = username.lower()
        
        try:
            print(f"🔍 Starting analysis for {username} on {platform}")
            
            # Update status - Starting
            self.analysis_results[username_lower] = {
                'status': 'starting',
                'message': f'Starting analysis for {username}...',
                'progress': 5
            }
            
            # Update status - Downloading
            self.analysis_results[username_lower] = {
                'status': 'downloading',
                'message': f'Downloading games from {platform}...',
                'progress': 20
            }
            
            # Update status - Analyzing
            self.analysis_results[username_lower] = {
                'status': 'analyzing',
                'message': f'Analyzing games for weaknesses...',
                'progress': 60
            }
            
            # Try to analyze the player
            success = self.analyzer.analyze_player(username, platform)
            
            if success:
                self.analysis_results[username_lower] = {
                    'status': 'completed',
                    'message': f'Analysis completed for {username}',
                    'progress': 100
                }
                print(f"✅ Analysis completed for {username}")
            else:
                self.analysis_results[username_lower] = {
                    'status': 'failed',
                    'message': f'Analysis failed for {username}. Please check username and platform.',
                    'progress': 0
                }
                print(f"❌ Analysis failed for {username}")
                
        except Exception as e:
            self.analysis_results[username_lower] = {
                'status': 'failed',
                'message': f'Error analyzing {username}: {str(e)}',
                'progress': 0
            }
            print(f"❌ Error analyzing {username}: {e}")
        
        finally:
            # Remove from in-progress set
            self.analysis_in_progress.discard(username_lower)
    
    def get_progress(self, username: str) -> Dict[str, Any]:
        """Get analysis progress"""
        username_lower = username.lower()
        
        if username_lower in self.analysis_results:
            return self.analysis_results[username_lower]
        elif self.is_analysis_in_progress(username_lower):
            return {
                'status': 'in_progress',
                'message': f'Analysis in progress for {username}',
                'progress': 50
            }
        elif self.is_player_analyzed(username_lower):
            return {
                'status': 'completed',
                'message': f'Analysis completed for {username}',
                'progress': 100
            }
        else:
            return {
                'status': 'not_started',
                'message': f'No analysis for {username}',
                'progress': 0
            }
    
    def get_player_data(self, username: str) -> Optional[Dict[str, Any]]:
        """Get analysis data for a player"""
        data = self.load_existing_data()
        if not isinstance(data, list):
            return None
        
        for entry in data:
            if isinstance(entry, dict):
                player_name = entry.get('input', {}).get('opponent_profile', {}).get('player_name', '')
                if player_name.lower() == username.lower():
                    return entry
        
        return None

# Global analyzer instance
enhanced_analyzer = EnhancedChessAnalyzer()
