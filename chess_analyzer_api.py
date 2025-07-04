#!/usr/bin/env python
"""
Chess Analyzer - Programmatic Version
Non-interactive version for web UI integration
"""

import requests
import json
import time
import chess
import chess.pgn
import chess.engine
import platform
import os
import io
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime


class ChessGameAnalyzer:
    def __init__(self):
        self.stockfish_path = self.get_stockfish_path()
        self.training_data_file = "chess_strategy_training_data.json"
        
    def get_stockfish_path(self):
        """Get the correct Stockfish path for the platform"""
        if platform.system() == "Windows":
            paths = [
                "stockfish/stockfish.exe",
                "stockfish/stockfish/stockfish-windows-x86-64-avx2.exe",
                "stockfish.exe"
            ]
        else:
            paths = [
                "stockfish/stockfish",
                "/usr/local/bin/stockfish",
                "/usr/bin/stockfish",
                "stockfish"
            ]
        
        for path in paths:
            if os.path.exists(path):
                return path
        
        # Return default and let chess.engine handle the error
        return "stockfish"
    
    def fetch_chess_com_games(self, username, max_games=50):
        """Fetch games from Chess.com API"""
        print(f"🔍 Fetching Chess.com games for {username}...")
        
        try:
            headers = {
                'User-Agent': 'ChessGPT/1.0 (Educational chess analysis tool)',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            
            time.sleep(1)  # Be respectful to the API
            
            response = requests.get(f"https://api.chess.com/pub/player/{username}/games/archives", headers=headers)
            response.raise_for_status()
            
            if response.text.strip() == "":
                print(f"❌ Empty response for user {username}")
                return []
            
            archives = response.json()
            print(f"📊 Found {len(archives['archives'])} archive months for {username}")
            
            all_games = []
            if archives["archives"]:
                # Try the last few months to find games
                for i in range(1, min(4, len(archives["archives"]) + 1)):
                    try:
                        archive_url = archives["archives"][-i]
                        print(f"📥 Fetching games from {archive_url}")
                        
                        time.sleep(1)  # Rate limiting
                        archive_response = requests.get(archive_url, headers=headers)
                        archive_response.raise_for_status()
                        
                        archive_data = archive_response.json()
                        games = archive_data.get("games", [])
                        print(f"📋 Found {len(games)} games in this archive")
                        
                        all_games.extend(games)
                        
                        if len(all_games) >= max_games:
                            break
                            
                    except Exception as e:
                        print(f"⚠️ Error fetching archive {i}: {e}")
                        continue
            
            # Limit to max_games
            if len(all_games) > max_games:
                all_games = all_games[-max_games:]
            
            print(f"✅ Successfully fetched {len(all_games)} games from Chess.com")
            return all_games
            
        except Exception as e:
            print(f"❌ Error fetching Chess.com games: {e}")
            return []
    
    def fetch_lichess_games(self, username, max_games=50):
        """Fetch games from Lichess API"""
        print(f"🔍 Fetching Lichess games for {username}...")
        
        try:
            headers = {
                'User-Agent': 'ChessGPT/1.0 (Educational chess analysis tool)',
                'Accept': 'application/x-ndjson'
            }
            
            # Lichess API endpoint for user games
            url = f"https://lichess.org/api/games/user/{username}"
            params = {
                'max': max_games,
                'rated': 'true',
                'perfType': 'blitz,rapid,classical',
                'format': 'json'
            }
            
            time.sleep(1)  # Be respectful to the API
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            games = []
            for line in response.text.strip().split('\n'):
                if line.strip():
                    try:
                        game = json.loads(line)
                        games.append(game)
                    except json.JSONDecodeError:
                        continue
            
            print(f"✅ Successfully fetched {len(games)} games from Lichess")
            return games
            
        except Exception as e:
            print(f"❌ Error fetching Lichess games: {e}")
            return []
    
    def analyze_game_with_stockfish(self, pgn_text, time_limit=1.0):
        """Analyze a single game with Stockfish"""
        try:
            with chess.engine.SimpleEngine.popen_uci(self.stockfish_path) as engine:
                game = chess.pgn.read_game(io.StringIO(pgn_text))
                if not game:
                    return None
                
                board = game.board()
                analysis = []
                
                for i, move in enumerate(game.mainline_moves()):
                    if i > 40:  # Limit analysis to first 40 moves
                        break
                    
                    # Get engine evaluation before the move
                    info = engine.analyse(board, chess.engine.Limit(time=time_limit))
                    score_before = info.get("score", chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE))
                    
                    board.push(move)
                    
                    # Get engine evaluation after the move
                    info = engine.analyse(board, chess.engine.Limit(time=time_limit))
                    score_after = info.get("score", chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE))
                    
                    analysis.append({
                        'move_number': i + 1,
                        'move': move.uci(),
                        'score_before': str(score_before),
                        'score_after': str(score_after)
                    })
                
                return analysis
                
        except Exception as e:
            print(f"⚠️ Error analyzing game: {e}")
            return None
    
    def identify_weaknesses(self, games_data, username):
        """Identify player weaknesses from analyzed games"""
        print("🔍 Identifying weaknesses...")
        
        weaknesses = []
        
        # Analyze game results
        total_games = len(games_data)
        if total_games == 0:
            return ["No games found for analysis"]
        
        losses = 0
        time_troubles = 0
        opening_issues = 0
        endgame_issues = 0
        
        for game in games_data:
            # Check game result
            if isinstance(game, dict):
                # Chess.com format
                if 'white' in game and 'black' in game:
                    if game['white']['username'].lower() == username.lower():
                        if game['white']['result'] == 'lose':
                            losses += 1
                    elif game['black']['username'].lower() == username.lower():
                        if game['black']['result'] == 'lose':
                            losses += 1
                
                # Lichess format
                elif 'players' in game:
                    player_color = None
                    if game['players']['white']['user']['name'].lower() == username.lower():
                        player_color = 'white'
                    elif game['players']['black']['user']['name'].lower() == username.lower():
                        player_color = 'black'
                    
                    if player_color and game['status'] == 'mate':
                        if game['winner'] != player_color:
                            losses += 1
        
        loss_rate = losses / total_games if total_games > 0 else 0
        
        # Generate weaknesses based on analysis
        if loss_rate > 0.6:
            weaknesses.append({
                "weakness_type": "High Loss Rate",
                "details": f"Loses {loss_rate:.1%} of games, indicating potential strategic or tactical issues"
            })
        
        if total_games < 20:
            weaknesses.append({
                "weakness_type": "Limited Game Sample",
                "details": f"Only {total_games} recent games available for analysis"
            })
        
        # Add some common weaknesses based on typical patterns
        weaknesses.extend([
            {
                "weakness_type": "Time Management",
                "details": "May struggle with time pressure in complex positions"
            },
            {
                "weakness_type": "Tactical Alertness",
                "details": "Occasional tactical oversights in critical moments"
            }
        ])
        
        return weaknesses
    
    def save_training_data(self, username, games_data, weaknesses):
        """Save analysis data to training file"""
        print("💾 Saving training data...")
        
        # Load existing data
        existing_data = []
        if os.path.exists(self.training_data_file):
            try:
                with open(self.training_data_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading existing data: {e}")
                existing_data = []
        
        # Create new training entry
        training_entry = {
            "input": {
                "opponent_profile": {
                    "player_name": username,
                    "total_games": len(games_data),
                    "platform": "auto-detected",
                    "analysis_date": datetime.now().isoformat(),
                    "weaknesses": weaknesses
                }
            },
            "output": {
                "strategy": f"Based on analysis of {username}'s games, focus on exploiting the identified weaknesses while maintaining solid positional play."
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to existing data
        existing_data.append(training_entry)
        
        # Save updated data
        try:
            with open(self.training_data_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Training data saved for {username}")
        except Exception as e:
            print(f"❌ Error saving training data: {e}")
    
    def analyze_player(self, username, platform="auto"):
        """Main analysis function"""
        print(f"🏛️ Starting analysis for {username} (platform: {platform})")
        
        games_data = []
        
        # Fetch games based on platform preference
        if platform.lower() in ["auto", "chess.com", "chesscom"]:
            chess_com_games = self.fetch_chess_com_games(username)
            games_data.extend(chess_com_games)
        
        if platform.lower() in ["auto", "lichess"] and len(games_data) < 20:
            lichess_games = self.fetch_lichess_games(username)
            games_data.extend(lichess_games)
        
        if not games_data:
            print(f"❌ No games found for {username}")
            return False
        
        print(f"📊 Total games collected: {len(games_data)}")
        
        # Identify weaknesses
        weaknesses = self.identify_weaknesses(games_data, username)
        
        print("🎯 Identified weaknesses:")
        for i, weakness in enumerate(weaknesses, 1):
            if isinstance(weakness, dict):
                print(f"   {i}. {weakness['weakness_type']}: {weakness['details']}")
            else:
                print(f"   {i}. {weakness}")
        
        # Save training data
        self.save_training_data(username, games_data, weaknesses)
        
        print(f"✅ Analysis completed for {username}")
        return True


def main():
    """Main function for command line usage"""
    if len(sys.argv) > 1:
        username = sys.argv[1]
        platform = sys.argv[2] if len(sys.argv) > 2 else "auto"
    else:
        username = input("Enter chess username: ").strip()
        platform = input("Enter platform (auto/chess.com/lichess) [auto]: ").strip() or "auto"
    
    if not username:
        print("❌ No username provided")
        return False
    
    analyzer = ChessGameAnalyzer()
    return analyzer.analyze_player(username, platform)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
