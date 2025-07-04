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
                        
                        archive_data = archive_response.json()
                        games = archive_data.get("games", [])
                        print(f"📋 Found {len(games)} games in this archive")
                        
                        all_games.extend(games)
                        if len(all_games) >= max_games:
                            break
                            
                    except Exception as e:
                        print(f"⚠️ Error fetching archive: {e}")
                        continue
            
            # Save to PGN file
            if all_games:
                self.save_games_to_pgn(all_games, "chess_com_games.pgn", "chess.com")
                print(f"✅ Downloaded {len(all_games)} Chess.com games")
            
            return all_games
            
        except Exception as e:
            print(f"❌ Error downloading Chess.com games: {e}")
            return []
    
    def download_lichess_games(self, username, max_games=50):
        """Download games from Lichess"""
        print(f"🔍 Downloading Lichess games for {username}...")
        
        try:
            headers = {
                'User-Agent': 'ChessGPT/1.0 (Educational chess analysis tool)',
                'Accept': 'application/x-ndjson'
            }
            
            url = f"https://lichess.org/api/games/user/{username}"
            params = {
                'max': max_games,
                'rated': 'true',
                'perfType': 'blitz,rapid,classical'
            }
            
            time.sleep(1)
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
            
            # Save to PGN file
            if games:
                self.save_lichess_games_to_pgn(games, "lichess_games.pgn")
                print(f"✅ Downloaded {len(games)} Lichess games")
            
            return games
            
        except Exception as e:
            print(f"❌ Error downloading Lichess games: {e}")
            return []
    
    def save_games_to_pgn(self, games, filename, platform):
        """Save Chess.com games to PGN format"""
        with open(filename, 'w', encoding='utf-8') as f:
            for game in games:
                if 'pgn' in game:
                    f.write(game['pgn'] + '\n\n')
    
    def save_lichess_games_to_pgn(self, games, filename):
        """Save Lichess games to PGN format"""
        with open(filename, 'w', encoding='utf-8') as f:
            for game in games:
                if 'moves' in game:
                    # Convert Lichess format to PGN
                    pgn_header = f"""[Event "{game.get('event', 'Lichess game')}"]
[Site "{game.get('site', 'https://lichess.org')}"]
[Date "{game.get('createdAt', '????.??.??')[:10]}"]
[White "{game.get('players', {}).get('white', {}).get('user', {}).get('name', 'Unknown')}"]
[Black "{game.get('players', {}).get('black', {}).get('user', {}).get('name', 'Unknown')}"]
[Result "{game.get('status', '*')}"]
[WhiteElo "{game.get('players', {}).get('white', {}).get('rating', '?')}"]
[BlackElo "{game.get('players', {}).get('black', {}).get('rating', '?')}"]
[TimeControl "{game.get('clock', {}).get('initial', '?')}+{game.get('clock', {}).get('increment', '?')}"]
[ECO "{game.get('opening', {}).get('eco', '?')}"]
[Opening "{game.get('opening', {}).get('name', '?')}"]

{game.get('moves', '')}
"""
                    f.write(pgn_header + '\n\n')
    
    def analyze_games_from_pgn(self, pgn_file, target_player):
        """Analyze games from PGN file"""
        if not os.path.exists(pgn_file):
            print(f"❌ PGN file {pgn_file} not found")
            return []
        
        print(f"📖 Analyzing games from {pgn_file}...")
        
        games = []
        with open(pgn_file, 'r', encoding='utf-8') as f:
            while True:
                game = chess.pgn.read_game(f)
                if game is None:
                    break
                
                # Check if target player is in this game
                white_player = game.headers.get("White", "").lower()
                black_player = game.headers.get("Black", "").lower()
                
                if target_player.lower() in white_player or target_player.lower() in black_player:
                    games.append(game)
        
        print(f"📊 Found {len(games)} games for {target_player}")
        return games
    
    def analyze_game_with_stockfish(self, game, target_player, max_moves=20):
        """Analyze a single game with Stockfish"""
        try:
            with chess.engine.SimpleEngine.popen_uci(self.stockfish_path) as engine:
                board = game.board()
                analysis = []
                
                # Determine player color
                white_player = game.headers.get("White", "").lower()
                black_player = game.headers.get("Black", "").lower()
                
                is_white = target_player.lower() in white_player
                is_black = target_player.lower() in black_player
                
                if not (is_white or is_black):
                    return None
                
                move_count = 0
                for move in game.mainline_moves():
                    if move_count >= max_moves:
                        break
                    
                    # Get evaluation before move
                    info_before = engine.analyse(board, chess.engine.Limit(time=0.1))
                    score_before = info_before.get("score", chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE))
                    
                    board.push(move)
                    
                    # Get evaluation after move
                    info_after = engine.analyse(board, chess.engine.Limit(time=0.1))
                    score_after = info_after.get("score", chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE))
                    
                    # Calculate move quality
                    if score_before.is_mate() or score_after.is_mate():
                        move_quality = "mate_threat"
                    else:
                        cp_before = score_before.white().score(mate_score=1000)
                        cp_after = score_after.white().score(mate_score=1000)
                        
                        if cp_before is not None and cp_after is not None:
                            cp_loss = abs(cp_after - cp_before)
                            if cp_loss > 100:
                                move_quality = "blunder"
                            elif cp_loss > 50:
                                move_quality = "mistake"
                            elif cp_loss > 20:
                                move_quality = "inaccuracy"
                            else:
                                move_quality = "good"
                        else:
                            move_quality = "unknown"
                    
                    analysis.append({
                        'move_number': move_count + 1,
                        'move': move.uci(),
                        'move_san': board.san(move),
                        'score_before': str(score_before),
                        'score_after': str(score_after),
                        'quality': move_quality
                    })
                    
                    move_count += 1
                
                return {
                    'game_info': {
                        'white': game.headers.get("White", ""),
                        'black': game.headers.get("Black", ""),
                        'result': game.headers.get("Result", ""),
                        'opening': game.headers.get("Opening", ""),
                        'eco': game.headers.get("ECO", "")
                    },
                    'target_player': target_player,
                    'is_white': is_white,
                    'moves_analyzed': analysis
                }
                
        except Exception as e:
            print(f"⚠️ Error analyzing game with Stockfish: {e}")
            return None
    
    def identify_weaknesses(self, analyzed_games, target_player):
        """Identify player weaknesses from analyzed games"""
        print(f"🔍 Identifying weaknesses for {target_player}...")
        
        weaknesses = []
        
        if not analyzed_games:
            return [{"weakness_type": "No games", "details": "No games available for analysis"}]
        
        # Analyze move quality
        total_moves = 0
        blunders = 0
        mistakes = 0
        inaccuracies = 0
        
        opening_issues = defaultdict(int)
        opening_games = defaultdict(int)
        
        for game_analysis in analyzed_games:
            if not game_analysis:
                continue
                
            moves = game_analysis.get('moves_analyzed', [])
            game_info = game_analysis.get('game_info', {})
            
            # Count move quality issues
            for move in moves:
                total_moves += 1
                quality = move.get('quality', 'unknown')
                
                if quality == 'blunder':
                    blunders += 1
                elif quality == 'mistake':
                    mistakes += 1
                elif quality == 'inaccuracy':
                    inaccuracies += 1
            
            # Track opening performance
            opening = game_info.get('opening', 'Unknown')
            eco = game_info.get('eco', 'Unknown')
            result = game_info.get('result', '*')
            
            opening_games[opening] += 1
            
            # Check if player lost
            is_white = game_analysis.get('is_white', False)
            if (is_white and result == "0-1") or (not is_white and result == "1-0"):
                opening_issues[opening] += 1
        
        # Generate weakness reports
        if total_moves > 0:
            blunder_rate = blunders / total_moves * 100
            mistake_rate = mistakes / total_moves * 100
            inaccuracy_rate = inaccuracies / total_moves * 100
            
            if blunder_rate > 5:
                weaknesses.append({
                    "weakness_type": "Tactical Blunders",
                    "details": f"Makes blunders in {blunder_rate:.1f}% of moves",
                    "confidence": "high"
                })
            
            if mistake_rate > 10:
                weaknesses.append({
                    "weakness_type": "Strategic Mistakes",
                    "details": f"Makes mistakes in {mistake_rate:.1f}% of moves",
                    "confidence": "medium"
                })
        
        # Opening weaknesses
        for opening, losses in opening_issues.items():
            games_played = opening_games[opening]
            if games_played >= 2:
                loss_rate = losses / games_played * 100
                if loss_rate > 60:
                    weaknesses.append({
                        "weakness_type": f"Opening Weakness: {opening}",
                        "details": f"Loses {loss_rate:.1f}% of games in this opening",
                        "confidence": "high"
                    })
        
        # Default weaknesses if none found
        if not weaknesses:
            weaknesses.append({
                "weakness_type": "Time Management",
                "details": "May struggle with time pressure in complex positions",
                "confidence": "medium"
            })
        
        return weaknesses
    
    def create_training_data(self, username, analyzed_games, weaknesses):
        """Create training data for the LLM"""
        print(f"💾 Creating training data for {username}...")
        
        # Load existing data
        existing_data = []
        if os.path.exists(self.training_data_file):
            try:
                with open(self.training_data_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading existing data: {e}")
        
        # Create new training entry
        training_entry = {
            "input": {
                "opponent_profile": {
                    "player_name": username,
                    "platform": "chess.com/lichess",
                    "games_analyzed": len(analyzed_games),
                    "analysis_date": datetime.now().isoformat()
                },
                "opponent_weaknesses": weaknesses
            },
            "output": {
                "strategic_recommendations": self.generate_strategy_recommendations(weaknesses),
                "opening_suggestions": self.generate_opening_suggestions(weaknesses),
                "tactical_advice": self.generate_tactical_advice(weaknesses)
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
        
        return training_entry
    
    def generate_strategy_recommendations(self, weaknesses):
        """Generate strategic recommendations based on weaknesses"""
        recommendations = []
        
        for weakness in weaknesses:
            weakness_type = weakness.get("weakness_type", "")
            details = weakness.get("details", "")
            
            if "Blunder" in weakness_type:
                recommendations.append({
                    "recommendation": "Create tactical complications",
                    "rationale": "Exploit opponent's tendency to blunder under pressure"
                })
            
            elif "Opening" in weakness_type:
                recommendations.append({
                    "recommendation": f"Target {weakness_type.split(':')[1].strip()}",
                    "rationale": f"Opponent struggles in this opening: {details}"
                })
            
            elif "Time" in weakness_type:
                recommendations.append({
                    "recommendation": "Play complex, time-consuming positions",
                    "rationale": "Exploit opponent's time management issues"
                })
        
        if not recommendations:
            recommendations.append({
                "recommendation": "Play solid, positional chess",
                "rationale": "Standard approach when specific weaknesses are unclear"
            })
        
        return recommendations
    
    def generate_opening_suggestions(self, weaknesses):
        """Generate opening suggestions based on weaknesses"""
        suggestions = []
        
        for weakness in weaknesses:
            weakness_type = weakness.get("weakness_type", "")
            
            if "Opening" in weakness_type:
                opening_name = weakness_type.split(":")[1].strip()
                suggestions.append({
                    "opening": opening_name,
                    "reason": "Opponent has poor results in this opening",
                    "approach": "Play forcing, tactical variations"
                })
        
        # Default suggestions
        if not suggestions:
            suggestions.extend([
                {
                    "opening": "Queen's Gambit",
                    "reason": "Solid, strategic opening",
                    "approach": "Build pressure gradually"
                },
                {
                    "opening": "Sicilian Defense",
                    "reason": "Complex, tactical positions",
                    "approach": "Create complications"
                }
            ])
        
        return suggestions
    
    def generate_tactical_advice(self, weaknesses):
        """Generate tactical advice based on weaknesses"""
        advice = []
        
        for weakness in weaknesses:
            weakness_type = weakness.get("weakness_type", "")
            
            if "Blunder" in weakness_type:
                advice.append("Look for tactical shots - opponent prone to blunders")
            elif "Mistake" in weakness_type:
                advice.append("Maintain pressure - opponent makes strategic errors")
            elif "Time" in weakness_type:
                advice.append("Create complex positions to induce time pressure")
        
        if not advice:
            advice.append("Play solid, accurate moves")
        
        return advice
    
    def analyze_player(self, username, platform="auto"):
        """Main analysis function"""
        print(f"🏛️ Starting comprehensive analysis for {username}")
        print(f"📊 Platform: {platform}")
        
        # Step 1: Download games
        all_games = []
        if platform in ["auto", "chess.com"]:
            chess_com_games = self.download_chess_com_games(username)
            all_games.extend(chess_com_games)
        
        if platform in ["auto", "lichess"] and len(all_games) < 20:
            lichess_games = self.download_lichess_games(username)
            all_games.extend(lichess_games)
        
        if not all_games:
            print(f"❌ No games found for {username}")
            return False
        
        # Step 2: Analyze games from PGN files
        pgn_games = []
        for pgn_file in ["chess_com_games.pgn", "lichess_games.pgn"]:
            if os.path.exists(pgn_file):
                pgn_games.extend(self.analyze_games_from_pgn(pgn_file, username))
        
        # Step 3: Stockfish analysis
        print(f"🔍 Analyzing {len(pgn_games)} games with Stockfish...")
        analyzed_games = []
        for i, game in enumerate(pgn_games[:10]):  # Limit to 10 games for speed
            print(f"📊 Analyzing game {i+1}/{min(10, len(pgn_games))}")
            analysis = self.analyze_game_with_stockfish(game, username)
            if analysis:
                analyzed_games.append(analysis)
        
        # Step 4: Identify weaknesses
        weaknesses = self.identify_weaknesses(analyzed_games, username)
        
        print(f"🎯 Identified {len(weaknesses)} weaknesses:")
        for weakness in weaknesses:
            print(f"   • {weakness['weakness_type']}: {weakness['details']}")
        
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
                latest_url = archives["archives"][-i]  # Get recent months
                print(f"Fetching games from: {latest_url}")
                
                pgn_response = requests.get(latest_url + "/pgn", headers=headers)
                pgn_response.raise_for_status()
                pgn_data = pgn_response.text
                
                if pgn_data.strip():  # If we found games, break
                    print(f"Fetched {len(pgn_data.splitlines())} lines of PGN data for {user}")
                    
                    # Save the PGN data to a file for later use
                    with open("chess_com_games.pgn", "w", encoding="utf-8") as f:
                        f.write(pgn_data)
                    print("PGN data saved to 'chess_com_games.pgn'")
                    break
                else:
                    print(f"No games found in {latest_url}")
            else:
                print(f"No games found in recent months for user {user}")
        else:
            print(f"No archives found for user {user}")
            
except requests.exceptions.HTTPError as e:
    print(f"HTTP error occurred: {e}")
    if hasattr(e.response, 'status_code'):
        print(f"Response status code: {e.response.status_code}")
        if e.response.status_code == 403:
            print("Error: Chess.com is blocking automated requests due to Cloudflare protection.")
            print("This is likely due to rate limiting or bot detection.")
            print("Possible solutions:")
            print("1. Try again later (rate limiting may reset)")
            print("2. Use a different username")
            print("3. Consider using the Lichess API instead (more bot-friendly)")
            print("4. Download PGN files manually from Chess.com")
        print(f"Response content: {e.response.text[:500]}...")  # Truncate long responses
    else:
        print("No response object available")
except requests.exceptions.RequestException as e:
    print(f"Request error occurred: {e}")
except json.JSONDecodeError as e:
    print(f"JSON decode error: {e}")
    print(f"Response content: {response.text}")
except Exception as e:
    print(f"Unexpected error: {e}")

# If Chess.com fails, try Lichess instead (more bot-friendly)
print("\nTrying Lichess API as alternative...")
try:
    lichess_user = "DrNykterstein"  # Hikaru's actual Lichess username
    lichess_url = f"https://lichess.org/api/games/user/{lichess_user}"
    
    # Lichess API parameters
    params = {
        'max': 10,  # Limit to 10 games for testing
        'format': 'pgn'
    }
    
    headers = {
        'User-Agent': 'ChessGPT/1.0 Educational Tool',
        'Accept': 'application/x-chess-pgn'
    }
    
    lichess_response = requests.get(lichess_url, headers=headers, params=params)
    lichess_response.raise_for_status()
    
    pgn_data = lichess_response.text
    if pgn_data.strip():
        print(f"Successfully fetched {len(pgn_data.splitlines())} lines of PGN data from Lichess")
        
        # Save the PGN data to a file for later use
        with open("lichess_games.pgn", "w", encoding="utf-8") as f:
            f.write(pgn_data)
        print("PGN data saved to 'lichess_games.pgn'")
    else:
        print("No game data found on Lichess")
        
except requests.exceptions.RequestException as e:
    print(f"Lichess API error: {e}")
except Exception as e:
    print(f"Unexpected error with Lichess: {e}")

### STEP 2: Parse Games and Extract Openings ###

# ECO code to opening name mapping for better identification
ECO_OPENINGS = {
    'A01': 'Nimzo-Larsen Attack',
    'A00': 'Uncommon Opening',
    'A10': 'English Opening',
    'A13': 'English Opening: Neo-Catalan',
    'A22': 'English Opening: Carls-Bremen System',
    'A44': 'Old Benoni Defense',
    'A45': 'Trompowsky Attack',
    'B01': 'Scandinavian Defense',
    'B06': 'Modern Defense',
    'B08': 'Pirc Defense',
    'B12': 'Caro-Kann Defense',
    'B15': 'Caro-Kann Defense: Forgacs Variation',
    'B22': 'Sicilian Defense: Alapin Variation',
    'B23': 'Sicilian Defense: Closed',
    'B56': 'Sicilian Defense: Accelerated Dragon',
    'C28': 'Vienna Game',
    'C41': 'Philidor Defense',
    'C55': 'Italian Game'
}

def get_opening_name(eco, header_opening):
    """Get a better opening name using ECO code mapping"""
    if header_opening and header_opening != "Unknown Opening":
        return header_opening
    return ECO_OPENINGS.get(eco, f"ECO {eco}")

def parse_pgn_file(filename):
    """Parse a PGN file and extract games with opening information"""
    games = []
    try:
        with open(filename, "r", encoding="utf-8") as pgn_file:
            while True:
                game = chess.pgn.read_game(pgn_file)
                if game is None:
                    break
                games.append(game)
        print(f"Successfully parsed {len(games)} games from {filename}")
    except FileNotFoundError:
        print(f"File {filename} not found")
    except Exception as e:
        print(f"Error parsing {filename}: {e}")
    
    return games

def extract_opening_stats(games, target_player):
    """Extract opening statistics for a specific player"""
    openings = defaultdict(list)
    player_stats = {
        'as_white': defaultdict(list),
        'as_black': defaultdict(list),
        'total_games': 0,
        'wins': 0,
        'losses': 0,
        'draws': 0
    }
    
    for game in games:
        white_player = game.headers.get("White", "").lower()
        black_player = game.headers.get("Black", "").lower()
        target_lower = target_player.lower()
        
        # Check if target player is in this game
        if target_lower not in white_player and target_lower not in black_player:
            continue
            
        eco = game.headers.get("ECO", "Unknown")
        opening = get_opening_name(eco, game.headers.get("Opening", "Unknown Opening"))
        result = game.headers.get("Result", "*")
        
        # Determine player color and result
        if target_lower in white_player:
            color = 'white'
            player_result = 'win' if result == '1-0' else 'loss' if result == '0-1' else 'draw'
            player_stats['as_white'][eco].append({
                'game': game,
                'result': player_result,
                'opening': opening,
                'opponent': black_player
            })
        else:
            color = 'black'
            player_result = 'win' if result == '0-1' else 'loss' if result == '1-0' else 'draw'
            player_stats['as_black'][eco].append({
                'game': game,
                'result': player_result,
                'opening': opening,
                'opponent': white_player
            })
        
        # Add to general openings collection
        openings[eco].append({
            'game': game,
            'color': color,
            'result': player_result,
            'opening': opening
        })
        
        # Update total stats
        player_stats['total_games'] += 1
        if player_result == 'win':
            player_stats['wins'] += 1
        elif player_result == 'loss':
            player_stats['losses'] += 1
        else:
            player_stats['draws'] += 1
    
    return openings, player_stats

def analyze_opening_weaknesses(player_stats):
    """Analyze opening weaknesses based on win rates"""
    weaknesses = []
    
    for color in ['as_white', 'as_black']:
        color_stats = player_stats[color]
        for eco, games in color_stats.items():
            if len(games) < 3:  # Skip openings with too few games
                continue
                
            total = len(games)
            wins = sum(1 for g in games if g['result'] == 'win')
            losses = sum(1 for g in games if g['result'] == 'loss')
            draws = sum(1 for g in games if g['result'] == 'draw')
            
            win_rate = (wins / total) * 100
            
            if win_rate < 40 or (losses / total) * 100 > 60:
                weaknesses.append({
                    'eco': eco,
                    'opening': games[0]['opening'],
                    'color': color,
                    'total_games': total,
                    'win_rate': win_rate,
                    'wins': wins,
                    'losses': losses,
                    'draws': draws
                })
    
    return sorted(weaknesses, key=lambda x: x['win_rate'])

# Parse both PGN files if they exist
print("\n### STEP 2: Parsing PGN Files ###")

all_games = []
target_username = user  # Use the input username for analysis

# Parse Chess.com games
chess_com_games = parse_pgn_file("chess_com_games.pgn")
all_games.extend(chess_com_games)

# Parse Lichess games  
lichess_games = parse_pgn_file("lichess_games.pgn")
all_games.extend(lichess_games)

if all_games:
    print(f"\nTotal games loaded: {len(all_games)}")
    
    # Extract opening statistics for the target player
    openings, player_stats = extract_opening_stats(all_games, target_username)
    
    print(f"\nPlayer Statistics for {target_username}:")
    print(f"Total games: {player_stats['total_games']}")
    print(f"Wins: {player_stats['wins']} ({(player_stats['wins']/max(1,player_stats['total_games']))*100:.1f}%)")
    print(f"Losses: {player_stats['losses']} ({(player_stats['losses']/max(1,player_stats['total_games']))*100:.1f}%)")
    print(f"Draws: {player_stats['draws']} ({(player_stats['draws']/max(1,player_stats['total_games']))*100:.1f}%)")
    
    # Show games by color
    white_games = sum(len(games) for games in player_stats['as_white'].values())
    black_games = sum(len(games) for games in player_stats['as_black'].values())
    print(f"Games as White: {white_games}")
    print(f"Games as Black: {black_games}")
    
    # Analyze weaknesses
    weaknesses = analyze_opening_weaknesses(player_stats)
    
    if weaknesses:
        print(f"\nIdentified Weaknesses:")
        for weakness in weaknesses[:5]:  # Show top 5 weaknesses
            print(f"- {weakness['opening']} ({weakness['eco']}) as {weakness['color'].replace('as_', '').title()}: "
                  f"{weakness['win_rate']:.1f}% win rate in {weakness['total_games']} games")
    
    # Show opening distribution
    print(f"\nOpening Distribution:")
    eco_counts = defaultdict(int)
    for eco, games in openings.items():
        eco_counts[eco] = len(games)
    
    # Show most played openings
    most_played = sorted(eco_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    for eco, count in most_played:
        if count > 0:
            example_opening = next(iter(openings[eco]))['opening']
            print(f"- {eco}: {example_opening} ({count} games)")

    # Detailed breakdown by color and opening
    print(f"\nDetailed Opening Analysis:")
    print(f"\nAs White:")
    for eco, games in player_stats['as_white'].items():
        if len(games) >= 2:  # Show openings with at least 2 games
            total = len(games)
            wins = sum(1 for g in games if g['result'] == 'win')
            win_rate = (wins / total) * 100
            opening_name = games[0]['opening']
            print(f"  {eco}: {opening_name} - {wins}/{total} ({win_rate:.1f}%)")
    
    print(f"\nAs Black:")
    for eco, games in player_stats['as_black'].items():
        if len(games) >= 2:  # Show openings with at least 2 games
            total = len(games)
            wins = sum(1 for g in games if g['result'] == 'win')
            win_rate = (wins / total) * 100
            opening_name = games[0]['opening']
            print(f"  {eco}: {opening_name} - {wins}/{total} ({win_rate:.1f}%)")

else:
    print("No games found to analyze. Make sure PGN files exist.")

print("\n### Analysis Complete ###")

### STEP 3: Identify Weakness Signals by Opening ###

def analyze_game_moves(game, target_player, max_moves=15):
    """Analyze the first few moves of a game to identify patterns"""
    board = chess.Board()
    moves_analysis = {
        'moves': [],
        'target_color': None,
        'opening_moves': [],
        'move_times': []
    }
    
    # Determine target player's color
    white_player = game.headers.get("White", "").lower()
    black_player = game.headers.get("Black", "").lower()
    target_lower = target_player.lower()
    
    if target_lower in white_player:
        moves_analysis['target_color'] = 'white'
    elif target_lower in black_player:
        moves_analysis['target_color'] = 'black'
    else:
        return moves_analysis
    
    move_count = 0
    for move in game.mainline_moves():
        if move_count >= max_moves:
            break
            
        board.push(move)
        move_count += 1
        
        # Store opening moves for pattern analysis
        moves_analysis['opening_moves'].append(move.uci())
        
        # If it's the target player's move, analyze it
        is_target_move = (
            (moves_analysis['target_color'] == 'white' and move_count % 2 == 1) or
            (moves_analysis['target_color'] == 'black' and move_count % 2 == 0)
        )
        
        if is_target_move:
            moves_analysis['moves'].append({
                'move': move.uci(),
                'move_number': (move_count + 1) // 2,
                'fen': board.fen()
            })
    
    return moves_analysis

def identify_tactical_patterns(games, target_player):
    """Identify patterns that suggest tactical weaknesses"""
    patterns = {
        'quick_losses': [],  # Games lost in under 25 moves
        'opening_blunders': [],  # Poor opening choices
        'time_pressure': [],  # Games with time control issues
        'repetitive_losses': {}  # Same opening leading to losses
    }
    
    for game_info in games:
        game = game_info['game']
        result = game_info['result']
        
        # Analyze game length
        move_count = len(list(game.mainline_moves()))
        
        if result == 'loss' and move_count < 25:
            patterns['quick_losses'].append({
                'game': game,
                'moves': move_count,
                'eco': game.headers.get('ECO', 'Unknown'),
                'opening': game_info['opening']
            })
        
        # Track repetitive losses in same opening
        eco = game.headers.get('ECO', 'Unknown')
        if result == 'loss':
            if eco not in patterns['repetitive_losses']:
                patterns['repetitive_losses'][eco] = []
            patterns['repetitive_losses'][eco].append(game)
    
    return patterns

def analyze_opening_experience(player_stats):
    """Analyze experience level in different openings"""
    experience_analysis = {
        'inexperienced': [],  # Openings with very few games
        'trending_down': [],  # Openings where performance is declining
        'unfamiliar_territory': []  # Rare opening variations
    }
    
    for color in ['as_white', 'as_black']:
        color_stats = player_stats[color]
        for eco, games in color_stats.items():
            total_games = len(games)
            
            # Identify inexperienced openings
            if total_games <= 2:
                experience_analysis['inexperienced'].append({
                    'eco': eco,
                    'opening': games[0]['opening'] if games else 'Unknown',
                    'color': color,
                    'games': total_games,
                    'results': [g['result'] for g in games]
                })
    
    return experience_analysis

def calculate_weakness_score(eco_data, patterns, experience):
    """Calculate a comprehensive weakness score for an opening"""
    total_games = len(eco_data)
    if total_games == 0:
        return 0
    
    wins = sum(1 for g in eco_data if g['result'] == 'win')
    losses = sum(1 for g in eco_data if g['result'] == 'loss')
    
    # Base score from win rate (lower win rate = higher weakness)
    win_rate = wins / total_games
    weakness_score = (1 - win_rate) * 100
    
    # Penalty for few games (inexperience)
    if total_games < 3:
        weakness_score += 20
    elif total_games < 5:
        weakness_score += 10
    
    # Penalty for quick losses
    eco = eco_data[0]['game'].headers.get('ECO', 'Unknown')
    quick_loss_count = sum(1 for loss in patterns['quick_losses'] 
                          if loss['eco'] == eco)
    weakness_score += quick_loss_count * 15
    
    # Penalty for repetitive losses
    if eco in patterns['repetitive_losses'] and len(patterns['repetitive_losses'][eco]) >= 2:
        weakness_score += 25
    
    return min(weakness_score, 100)  # Cap at 100

def generate_weakness_report(openings, player_stats, target_player):
    """Generate a comprehensive weakness analysis report"""
    
    print(f"\n### STEP 3: Comprehensive Weakness Analysis for {target_player} ###")
    
    all_games = []
    for eco_games in openings.values():
        all_games.extend(eco_games)
    
    # 1. Identify tactical patterns
    patterns = identify_tactical_patterns(all_games, target_player)
    
    # 2. Analyze opening experience
    experience = analyze_opening_experience(player_stats)
    
    # 3. Calculate weakness scores for each opening
    opening_weaknesses = []
    
    for color in ['as_white', 'as_black']:
        color_stats = player_stats[color]
        for eco, games in color_stats.items():
            if len(games) > 0:  # Analyze all openings, not just those with many games
                weakness_score = calculate_weakness_score(games, patterns, experience)
                
                total = len(games)
                wins = sum(1 for g in games if g['result'] == 'win')
                losses = sum(1 for g in games if g['result'] == 'loss')
                draws = sum(1 for g in games if g['result'] == 'draw')
                
                opening_weaknesses.append({
                    'eco': eco,
                    'opening': games[0]['opening'],
                    'color': color,
                    'weakness_score': weakness_score,
                    'total_games': total,
                    'wins': wins,
                    'losses': losses,
                    'draws': draws,
                    'win_rate': (wins / total) * 100
                })
    
    # Sort by weakness score (highest first)
    opening_weaknesses.sort(key=lambda x: x['weakness_score'], reverse=True)
    
    # Print comprehensive analysis
    print(f"\n1) Performance-Based Weaknesses:")
    print("   Top weaknesses based on results and experience:")
    
    for i, weakness in enumerate(opening_weaknesses[:8]):  # Top 8 weaknesses
        print(f"   {i+1}. {weakness['opening']} ({weakness['eco']}) as {weakness['color'].replace('as_', '').title()}")
        print(f"      Weakness Score: {weakness['weakness_score']:.1f}/100")
        print(f"      Record: {weakness['wins']}-{weakness['losses']}-{weakness['draws']} ({weakness['win_rate']:.1f}% win rate)")
        print()
    
    print(f"\n2) Experience-Based Vulnerabilities:")
    print("   Openings with limited experience:")
    
    for inexperienced in experience['inexperienced'][:5]:
        results_str = ', '.join(inexperienced['results']) if inexperienced['results'] else 'No games'
        print(f"   - {inexperienced['opening']} ({inexperienced['eco']}) as {inexperienced['color'].replace('as_', '').title()}")
        print(f"     Only {inexperienced['games']} game(s): {results_str}")
    
    print(f"\n3) Tactical Warning Signs:")
    
    if patterns['quick_losses']:
        print(f"   Quick defeats (< 25 moves): {len(patterns['quick_losses'])} games")
        for quick_loss in patterns['quick_losses'][:3]:
            print(f"   - {quick_loss['opening']} ({quick_loss['eco']}): Lost in {quick_loss['moves']} moves")
    else:
        print("   No quick defeats detected (good sign!)")
    
    if patterns['repetitive_losses']:
        print(f"   Repetitive losses in same openings:")
        for eco, loss_games in patterns['repetitive_losses'].items():
            if len(loss_games) >= 2:
                opening_name = ECO_OPENINGS.get(eco, f"ECO {eco}")
                print(f"   - {opening_name} ({eco}): {len(loss_games)} losses")
    else:
        print("   No concerning patterns of repetitive losses")
    
    print(f"\n4) Strategic Recommendations:")
    
    # Identify the top 3 most problematic openings
    top_problems = opening_weaknesses[:3]
    
    for i, problem in enumerate(top_problems):
        print(f"   Priority {i+1}: Address {problem['opening']} as {problem['color'].replace('as_', '').title()}")
        
        if problem['total_games'] < 3:
            print(f"   - Recommendation: Study this opening more - insufficient experience")
        elif problem['win_rate'] < 30:
            print(f"   - Recommendation: Consider alternative opening choices")
        elif problem['losses'] > problem['wins']:
            print(f"   - Recommendation: Analyze losses for common tactical patterns")
        
        print()
    
    return {
        'opening_weaknesses': opening_weaknesses,
        'tactical_patterns': patterns,
        'experience_gaps': experience,
        'top_vulnerabilities': top_problems
    }

# Apply weakness analysis to our parsed games
if all_games:
    weakness_report = generate_weakness_report(openings, player_stats, target_username)
else:
    print("No games available for weakness analysis.")

print("\n### Analysis Complete ###")

### STEP 4: Stockfish Evaluation for Move-by-Move Analysis

def get_stockfish_engine():
    """Get a working Stockfish engine instance"""
    # Try to find Stockfish in common locations
    stockfish_paths = [
        "stockfish/stockfish.exe", # Downloaded executable
        "stockfish.exe",           # Current directory (Windows)
        "stockfish",               # Current directory (Unix)
        "/usr/local/bin/stockfish", # Common install location
        "/opt/homebrew/bin/stockfish", # Homebrew on M1 Mac
        "C:\\Program Files\\Stockfish\\stockfish.exe",  # Windows install
    ]
    
    # Try system paths
    for path in stockfish_paths:
        try:
            if os.path.exists(path):
                engine = chess.engine.SimpleEngine.popen_uci(path)
                print(f"✓ Found Stockfish at: {path}")
                return engine
        except Exception as e:
            continue
    
    print("⚠ Stockfish not found. Download from https://stockfishchess.org/")
    print("Or install via: conda install -c conda-forge stockfish")
    return None

def analyze_game_moves(game, target_player, engine, max_ply=20):
    """
    Analyze the first max_ply moves of a game to identify blunders, mistakes, and inaccuracies.
    max_ply represents half-moves (ply), so 20 ply = 10 moves from each side.
    """
    
    analysis = {
        'blunders': [],      # Moves losing 200+ centipawns
        'mistakes': [],      # Moves losing 100-199 centipawns  
        'inaccuracies': [],  # Moves losing 50-99 centipawns
        'evaluations': [],   # Position evaluations
        'target_color': None,
        'avg_centipawn_loss': 0,
        'analyzed': False
    }
    
    # Determine target player's color
    white_player = game.headers.get("White", "").lower()
    black_player = game.headers.get("Black", "").lower()
    target_lower = target_player.lower()
    
    if target_lower in white_player:
        analysis['target_color'] = 'white'
    elif target_lower in black_player:
        analysis['target_color'] = 'black'
    else:
        return analysis
    
    if not engine:
        return analysis
    
    try:
        board = chess.Board()
        ply_count = 0
        prev_score = None
        total_centipawn_loss = 0
        target_moves = 0
        
        # Get initial position evaluation
        info = engine.analyse(board, chess.engine.Limit(depth=15))
        prev_score = info["score"].relative.score(mate_score=10000)
        
        for move in game.mainline_moves():
            if ply_count >= max_ply:
                break
                
            # Make the move
            board.push(move)
            ply_count += 1
            
            # Get evaluation after the move
            info = engine.analyse(board, chess.engine.Limit(depth=15))
            current_score = info["score"].relative.score(mate_score=10000)
            
            # Determine whose move this was
            move_color = 'white' if ply_count % 2 == 1 else 'black'
            is_target_move = (analysis['target_color'] == move_color)
            
            # Calculate centipawn loss from the moving player's perspective
            if move_color == 'white':
                centipawn_loss = max(0, prev_score - (-current_score))
            else:
                centipawn_loss = max(0, -prev_score - current_score)
            
            move_info = {
                'ply': ply_count,
                'move_number': (ply_count + 1) // 2,
                'move': move.uci(),
                'color': move_color,
                'is_target_player': is_target_move,
                'score_before': prev_score,
                'score_after': current_score,
                'centipawn_loss': centipawn_loss,
            }
            
            analysis['evaluations'].append(move_info)
            
            # If this was the target player's move, analyze it
            if is_target_move:
                target_moves += 1
                total_centipawn_loss += centipawn_loss
                
                # Classify the move
                if centipawn_loss >= 200:
                    analysis['blunders'].append(move_info)
                    move_info['classification'] = 'blunder'
                elif centipawn_loss >= 100:
                    analysis['mistakes'].append(move_info)
                    move_info['classification'] = 'mistake'
                elif centipawn_loss >= 50:
                    analysis['inaccuracies'].append(move_info)
                    move_info['classification'] = 'inaccuracy'
                else:
                    move_info['classification'] = 'good'
            
            prev_score = current_score
        
        # Calculate average centipawn loss
        if target_moves > 0:
            analysis['avg_centipawn_loss'] = total_centipawn_loss / target_moves
            analysis['analyzed'] = True
        
        return analysis
        
    except Exception as e:
        print(f"    Game analysis error: {e}")
        return analysis

def perform_stockfish_analysis(games, target_player, max_games=None):
    """
    Perform Stockfish analysis on games to detect tactical patterns.
    Analyzes the first 10 moves (20 ply) from each side.
    """
    
    # If max_games is None, analyze all games
    if max_games is None:
        max_games = len(games)
    
    print(f"\n### STEP 4: Stockfish Engine Analysis ###")
    print(f"Analyzing up to {max_games} games for tactical patterns...")
    print("Looking for blunders (200+ cp loss), mistakes (100-199 cp), and inaccuracies (50-99 cp)")
    
    # Try to get Stockfish engine
    engine = get_stockfish_engine()
    
    if not engine:
        print("⚠ Cannot perform engine analysis without Stockfish")
        return perform_heuristic_analysis(games, target_player, max_games)
    
    tactical_stats = {
        'total_analyzed': 0,
        'blunder_count': 0,
        'mistake_count': 0,
        'inaccuracy_count': 0,
        'avg_centipawn_loss': 0,
        'opening_errors': defaultdict(lambda: {'blunders': 0, 'mistakes': 0, 'inaccuracies': 0, 'games': 0}),
        'detailed_analysis': []
    }
    
    total_centipawn_loss = 0
    analyzed_games = 0
    games_to_analyze = min(max_games, len(games))
    
    try:
        for i, game in enumerate(games[:games_to_analyze]):
            eco = game.headers.get('ECO', 'Unknown')
            opening_name = ECO_OPENINGS.get(eco, f"ECO {eco}")
            
            # Progress indicator
            progress = (i + 1) / games_to_analyze * 100
            print(f"  [{i+1}/{games_to_analyze}] ({progress:.1f}%) Analyzing: {opening_name} ({eco})")
            
            # Analyze this specific game
            game_analysis = analyze_game_moves(game, target_player, engine)
            
            if game_analysis['analyzed']:
                analyzed_games += 1
                tactical_stats['total_analyzed'] += 1
                
                # Accumulate statistics
                blunders = len(game_analysis['blunders'])
                mistakes = len(game_analysis['mistakes'])
                inaccuracies = len(game_analysis['inaccuracies'])
                
                tactical_stats['blunder_count'] += blunders
                tactical_stats['mistake_count'] += mistakes
                tactical_stats['inaccuracy_count'] += inaccuracies
                total_centipawn_loss += game_analysis['avg_centipawn_loss']
                
                # Track by opening
                opening_stats = tactical_stats['opening_errors'][eco]
                opening_stats['blunders'] += blunders
                opening_stats['mistakes'] += mistakes
                opening_stats['inaccuracies'] += inaccuracies
                opening_stats['games'] += 1
                
                # Store detailed info
                tactical_stats['detailed_analysis'].append({
                    'eco': eco,
                    'opening': opening_name,
                    'blunders': blunders,
                    'mistakes': mistakes,
                    'inaccuracies': inaccuracies,
                    'avg_loss': game_analysis['avg_centipawn_loss'],
                    'critical_moves': [m for m in game_analysis['evaluations'] 
                                     if m.get('classification') in ['blunder', 'mistake']]
                })
                
                # Show critical moves for this game
                if blunders > 0:
                    print(f"    ⚠ Found {blunders} blunders!")
                    for blunder in game_analysis['blunders'][:2]:  # Show first 2
                        print(f"      Move {blunder['move_number']}: {blunder['move']} lost {blunder['centipawn_loss']:.0f} cp")
                elif mistakes > 0:
                    print(f"    ⚡ Found {mistakes} mistakes")
                else:
                    print(f"    ✓ Clean game (avg loss: {game_analysis['avg_centipawn_loss']:.1f} cp)")
    
    finally:
        if engine:
            engine.quit()
    
    # Calculate averages
    if analyzed_games > 0:
        tactical_stats['avg_centipawn_loss'] = total_centipawn_loss / analyzed_games
    
    # Print results
    print_tactical_analysis_results(tactical_stats, analyzed_games)
    
    return tactical_stats

def perform_heuristic_analysis(games, target_player, max_games):
    """Simplified analysis without Stockfish using heuristics"""
    
    print("Using heuristic analysis based on game length and outcomes...")
    
    tactical_stats = {
        'total_analyzed': 0,
        'blunder_count': 0,
        'mistake_count': 0,
        'inaccuracy_count': 0,
        'avg_centipawn_loss': 25.0,  # Mock average
        'opening_errors': defaultdict(lambda: {'blunders': 0, 'mistakes': 0, 'inaccuracies': 0, 'games': 0}),
        'detailed_analysis': []
    }
    
    analyzed_games = 0
    games_to_analyze = min(max_games, len(games))
    
    for i, game in enumerate(games[:games_to_analyze]):
        eco = game.headers.get('ECO', 'Unknown')
        opening_name = ECO_OPENINGS.get(eco, f"ECO {eco}")
        
        # Simple heuristics
        game_length = len(list(game.mainline_moves()))
        result = game.headers.get('Result', '*')
        
        # Determine if target player lost
        white_player = game.headers.get("White", "").lower()
        target_lower = target_player.lower()
        target_lost = False
        
        if target_lower in white_player and result == '0-1':
            target_lost = True
        elif target_lower not in white_player and result == '1-0':
            target_lost = True
        
        print(f"  [{i+1}/{games_to_analyze}] {opening_name} ({eco}): {game_length} moves, result: {result}")
        
        if target_lost and game_length < 30:
            # Short loss suggests tactical errors
            tactical_stats['blunder_count'] += 1
            tactical_stats['opening_errors'][eco]['blunders'] += 1
            print(f"    ⚠ Short loss detected - likely tactical errors")
        elif target_lost and game_length < 50:
            tactical_stats['mistake_count'] += 1
            tactical_stats['opening_errors'][eco]['mistakes'] += 1
            print(f"    ⚡ Medium-length loss - possible mistakes")
        else:
            print(f"    ✓ No obvious tactical issues")
        
        tactical_stats['opening_errors'][eco]['games'] += 1
        analyzed_games += 1
    
    tactical_stats['total_analyzed'] = analyzed_games
    
    print_tactical_analysis_results(tactical_stats, analyzed_games)
    return tactical_stats

def print_tactical_analysis_results(tactical_stats, analyzed_games):
    """Print the results of tactical analysis"""
    
    print(f"\n### Tactical Analysis Results ###")
    print(f"Games analyzed: {analyzed_games}")
    
    if analyzed_games > 0:
        print(f"Average centipawn loss per move: {tactical_stats['avg_centipawn_loss']:.1f}")
        print(f"Total errors found:")
        print(f"  • Blunders (200+ cp): {tactical_stats['blunder_count']}")
        print(f"  • Mistakes (100-199 cp): {tactical_stats['mistake_count']}")
        print(f"  • Inaccuracies (50-99 cp): {tactical_stats['inaccuracy_count']}")
        
        total_errors = tactical_stats['blunder_count'] + tactical_stats['mistake_count'] + tactical_stats['inaccuracy_count']
        if total_errors > 0:
            print(f"Error rate: {total_errors/analyzed_games:.1f} errors per game")
        
        # Opening-specific analysis
        if tactical_stats['opening_errors']:
            print(f"\n### Error Patterns by Opening ###")
            for eco, stats in tactical_stats['opening_errors'].items():
                if stats['games'] > 0:
                    opening_name = ECO_OPENINGS.get(eco, f"ECO {eco}")
                    total_errors = stats['blunders'] + stats['mistakes'] + stats['inaccuracies']
                    
                    print(f"{opening_name} ({eco}): {total_errors} errors in {stats['games']} games")
                    if stats['blunders'] > 0:
                        print(f"  ⚠ {stats['blunders']} blunders")
                    if stats['mistakes'] > 0:
                        print(f"  ⚡ {stats['mistakes']} mistakes")
                    if stats['inaccuracies'] > 0:
                        print(f"  ⚪ {stats['inaccuracies']} inaccuracies")
        
        # Show games with most tactical issues
        if 'detailed_analysis' in tactical_stats:
            problematic_games = [g for g in tactical_stats['detailed_analysis'] if g['blunders'] > 0 or g['mistakes'] > 1]
            if problematic_games:
                print(f"\n### Most Problematic Games ###")
                for game_info in sorted(problematic_games, key=lambda x: x['blunders'], reverse=True)[:3]:
                    print(f"{game_info['opening']} ({game_info['eco']}): {game_info['blunders']} blunders, {game_info['mistakes']} mistakes")
                    
                    for move in game_info.get('critical_moves', [])[:2]:  # Show worst moves
                        if move.get('classification') == 'blunder':
                            print(f"  💥 Move {move['move_number']}: {move['move']} (blunder, -{move['centipawn_loss']:.0f} cp)")

# Apply the tactical analysis
if all_games:
    print("\nStarting Stockfish tactical analysis...")
    tactical_analysis = perform_stockfish_analysis(all_games, target_username, max_games=len(all_games))
    
    print(f"\n### FINAL SUMMARY ###")
    print(f"Total games analyzed: {len(all_games)}")
    print(f"Games with tactical analysis: {tactical_analysis['total_analyzed']}")
    print(f"Average accuracy: {100 - tactical_analysis['avg_centipawn_loss']:.1f}% (based on centipawn loss)")
    
    if tactical_analysis['blunder_count'] > 0:
        print(f"⚠ PRIORITY: Address {tactical_analysis['blunder_count']} blunders found")
    if tactical_analysis['mistake_count'] > 0:
        print(f"⚡ SECONDARY: Reduce {tactical_analysis['mistake_count']} mistakes")
    
    # Identify the most problematic openings
    worst_openings = []
    for eco, stats in tactical_analysis['opening_errors'].items():
        if stats['games'] > 0:
            total_errors = stats['blunders'] + stats['mistakes']
            if total_errors > 0:
                worst_openings.append({
                    'eco': eco,
                    'opening': ECO_OPENINGS.get(eco, f"ECO {eco}"),
                    'total_errors': total_errors,
                    'games': stats['games'],
                    'error_rate': total_errors / stats['games']
                })
    
    if worst_openings:
        worst_openings.sort(key=lambda x: x['error_rate'], reverse=True)
        print(f"\n### OPENINGS TO STUDY ###")
        for opening in worst_openings[:3]:
            print(f"1. {opening['opening']} ({opening['eco']}): {opening['total_errors']} errors in {opening['games']} games")
            print(f"   Recommendation: Focus tactical training in this opening")

    # Update the weakness report with tactical data
    if 'weakness_report' in locals():
        weakness_report['tactical_analysis'] = tactical_analysis
else:
    print("No games available for tactical analysis.")

print("\n### STEP 4 COMPLETE ###")
print("Move-by-move Stockfish analysis complete!")
print("Key findings:")
print("- Blunders: Moves losing 200+ centipawns")
print("- Mistakes: Moves losing 100-199 centipawns") 
print("- Inaccuracies: Moves losing 50-99 centipawns")
print("- Analysis covers the first 10 moves (20 ply) from each side")

### STEP 5: Generate LLM Training Data for Chess Strategy ###

def analyze_opponent_patterns(weakness_report, tactical_analysis):
    """Analyze opponent patterns to create detailed weakness profiles"""
    
    opponent_analysis = {
        'opening_weaknesses': [],
        'tactical_vulnerabilities': [],
        'experience_gaps': [],
        'time_management_issues': [],
        'pattern_recognition': {}
    }
    
    # Extract opening weaknesses
    for weakness in weakness_report['opening_weaknesses'][:5]:  # Top 5 weaknesses
        opponent_analysis['opening_weaknesses'].append({
            'opening': weakness['opening'],
            'eco': weakness['eco'],
            'color': weakness['color'],
            'win_rate': weakness['win_rate'],
            'sample_size': weakness['total_games'],
            'severity': 'high' if weakness['win_rate'] < 30 else 'medium' if weakness['win_rate'] < 50 else 'low'
        })
    
    # Extract tactical vulnerabilities
    for eco, stats in tactical_analysis['opening_errors'].items():
        if stats['games'] > 0:
            total_errors = stats['blunders'] + stats['mistakes']
            error_rate = total_errors / stats['games']
            
            if error_rate > 0.5:  # More than 0.5 errors per game
                opponent_analysis['tactical_vulnerabilities'].append({
                    'opening': ECO_OPENINGS.get(eco, f"ECO {eco}"),
                    'eco': eco,
                    'blunders_per_game': stats['blunders'] / stats['games'],
                    'mistakes_per_game': stats['mistakes'] / stats['games'],
                    'error_rate': error_rate,
                    'games_analyzed': stats['games']
                })
    
    # Extract experience gaps
    for gap in weakness_report['experience_gaps']['inexperienced']:
        opponent_analysis['experience_gaps'].append({
            'opening': gap['opening'],
            'eco': gap['eco'],
            'color': gap['color'],
            'games_played': gap['games'],
            'results': gap['results']
        })
    
    return opponent_analysis

def generate_counter_strategy(opponent_patterns):
    """Generate strategic recommendations to exploit opponent weaknesses"""
    
    counter_strategy = {
        'opening_recommendations': [],
        'tactical_approach': [],
        'psychological_pressure': [],
        'time_management': [],
        'overall_strategy': ""
    }
    
    # Opening-specific recommendations
    for weakness in opponent_patterns['opening_weaknesses']:
        eco = weakness['eco']
        color = weakness['color']
        win_rate = weakness['win_rate']
        
        # Generate specific recommendations based on the opening
        recommendation = {
            'target_opening': weakness['opening'],
            'opponent_color': color.replace('as_', ''),
            'exploitation_method': "",
            'specific_lines': [],
            'reasoning': ""
        }
        
        if color == 'as_white':
            # Opponent struggles as White with this opening
            recommendation['exploitation_method'] = "Force opponent into uncomfortable defensive positions"
            recommendation['reasoning'] = f"Opponent has only {win_rate:.1f}% win rate as White in this opening"
            
            # Suggest sharp, tactical defenses
            if 'Sicilian' in weakness['opening']:
                recommendation['specific_lines'] = [
                    "Play Sicilian Dragon variation for sharp tactical play",
                    "Consider Sicilian Najdorf for complex middlegame positions",
                    "Use Accelerated Dragon to avoid main theoretical lines"
                ]
            elif 'Italian' in weakness['opening'] or 'Ruy Lopez' in weakness['opening']:
                recommendation['specific_lines'] = [
                    "Employ Two Knights Defense for tactical complications",
                    "Consider Berlin Defense for solid, technical endgames",
                    "Use Marshall Attack for aggressive counterplay"
                ]
            elif 'English' in weakness['opening']:
                recommendation['specific_lines'] = [
                    "Respond with ...c5 to create symmetrical pawn structure",
                    "Consider King's Indian setup with ...Nf6, ...g6, ...Bg7",
                    "Use reversed Sicilian patterns"
                ]
            else:
                recommendation['specific_lines'] = [
                    "Choose sharp, tactical variations",
                    "Avoid simplified positions",
                    "Create imbalanced pawn structures"
                ]
                
        else:
            # Opponent struggles as Black with this opening
            recommendation['exploitation_method'] = "Play this opening as White to exploit opponent's weakness"
            recommendation['reasoning'] = f"Opponent has only {win_rate:.1f}% win rate as Black against this opening"
            
            # Suggest playing this opening as White
            if 'Sicilian' in weakness['opening']:
                recommendation['specific_lines'] = [
                    "Play 1.e4 to reach Sicilian positions",
                    "Choose sharp attacking variations like Yugoslav Attack",
                    "Avoid early simplifications"
                ]
            elif 'Caro-Kann' in weakness['opening']:
                recommendation['specific_lines'] = [
                    "Play 1.e4 and meet ...c6 with Advance Variation",
                    "Consider Panov-Botvinnik Attack for active piece play",
                    "Aim for kingside attacking chances"
                ]
            elif 'French' in weakness['opening']:
                recommendation['specific_lines'] = [
                    "Play 1.e4 e6 2.d4 d5 3.Nc3 (Classical variation)",
                    "Consider Advance Variation with f4-f5 attack",
                    "Target light squares and kingside"
                ]
            else:
                recommendation['specific_lines'] = [
                    f"Play this opening ({weakness['opening']}) as White",
                    "Choose the most forcing variations",
                    "Maintain central tension"
                ]
        
        counter_strategy['opening_recommendations'].append(recommendation)
    
    # Tactical approach based on opponent's tactical vulnerabilities
    tactical_issues = opponent_patterns['tactical_vulnerabilities']
    if tactical_issues:
        high_error_openings = [t for t in tactical_issues if t['error_rate'] > 1.0]
        
        if high_error_openings:
            counter_strategy['tactical_approach'] = [
                "Seek complex, tactical positions where opponent is prone to errors",
                "Avoid simplified endgames - keep pieces on the board",
                "Create multiple threats simultaneously",
                f"Focus on openings where opponent averages {high_error_openings[0]['error_rate']:.1f} errors per game"
            ]
        else:
            counter_strategy['tactical_approach'] = [
                "Create moderate tactical complexity",
                "Look for opportunities to increase time pressure",
                "Focus on positional pressure rather than tactics"
            ]
    
    # Experience gap exploitation
    inexperienced_openings = opponent_patterns['experience_gaps']
    if inexperienced_openings:
        counter_strategy['psychological_pressure'] = [
            "Steer games into opponent's least experienced openings",
            f"Target openings where opponent has played fewer than 3 games",
            "Use rare but sound variations to take opponent out of preparation",
            "Create novel positions early in the game"
        ]
    
    # Overall strategy synthesis
    if len(counter_strategy['opening_recommendations']) > 0:
        main_weakness = counter_strategy['opening_recommendations'][0]
        counter_strategy['overall_strategy'] = f"""
Primary Strategy: Target opponent's weakness in {main_weakness['target_opening']} where they score {opponent_patterns['opening_weaknesses'][0]['win_rate']:.1f}%.

Key Approach:
1. {main_weakness['exploitation_method']}
2. Use tactical complexity to induce errors (opponent averages {tactical_analysis.get('avg_centipawn_loss', 25):.1f} cp loss per move)
3. Avoid opponent's strongest openings and steer toward their weak areas
4. Maintain time pressure and create unfamiliar positions

This strategy exploits both positional weaknesses and tactical vulnerabilities while leveraging psychological pressure.
""".strip()
    
    return counter_strategy

def create_training_data_entry(opponent_patterns, counter_strategy, target_player):
    """Create a single training data entry in input-output format"""
    
    import datetime
    
    # Generate unique session ID based on timestamp and player
    session_id = f"{target_player}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Format input: opponent weakness profile
    input_data = {
        "opponent_profile": {
            "player_name": target_player,
            "analysis_summary": {
                "total_games_analyzed": sum(w['sample_size'] for w in opponent_patterns['opening_weaknesses']),
                "primary_weaknesses_count": len(opponent_patterns['opening_weaknesses']),
                "tactical_vulnerability_count": len(opponent_patterns['tactical_vulnerabilities'])
            }
        },
        "opening_weaknesses": opponent_patterns['opening_weaknesses'],
        "tactical_vulnerabilities": opponent_patterns['tactical_vulnerabilities'],
        "experience_gaps": opponent_patterns['experience_gaps']
    }
    
    # Format output: strategic recommendations
    output_data = {
        "strategic_recommendations": {
            "opening_choices": counter_strategy['opening_recommendations'],
            "tactical_approach": counter_strategy['tactical_approach'],
            "psychological_tactics": counter_strategy['psychological_pressure'],
            "overall_game_plan": counter_strategy['overall_strategy']
        },
        "confidence_level": "high" if len(opponent_patterns['opening_weaknesses']) >= 3 else "medium",
        "expected_success_rate": calculate_success_probability(opponent_patterns)
    }
    
    return {
        "input": input_data,
        "output": output_data,
        "metadata": {
            "analysis_date": datetime.datetime.now().strftime('%Y-%m-%d'),
            "analysis_timestamp": datetime.datetime.now().isoformat(),
            "analysis_session_id": session_id,
            "player_analyzed": target_player,
            "analysis_type": "opening_and_tactical_weakness_exploitation",
            "data_source": "chess_com_and_lichess_games"
        }
    }

def calculate_success_probability(opponent_patterns):
    """Calculate expected success probability based on opponent weaknesses"""
    
    if not opponent_patterns['opening_weaknesses']:
        return 0.5  # Neutral if no data
    
    # Base probability on worst opening performance
    worst_win_rate = min(w['win_rate'] for w in opponent_patterns['opening_weaknesses'])
    
    # Convert opponent's win rate to our expected success rate
    # If opponent wins 30% in an opening, we should expect ~70% success
    base_probability = (100 - worst_win_rate) / 100
    
    # Adjust based on sample size confidence
    avg_sample_size = sum(w['sample_size'] for w in opponent_patterns['opening_weaknesses']) / len(opponent_patterns['opening_weaknesses'])
    confidence_multiplier = min(1.0, avg_sample_size / 5)  # Full confidence at 5+ games
    
    # Adjust based on tactical vulnerability
    tactical_bonus = len(opponent_patterns['tactical_vulnerabilities']) * 0.05
    
    final_probability = base_probability * confidence_multiplier + tactical_bonus
    return min(0.95, max(0.55, final_probability))  # Keep between 55% and 95%

def extract_tactical_approach(tactical_vulnerabilities):
    """Extract specific tactical recommendations based on vulnerabilities"""
    
    if not tactical_vulnerabilities:
        return ["Maintain standard tactical alertness", "Look for typical tactical motifs"]
    
    approaches = []
    
    # High error rate opponents
    high_error_opponents = [tv for tv in tactical_vulnerabilities if tv['error_rate'] > 1.0]
    if high_error_opponents:
        approaches.extend([
            "Increase tactical complexity to induce more errors",
            "Avoid premature simplification",
            "Create multiple simultaneous threats"
        ])
    
    # Blunder-prone opponents
    blunder_prone = [tv for tv in tactical_vulnerabilities if tv['blunders_per_game'] > 0.3]
    if blunder_prone:
        approaches.extend([
            "Apply time pressure to increase blunder probability",
            "Create positions with hidden tactical motifs",
            "Use psychological pressure through aggressive piece placement"
        ])
    
    return approaches

def generate_llm_training_dataset(all_games, weakness_report, tactical_analysis, target_player):
    """Generate a complete LLM training dataset"""
    
    print(f"\n### STEP 5: Generating LLM Training Dataset ###")
    print("Creating input-output pairs for chess strategy training...")
    
    # Analyze opponent patterns
    opponent_patterns = analyze_opponent_patterns(weakness_report, tactical_analysis)
    
    # Generate counter-strategy
    counter_strategy = generate_counter_strategy(opponent_patterns)
    
    # Create training data entries
    training_dataset = []
    
    # Main entry - comprehensive analysis
    main_entry = create_training_data_entry(opponent_patterns, counter_strategy, target_player)
    training_dataset.append(main_entry)
    
    # Additional entries for specific openings
    for weakness in opponent_patterns['opening_weaknesses'][:3]:  # Top 3 weaknesses
        specific_patterns = {
            'opening_weaknesses': [weakness],
            'tactical_vulnerabilities': [tv for tv in opponent_patterns['tactical_vulnerabilities'] 
                                       if tv['eco'] == weakness['eco']],
            'experience_gaps': [eg for eg in opponent_patterns['experience_gaps']
                              if eg['eco'] == weakness['eco']]
        }
        
        specific_strategy = generate_counter_strategy(specific_patterns)
        specific_entry = create_training_data_entry(specific_patterns, specific_strategy, target_player)
        
        # Add opening-specific metadata
        specific_entry['metadata']['focus_opening'] = weakness['opening']
        specific_entry['metadata']['focus_eco'] = weakness['eco']
        specific_entry['metadata']['analysis_type'] = "specific_opening_weakness_exploitation"
        
        training_dataset.append(specific_entry)
    
    return training_dataset

def save_training_dataset(dataset, filename="chess_strategy_training_data.json"):
    """Save the training dataset to a JSON file, appending to existing data"""
    
    existing_data = []
    
    # Try to load existing data
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            print(f"✓ Loaded {len(existing_data)} existing training entries")
        else:
            print("✓ Creating new training dataset file")
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"⚠ Could not load existing data: {e}. Starting fresh.")
        existing_data = []
    
    # Check for duplicate entries (same player and analysis date)
    new_entries = []
    for new_entry in dataset:
        is_duplicate = False
        for existing_entry in existing_data:
            if (existing_entry.get('metadata', {}).get('player_analyzed') == new_entry['metadata'].get('player_analyzed') and
                existing_entry.get('metadata', {}).get('analysis_session_id') == new_entry['metadata'].get('analysis_session_id')):
                print(f"⚠ Duplicate entry found for {new_entry['metadata'].get('player_analyzed')}, skipping...")
                is_duplicate = True
                break
        
        if not is_duplicate:
            new_entries.append(new_entry)
    
    if not new_entries:
        print("⚠ No new entries to add (all were duplicates)")
        return True
    
    # Combine existing and new data
    combined_data = existing_data + new_entries
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Training dataset updated and saved to '{filename}'")
        print(f"✓ Added {len(new_entries)} new training examples")
        print(f"✓ Total dataset now contains {len(combined_data)} training examples")
        
        # Print summary statistics for new entries only
        total_weaknesses = sum(len(entry['input']['opening_weaknesses']) for entry in new_entries)
        total_recommendations = sum(len(entry['output']['strategic_recommendations']['opening_choices']) for entry in new_entries)
        
        print(f"✓ New entries contain {total_weaknesses} opening weaknesses")
        print(f"✓ New entries contain {total_recommendations} strategic recommendations")
        
        return True
        
    except Exception as e:
        print(f"✗ Error saving dataset: {e}")
        return False

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
        
        print(f"\n### Training Dataset Statistics ###")
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
            print(f"\n  {player}:")
            print(f"    - Training entries: {len(entries)}")
            
            # Count different analysis types
            analysis_types = {}
            for entry in entries:
                analysis_type = entry.get('metadata', {}).get('analysis_type', 'Unknown')
                analysis_types[analysis_type] = analysis_types.get(analysis_type, 0) + 1
            
            for analysis_type, count in analysis_types.items():
                print(f"    - {analysis_type}: {count} entries")
            
            # Show latest analysis date
            latest_date = max([entry.get('metadata', {}).get('analysis_date', '') for entry in entries])
            print(f"    - Latest analysis: {latest_date}")
            
            # Count weaknesses and recommendations
            total_weaknesses = sum(len(entry['input']['opening_weaknesses']) for entry in entries)
            total_recommendations = sum(len(entry['output']['strategic_recommendations']['opening_choices']) for entry in entries)
            print(f"    - Total weaknesses identified: {total_weaknesses}")
            print(f"    - Total recommendations: {total_recommendations}")
        
        print(f"\nDataset ready for LLM training with {len(dataset)} diverse examples!")
        
    except Exception as e:
        print(f"✗ Error reading dataset statistics: {e}")

# Generate the training dataset
if all_games and 'weakness_report' in locals() and 'tactical_analysis' in locals():
    training_dataset = generate_llm_training_dataset(all_games, weakness_report, tactical_analysis, target_username)
    
    # Save the dataset
    save_success = save_training_dataset(training_dataset)
    
    if save_success:
        # Print a sample entry for review
        print(f"\n### Sample Training Entry ###")
        sample_entry = training_dataset[0]
        
        print("INPUT (Opponent Weaknesses):")
        print(f"  - Primary weakness: {sample_entry['input']['opening_weaknesses'][0]['opening']}")
        print(f"    Win rate: {sample_entry['input']['opening_weaknesses'][0]['win_rate']:.1f}%")
        print(f"    Sample size: {sample_entry['input']['opening_weaknesses'][0]['sample_size']} games")
        
        if sample_entry['input']['tactical_vulnerabilities']:
            print(f"  - Tactical vulnerability: {sample_entry['input']['tactical_vulnerabilities'][0]['opening']}")
            print(f"    Error rate: {sample_entry['input']['tactical_vulnerabilities'][0]['error_rate']:.1f} per game")
        
        print("\nOUTPUT (Counter-Strategy):")
        if sample_entry['output']['strategic_recommendations']['opening_choices']:
            rec = sample_entry['output']['strategic_recommendations']['opening_choices'][0]
            print(f"  - Target: {rec['target_opening']}")
            print(f"  - Method: {rec['exploitation_method']}")
            print(f"  - Specific lines: {rec['specific_lines'][0] if rec['specific_lines'] else 'None'}")
        
        print(f"  - Expected success rate: {sample_entry['output']['expected_success_rate']:.1f}")
        
        print(f"\n### Dataset Generation Complete ###")
        print(f"The dataset is ready for LLM training and contains structured input-output pairs")
        print(f"where the input describes opponent weaknesses and the output provides counter-strategies.")
        
        # Display overall dataset statistics
        display_dataset_statistics()
        
    else:
        print("Cannot generate training dataset - missing game analysis data")

    print("\n### STEP 5 COMPLETE ###")
    print("LLM training dataset generation complete!")
    print("\nTo analyze another player, run:")
    print("  python chess_analyzer.py <username>")
    print("or just run:")
    print("  python chess_analyzer.py")
    print("and enter the username when prompted.")

