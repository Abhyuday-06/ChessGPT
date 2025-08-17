#!/usr/bin/env python
"""
Chess Strategy AI - Complete Game Analyzer
Downloads games, analyzes weaknesses, creates training data, and generates strategies
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
        """Get the correct Stockfish path"""
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
                "/usr/bin/stockfish"
            ]
        
        for path in paths:
            if os.path.exists(path):
                return path
        return "stockfish"  # Default
    
    def get_user_input(self):
        """Get username and platform from user"""
        if len(sys.argv) > 1:
            username = sys.argv[1]
            platform = sys.argv[2] if len(sys.argv) > 2 else None
        else:
            username = input("Enter chess username: ").strip()
            print("\nSelect platform:")
            print("1. Chess.com")
            print("2. Lichess")
            print("3. Auto-detect (try both)")
            
            choice = input("Enter choice (1-3) [3]: ").strip()
            if choice == "1":
                platform = "chess.com"
            elif choice == "2":
                platform = "lichess"
            else:
                platform = "auto"
        
        return username, platform or "auto"
    
    def download_chess_com_games(self, username, max_games=50):
        """Download games from Chess.com"""
        print(f"🔍 Downloading Chess.com games for {username}...")
        
        try:
            headers = {
                'User-Agent': 'ChessGPT/1.0 (Educational chess analysis tool)',
                'Accept': 'application/json'
            }
            
            time.sleep(1)
            response = requests.get(f"https://api.chess.com/pub/player/{username}/games/archives", headers=headers)
            response.raise_for_status()
            
            if not response.text.strip():
                print(f"❌ No data found for {username}")
                return []
            
            archives = response.json()
            print(f"📊 Found {len(archives['archives'])} archive months")
            
            all_games = []
            if archives["archives"]:
                # Get recent games
                for i in range(1, min(4, len(archives["archives"]) + 1)):
                    try:
                        archive_url = archives["archives"][-i]
                        print(f"📥 Fetching {archive_url}")
                        
                        time.sleep(1)
                        archive_response = requests.get(archive_url, headers=headers)
                        archive_response.raise_for_status()
                        
                        games_data = archive_response.json()
                        all_games.extend(games_data["games"])
                        
                        if len(all_games) >= max_games:
                            break
                            
                    except Exception as e:
                        print(f"⚠️ Error fetching archive {i}: {e}")
                        continue
                        
            # Convert to PGN format
            pgn_games = []
            for game in all_games[:max_games]:
                if "pgn" in game:
                    pgn_games.append(game["pgn"])
            
            if pgn_games:
                pgn_content = "\n\n".join(pgn_games)
                with open("chess_com_games.pgn", "w", encoding="utf-8") as f:
                    f.write(pgn_content)
                print(f"✅ Saved {len(pgn_games)} games to chess_com_games.pgn")
                return pgn_games
            
        except Exception as e:
            print(f"❌ Chess.com download failed: {e}")
            return []
    
    def download_lichess_games(self, username, max_games=50):
        """Download games from Lichess"""
        print(f"🔍 Downloading Lichess games for {username}...")
        
        try:
            headers = {
                'User-Agent': 'ChessGPT/1.0 (Educational chess analysis tool)',
                'Accept': 'application/x-chess-pgn'
            }
            
            params = {
                'max': max_games,
                'format': 'pgn'
            }
            
            response = requests.get(f"https://lichess.org/api/games/user/{username}", 
                                  params=params, headers=headers)
            response.raise_for_status()
            
            pgn_content = response.text
            if pgn_content.strip():
                with open("lichess_games.pgn", "w", encoding="utf-8") as f:
                    f.write(pgn_content)
                
                # Count games
                game_count = pgn_content.count('[Event ')
                print(f"✅ Saved {game_count} games to lichess_games.pgn")
                return [pgn_content]
            
        except Exception as e:
            print(f"❌ Lichess download failed: {e}")
            return []
    
    def download_games(self, username, platform="auto"):
        """Download games from specified platform"""
        games = []
        
        if platform == "auto" or platform == "chess.com":
            chess_com_games = self.download_chess_com_games(username)
            games.extend(chess_com_games)
        
        if platform == "auto" or platform == "lichess":
            lichess_games = self.download_lichess_games(username)
            games.extend(lichess_games)
        
        return games
    
    def parse_pgn_files(self):
        """Parse PGN files and return games"""
        pgn_files = ["chess_com_games.pgn", "lichess_games.pgn"]
        all_games = []
        
        for pgn_file in pgn_files:
            if os.path.exists(pgn_file):
                print(f"📖 Parsing {pgn_file}...")
                try:
                    with open(pgn_file, "r", encoding="utf-8") as f:
                        while True:
                            game = chess.pgn.read_game(f)
                            if game is None:
                                break
                            all_games.append(game)
                except Exception as e:
                    print(f"⚠️ Error parsing {pgn_file}: {e}")
        
        print(f"📊 Total games loaded: {len(all_games)}")
        return all_games
    
    def analyze_games_with_stockfish(self, games, max_games=10):
        """Analyze games with Stockfish"""
        print(f"🔍 Analyzing games with Stockfish...")
        
        if not os.path.exists(self.stockfish_path):
            print(f"❌ Stockfish not found at {self.stockfish_path}")
            return []
        
        analyzed_games = []
        
        try:
            with chess.engine.SimpleEngine.popen_uci(self.stockfish_path) as engine:
                print(f"✅ Stockfish engine loaded")
                
                for i, game in enumerate(games[:max_games]):
                    print(f"🎯 Analyzing game {i+1}/{min(max_games, len(games))}...")
                    
                    board = game.board()
                    game_analysis = {
                        "white": game.headers.get("White", "Unknown"),
                        "black": game.headers.get("Black", "Unknown"),
                        "result": game.headers.get("Result", "*"),
                        "moves": [],
                        "mistakes": []
                    }
                    
                    move_count = 0
                    for move in game.mainline_moves():
                        board.push(move)
                        move_count += 1
                        
                        # Analyze every 3rd move up to move 20
                        if move_count % 3 == 0 and move_count <= 20:
                            try:
                                info = engine.analyse(board, chess.engine.Limit(depth=15))
                                best_move = info["pv"][0] if info["pv"] else None
                                score = info["score"]
                                
                                move_analysis = {
                                    "move_number": move_count,
                                    "actual_move": str(move),
                                    "best_move": str(best_move) if best_move else None,
                                    "evaluation": str(score) if score else None,
                                    "position": board.fen()
                                }
                                
                                game_analysis["moves"].append(move_analysis)
                                
                                # Check for mistakes (simplified)
                                if best_move and str(move) != str(best_move):
                                    game_analysis["mistakes"].append({
                                        "move": move_count,
                                        "played": str(move),
                                        "better": str(best_move)
                                    })
                                
                            except Exception as e:
                                print(f"⚠️ Error analyzing move {move_count}: {e}")
                                continue
                    
                    analyzed_games.append(game_analysis)
                    
        except Exception as e:
            print(f"❌ Stockfish analysis failed: {e}")
            return []
        
        print(f"✅ Analyzed {len(analyzed_games)} games")
        return analyzed_games
    
    def extract_weaknesses(self, analyzed_games, target_player):
        """Extract weaknesses from analyzed games"""
        print(f"🔍 Extracting weaknesses for {target_player}...")
        
        weaknesses = {
            "opening_mistakes": [],
            "tactical_errors": [],
            "positional_issues": [],
            "pattern_recognition": []
        }
        
        for game in analyzed_games:
            # Check if target player is in this game
            player_color = None
            if game["white"].lower() == target_player.lower():
                player_color = "white"
            elif game["black"].lower() == target_player.lower():
                player_color = "black"
            
            if player_color:
                # Analyze mistakes
                for mistake in game["mistakes"]:
                    if mistake["move"] <= 15:
                        weaknesses["opening_mistakes"].append({
                            "move": mistake["move"],
                            "played": mistake["played"],
                            "better": mistake["better"],
                            "game_id": f"{game['white']} vs {game['black']}"
                        })
                    else:
                        weaknesses["tactical_errors"].append({
                            "move": mistake["move"],
                            "played": mistake["played"],
                            "better": mistake["better"],
                            "game_id": f"{game['white']} vs {game['black']}"
                        })
        
        print(f"📊 Found {len(weaknesses['opening_mistakes'])} opening mistakes")
        print(f"📊 Found {len(weaknesses['tactical_errors'])} tactical errors")
        
        return weaknesses
    
    def create_training_data(self, username, analyzed_games, weaknesses):
        """Create training data for LLM"""
        print(f"📝 Creating training data for {username}...")
        
        # Load existing training data
        existing_data = []
        if os.path.exists(self.training_data_file):
            try:
                with open(self.training_data_file, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading existing data: {e}")
        
        # Create new training entries
        new_entries = []
        
        # Entry 1: Opening weaknesses
        if weaknesses["opening_mistakes"]:
            opening_input = f"Player {username} shows weaknesses in opening play:\n"
            for mistake in weaknesses["opening_mistakes"][:5]:
                opening_input += f"- Move {mistake['move']}: played {mistake['played']} instead of {mistake['better']}\n"
            
            opening_output = f"Strategy to exploit {username}'s opening weaknesses:\n"
            opening_output += "1. Force complex opening positions\n"
            opening_output += "2. Choose openings that lead to tactical complications\n"
            opening_output += "3. Avoid simplified, theoretical lines\n"
            opening_output += "4. Create early imbalances to increase decision-making pressure"
            
            new_entries.append({
                "input": {
                    "opponent_profile": {
                        "player_name": username,
                        "platform": "chess.com/lichess",
                        "games_analyzed": len(analyzed_games)
                    },
                    "opponent_weaknesses": [opening_input.strip()],
                    "tactical_vulnerabilities": [],
                    "experience_gaps": []
                },
                "output": {
                    "strategic_recommendations": {
                        "overall_game_plan": opening_output,
                        "opening_choices": [
                            {
                                "target_opening": "Tactical openings",
                                "exploitation_method": "Force complex positions",
                                "specific_lines": ["Sicilian Najdorf", "King's Indian Defense", "Dutch Defense"]
                            }
                        ]
                    },
                    "confidence_level": "high",
                    "expected_success_rate": 0.65
                },
                "metadata": {
                    "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                    "player_analyzed": username,
                    "analysis_type": "opening_weaknesses"
                }
            })
        
        # Entry 2: Tactical errors
        if weaknesses["tactical_errors"]:
            tactical_input = f"Player {username} shows tactical vulnerabilities:\n"
            for mistake in weaknesses["tactical_errors"][:5]:
                tactical_input += f"- Move {mistake['move']}: missed {mistake['better']}\n"
            
            tactical_output = f"Strategy to exploit {username}'s tactical weaknesses:\n"
            tactical_output += "1. Create tactical complications\n"
            tactical_output += "2. Maintain multiple threats\n"
            tactical_output += "3. Use tactical motifs they struggle with\n"
            tactical_output += "4. Increase time pressure in complex positions"
            
            new_entries.append({
                "input": {
                    "opponent_profile": {
                        "player_name": username,
                        "platform": "chess.com/lichess",
                        "games_analyzed": len(analyzed_games)
                    },
                    "opponent_weaknesses": [tactical_input.strip()],
                    "tactical_vulnerabilities": [],
                    "experience_gaps": []
                },
                "output": {
                    "strategic_recommendations": {
                        "overall_game_plan": tactical_output,
                        "opening_choices": [
                            {
                                "target_opening": "Tactical systems",
                                "exploitation_method": "Create tactical complexity",
                                "specific_lines": ["Sicilian Dragon", "Alekhine Defense", "Benoni Defense"]
                            }
                        ]
                    },
                    "confidence_level": "high",
                    "expected_success_rate": 0.70
                },
                "metadata": {
                    "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                    "player_analyzed": username,
                    "analysis_type": "tactical_errors"
                }
            })
        
        # Add new entries to existing data
        all_data = existing_data + new_entries
        
        # Save updated training data
        with open(self.training_data_file, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Training data updated with {len(new_entries)} new entries")
        print(f"📊 Total entries: {len(all_data)}")
        
        return all_data
    
    def analyze_player(self, username, platform="auto"):
        """Complete analysis pipeline"""
        print(f"🚀 Starting analysis for {username} on {platform}")
        
        # Step 1: Download games
        games = self.download_games(username, platform)
        if not games:
            print("❌ No games downloaded")
            return False
        
        # Step 2: Parse PGN files
        parsed_games = self.parse_pgn_files()
        if not parsed_games:
            print("❌ No games parsed")
            return False
        
        # Step 3: Analyze with Stockfish
        analyzed_games = self.analyze_games_with_stockfish(parsed_games)
        if not analyzed_games:
            print("❌ Stockfish analysis failed")
            return False
        
        # Step 4: Extract weaknesses
        weaknesses = self.extract_weaknesses(analyzed_games, username)
        
        # Step 5: Create training data
        training_data = self.create_training_data(username, analyzed_games, weaknesses)
        
        print(f"✅ Analysis completed for {username}")
        return True

def main():
    """Main function"""
    analyzer = ChessGameAnalyzer()
    
    # Get user input
    username, platform = analyzer.get_user_input()
    
    if not username:
        print("❌ No username provided")
        return
    
    # Analyze the player
    success = analyzer.analyze_player(username, platform)
    
    if success:
        print(f"\n🎉 Analysis complete for {username}!")
        print(f"📁 Training data saved to: {analyzer.training_data_file}")
        print(f"💡 Run the web UI to generate strategies!")
    else:
        print(f"\n❌ Analysis failed for {username}")

if __name__ == "__main__":
    main()
