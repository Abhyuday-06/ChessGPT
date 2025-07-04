import requests
import json
import time
from pathlib import Path

### STEP 1: Fetch Games from Chess.com and Lichess ###



user = "hikaru"  # Using a known Chess.com player

# Fetches the games from chess.com API with error handling
try:
    # Add headers to make the request look more like a browser
    headers = {
        'User-Agent': 'ChessGPT/1.0 (Educational chess analysis tool)',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    # Add a small delay to be respectful to the API
    import time
    time.sleep(1)
    
    response = requests.get(f"https://api.chess.com/pub/player/{user}/games/archives", headers=headers)
    response.raise_for_status()  # Raises an HTTPError for bad responses
    
    if response.text.strip() == "":
        print(f"Empty response for user {user}")
    else:
        archives = response.json()
        print(f"Found {len(archives['archives'])} archive months for {user}")
        
        # Get the most recent archive to avoid too much data
        if archives["archives"]:
            # Try the last few months to find games
            for i in range(1, min(4, len(archives["archives"]) + 1)):
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

#  NEED A DATABASE TO STORE THE PGN DATA

### STEP 2: Parse Games and Extract Openings ###

import chess.pgn
import io
from collections import defaultdict

# ECO code to opening name mapping for better identification
ECO_OPENINGS = {
    'A01': 'Nimzo-Larsen Attack',
    'A44': 'Old Benoni Defense',
    'B01': 'Scandinavian Defense',
    'B06': 'Modern Defense',
    'B12': 'Caro-Kann Defense',
    'B15': 'Caro-Kann Defense: Forgacs Variation',
    'B22': 'Sicilian Defense: Alapin Variation',
    'B23': 'Sicilian Defense: Closed',
    'C28': 'Vienna Game',
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
target_username = "Hikaru"  # Target player to analyze

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

else:
    print("No games found to analyze. Make sure PGN files exist.")
"""

### STEP 3: Identify Weakness Signals by Opening

# 1) Poor Results using results from the games
# 2) Low experience of openings with the help of ECO codes
# 3) Tactical mistakes using engine analysis
# 4) Evaluation trends using engine analysis

# Expected output: Opponent has played 50 games of the Sicilian Defense (ECO B20-B99) as Black and lost 40% of them. Many losses involve a critical error on move 5 in the Najdorf. They have only 3 games in the Ruy Lopez.” 


### STEP 4: Stockfish Evaluation for Move-by-Move Analysis

import chess.engine
import platform
import os
from pathlib import Path

def download_stockfish():
    """Download Stockfish if not available"""
    import urllib.request
    import zipfile
    
    system = platform.system().lower()
    stockfish_path = None
    
    if system == "windows":
        stockfish_url = "https://github.com/official-stockfish/Stockfish/releases/download/sf_16.1/stockfish-windows-x86-64-avx2.zip"
        stockfish_path = "stockfish/stockfish.exe"
    elif system == "darwin":  # macOS
        stockfish_url = "https://github.com/official-stockfish/Stockfish/releases/download/sf_16.1/stockfish-macos-x86-64-modern.zip" 
        stockfish_path = "stockfish/stockfish"
    else:  # Linux
        stockfish_url = "https://github.com/official-stockfish/Stockfish/releases/download/sf_16.1/stockfish-ubuntu-x86-64-avx2.zip"
        stockfish_path = "stockfish/stockfish"
    
    if not os.path.exists(stockfish_path):
        print("Downloading Stockfish engine...")
        try:
            urllib.request.urlretrieve(stockfish_url, "stockfish.zip")
            with zipfile.ZipFile("stockfish.zip", 'r') as zip_ref:
                zip_ref.extractall(".")
            os.remove("stockfish.zip")
            print("Stockfish downloaded successfully!")
        except Exception as e:
            print(f"Failed to download Stockfish: {e}")
            return None
    
    return stockfish_path

def get_stockfish_engine():
    """Get a working Stockfish engine instance"""
    # Try to find Stockfish in common locations
    stockfish_paths = [
        "stockfish.exe",           # Current directory (Windows)
        "stockfish",               # Current directory (Unix)
        "/usr/local/bin/stockfish", # Common install location
        "/opt/homebrew/bin/stockfish", # Homebrew on M1 Mac
        "C:\\Program Files\\Stockfish\\stockfish.exe",  # Windows install
        str(Path.home() / "stockfish" / "stockfish.exe"),  # User install Windows
        str(Path.home() / "stockfish" / "stockfish"),      # User install Unix
    ]
    
    # First, try to use the stockfish package if available
    try:
        # Install stockfish via pip if needed
        import subprocess
        import sys
        
        # Check if stockfish package is available
        try:
            import stockfish
        except ImportError:
            print("Installing stockfish package...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "stockfish"])
            import stockfish
        
        # Try to get the stockfish binary path from the package
        from stockfish import Stockfish
        sf = Stockfish()
        
        # Get the stockfish binary path 
        stockfish_path = sf._stockfish.get_stockfish_path() if hasattr(sf._stockfish, 'get_stockfish_path') else None
        
        if stockfish_path and os.path.exists(stockfish_path):
            try:
                engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
                return engine
            except:
                pass
                
    except Exception as e:
        print(f"Stockfish package approach failed: {e}")
    
    # Try system paths
    for path in stockfish_paths:
        try:
            if os.path.exists(path):
                engine = chess.engine.SimpleEngine.popen_uci(path)
                print(f"Found Stockfish at: {path}")
                return engine
        except Exception as e:
            continue
    
    # Try to download Stockfish
    print("Stockfish not found locally. Attempting to download...")
    downloaded_path = download_stockfish()
    if downloaded_path:
        try:
            engine = chess.engine.SimpleEngine.popen_uci(downloaded_path)
            print(f"Successfully downloaded and started Stockfish: {downloaded_path}")
            return engine
        except Exception as e:
            print(f"Failed to start downloaded Stockfish: {e}")
    
    print("Could not find or download Stockfish. Analysis will be limited.")
    return None

def analyze_position_with_stockfish(board, engine, depth=15):
    """Analyze a position with Stockfish"""
    try:
        info = engine.analyse(board, chess.engine.Limit(depth=depth))
        score = info["score"].relative.score(mate_score=10000)
        return score
    except Exception as e:
        print(f"Engine analysis error: {e}")
        return 0

def analyze_game_moves(game, target_player, max_ply=20):
    """
    Analyze the first max_ply moves of a game to identify blunders, mistakes, and inaccuracies.
    max_ply represents half-moves (ply), so 20 ply = 10 moves from each side.
    """
    
    engine = get_stockfish_engine()
    if not engine:
        print("No Stockfish engine available for analysis")
        return None
    
    try:
        analysis = {
            'blunders': [],      # Moves losing 200+ centipawns
            'mistakes': [],      # Moves losing 100-199 centipawns  
            'inaccuracies': [],  # Moves losing 50-99 centipawns
            'evaluations': [],   # Position evaluations
            'target_color': None,
            'avg_centipawn_loss': 0,
            'move_classifications': []
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
            engine.quit()
            return analysis
        
        board = chess.Board()
        ply_count = 0
        prev_score = None
        total_centipawn_loss = 0
        target_moves = 0
        
        # Get initial position evaluation
        prev_score = analyze_position_with_stockfish(board, engine)
        
        for move in game.mainline_moves():
            if ply_count >= max_ply:
                break
                
            # Make the move
            board.push(move)
            ply_count += 1
            
            # Get evaluation after the move
            current_score = analyze_position_with_stockfish(board, engine)
            
            # Determine whose move this was
            move_color = 'white' if ply_count % 2 == 1 else 'black'
            is_target_move = (analysis['target_color'] == move_color)
            
            # Calculate centipawn loss from the moving player's perspective
            if move_color == 'white':
                # For white, a decrease in score is bad
                centipawn_loss = max(0, prev_score - (-current_score))
            else:
                # For black, an increase in score (from white's perspective) is bad for black
                centipawn_loss = max(0, -prev_score - current_score)
            
            move_info = {
                'ply': ply_count,
                'move_number': (ply_count + 1) // 2,
                'move': move.uci(),
                'move_san': board.san(move) if ply_count < len(list(game.mainline_moves())) else move.uci(),
                'color': move_color,
                'is_target_player': is_target_move,
                'score_before': prev_score,
                'score_after': current_score,
                'centipawn_loss': centipawn_loss,
                'fen': board.fen()
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
                
                analysis['move_classifications'].append(move_info)
            
            prev_score = current_score
        
        # Calculate average centipawn loss
        if target_moves > 0:
            analysis['avg_centipawn_loss'] = total_centipawn_loss / target_moves
        
        engine.quit()
        return analysis
        
    except Exception as e:
        print(f"Game analysis error: {e}")
        if engine:
            engine.quit()
        return None

def perform_tactical_analysis(games, target_player, max_games=10):
    """Perform Stockfish analysis on multiple games to identify patterns"""
    
    print(f"\n### STEP 4: Stockfish Engine Analysis ###")
    print(f"Analyzing up to {max_games} games for tactical patterns...")
    
    tactical_stats = {
        'total_analyzed': 0,
        'blunder_count': 0,
        'mistake_count': 0,
        'inaccuracy_count': 0,
        'games_with_blunders': 0,
        'opening_blunders': defaultdict(list),
        'opening_mistakes': defaultdict(list),
        'avg_centipawn_loss': 0,
        'tactical_weaknesses': [],
        'best_openings': [],  # Openings with low error rates
        'worst_openings': []  # Openings with high error rates
    }
    
    total_centipawn_loss = 0
    analyzed_games = 0
    
    # Analyze a subset of games to avoid long processing time
    games_to_analyze = min(max_games, len(games))
    
    for i, game in enumerate(games[:games_to_analyze]):
        eco = game.headers.get('ECO', 'Unknown')
        opening_name = ECO_OPENINGS.get(eco, f"ECO {eco}")
        
        print(f"  [{i+1}/{games_to_analyze}] Analyzing: {opening_name} ({eco})")
        
        # Analyze this game
        game_analysis = analyze_game_moves(game, target_player, max_ply=20)
        
        if game_analysis and game_analysis['target_color']:
            analyzed_games += 1
            tactical_stats['total_analyzed'] += 1
            
            # Count tactical errors
            blunders = len(game_analysis['blunders'])
            mistakes = len(game_analysis['mistakes'])
            inaccuracies = len(game_analysis['inaccuracies'])
            
            tactical_stats['blunder_count'] += blunders
            tactical_stats['mistake_count'] += mistakes
            tactical_stats['inaccuracy_count'] += inaccuracies
            
            if blunders > 0:
                tactical_stats['games_with_blunders'] += 1
                tactical_stats['opening_blunders'][eco].extend(game_analysis['blunders'])
            
            if mistakes > 0:
                tactical_stats['opening_mistakes'][eco].extend(game_analysis['mistakes'])
            
            total_centipawn_loss += game_analysis['avg_centipawn_loss']
            
            # Determine game result for target player
            white_player = game.headers.get("White", "").lower()
            target_lower = target_player.lower()
            result = game.headers.get('Result', '*')
            
            if target_lower in white_player:
                if result == '1-0':
                    game_result = 'win'
                elif result == '0-1':
                    game_result = 'loss'
                else:
                    game_result = 'draw'
            else:
                if result == '0-1':
                    game_result = 'win'
                elif result == '1-0':
                    game_result = 'loss'
                else:
                    game_result = 'draw'
            
            # Store detailed analysis for this opening
            opening_stats = {
                'eco': eco,
                'opening': opening_name,
                'blunders': blunders,
                'mistakes': mistakes,
                'inaccuracies': inaccuracies,
                'total_errors': blunders + mistakes + inaccuracies,
                'avg_centipawn_loss': game_analysis['avg_centipawn_loss'],
                'game_result': game_result,
                'target_color': game_analysis['target_color']
            }
            
            # Classify as tactical weakness if many errors
            if blunders > 0 or mistakes > 1 or game_analysis['avg_centipawn_loss'] > 25:
                tactical_stats['tactical_weaknesses'].append(opening_stats)
            else:
                tactical_stats['best_openings'].append(opening_stats)
        
        else:
            print(f"    Could not analyze this game (target player not found or engine error)")
    
    # Calculate averages
    if analyzed_games > 0:
        tactical_stats['avg_centipawn_loss'] = total_centipawn_loss / analyzed_games
    
    # Print detailed analysis results
    print(f"\n### Tactical Analysis Results ###")
    print(f"Games analyzed: {analyzed_games}")
    
    if analyzed_games > 0:
        print(f"Average centipawn loss per move: {tactical_stats['avg_centipawn_loss']:.1f}")
        print(f"Total blunders: {tactical_stats['blunder_count']}")
        print(f"Total mistakes: {tactical_stats['mistake_count']}")
        print(f"Total inaccuracies: {tactical_stats['inaccuracy_count']}")
        print(f"Games with blunders: {tactical_stats['games_with_blunders']}/{analyzed_games} ({tactical_stats['games_with_blunders']/analyzed_games*100:.1f}%)")
        
        # Analysis by opening
        if tactical_stats['opening_blunders']:
            print(f"\n### Blunder Patterns by Opening ###")
            for eco, blunder_list in tactical_stats['opening_blunders'].items():
                opening_name = ECO_OPENINGS.get(eco, f"ECO {eco}")
                print(f"\n{opening_name} ({eco}): {len(blunder_list)} blunders")
                
                # Show specific blunder details
                for i, blunder in enumerate(blunder_list[:3]):  # Show first 3 blunders
                    print(f"  Blunder {i+1}: Move {blunder['move_number']}.{blunder['move_san'] if 'move_san' in blunder else blunder['move']} "
                          f"({blunder['color']}) - Lost {blunder['centipawn_loss']:.0f} centipawns")
        
        # Tactical weakness summary
        if tactical_stats['tactical_weaknesses']:
            print(f"\n### Openings with Tactical Issues ###")
            for weakness in sorted(tactical_stats['tactical_weaknesses'], 
                                 key=lambda x: x['total_errors'], reverse=True)[:5]:
                print(f"{weakness['opening']} ({weakness['eco']}) as {weakness['target_color'].title()}:")
                print(f"  Errors: {weakness['blunders']} blunders, {weakness['mistakes']} mistakes, {weakness['inaccuracies']} inaccuracies")
                print(f"  Average loss: {weakness['avg_centipawn_loss']:.1f} cp/move, Result: {weakness['game_result']}")
        
        # Best openings
        if tactical_stats['best_openings']:
            print(f"\n### Tactically Sound Openings ###")
            for good_opening in sorted(tactical_stats['best_openings'], 
                                     key=lambda x: x['avg_centipawn_loss'])[:3]:
                print(f"{good_opening['opening']} ({good_opening['eco']}) as {good_opening['target_color'].title()}:")
                print(f"  Clean play: {good_opening['avg_centipawn_loss']:.1f} cp/move average loss, Result: {good_opening['game_result']}")
    
    else:
        print("No games could be analyzed with Stockfish.")
    
    return tactical_stats

# Apply engine analysis to our parsed games
if all_games:
    print("\nStarting comprehensive Stockfish analysis...")
    tactical_analysis = perform_tactical_analysis(all_games, target_username, max_games=5)
    
    # Integrate tactical analysis with existing weakness analysis
    if 'weakness_report' in locals():
        weakness_report['tactical_analysis'] = tactical_analysis
        
        print(f"\n### INTEGRATED ANALYSIS SUMMARY ###")
        print(f"Total games analyzed: {len(all_games)}")
        print(f"Games with tactical analysis: {tactical_analysis['total_analyzed']}")
        print(f"Opening weaknesses identified: {len(weakness_report['opening_weaknesses'])}")
        print(f"Tactical patterns detected: {tactical_analysis['blunder_count']} blunders, {tactical_analysis['mistake_count']} mistakes")
        
        # Combine opening and tactical weaknesses
        combined_weaknesses = []
        for opening_weakness in weakness_report['opening_weaknesses'][:5]:
            eco = opening_weakness['eco']
            # Find corresponding tactical data
            tactical_data = next((t for t in tactical_analysis['tactical_weaknesses'] if t['eco'] == eco), None)
            
            if tactical_data:
                opening_weakness['tactical_errors'] = tactical_data['total_errors']
                opening_weakness['avg_centipawn_loss'] = tactical_data['avg_centipawn_loss']
                opening_weakness['combined_score'] = opening_weakness['weakness_score'] + tactical_data['total_errors'] * 10
            else:
                opening_weakness['tactical_errors'] = 0
                opening_weakness['avg_centipawn_loss'] = 0
                opening_weakness['combined_score'] = opening_weakness['weakness_score']
            
            combined_weaknesses.append(opening_weakness)
        
        # Sort by combined score
        combined_weaknesses.sort(key=lambda x: x['combined_score'], reverse=True)
        
        print(f"\n### TOP COMBINED WEAKNESSES (Results + Tactics) ###")
        for i, weakness in enumerate(combined_weaknesses[:3], 1):
            print(f"{i}. {weakness['opening']} ({weakness['eco']}) as {weakness['color'].replace('as_', '').title()}")
            print(f"   Win Rate: {weakness['win_rate']:.1f}% ({weakness['wins']}-{weakness['losses']}-{weakness.get('draws', 0)})")
            print(f"   Tactical: {weakness['tactical_errors']} errors, {weakness['avg_centipawn_loss']:.1f} cp/move")
            print(f"   Combined Score: {weakness['combined_score']:.1f}/100")
            print()
    
else:
    print("No games available for tactical analysis.")
### STEP 3: Identify Weakness Signals by Opening

import chess
import chess.pgn

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
    quick_loss_count = sum(1 for loss in patterns['quick_losses'] 
                          if loss['eco'] == eco_data[0]['game'].headers.get('ECO'))
    weakness_score += quick_loss_count * 15
    
    # Penalty for repetitive losses
    eco = eco_data[0]['game'].headers.get('ECO', 'Unknown')
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
    
    if patterns['repetitive_losses']:
        print(f"   Repetitive losses in same openings:")
        for eco, loss_games in patterns['repetitive_losses'].items():
            if len(loss_games) >= 2:
                opening_name = loss_games[0].headers.get('Opening', 'Unknown')
                print(f"   - {opening_name} ({eco}): {len(loss_games)} losses")
    
    print(f"\n4) Strategic Recommendations:")
    
    # Identify the top 3 most problematic openings
    top_problems = opening_weaknesses[:3]
    
    for i, problem in enumerate(top_problems):
        print(f"   Priority {i+1}: Avoid or improve {problem['opening']} as {problem['color'].replace('as_', '').title()}")
        
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
    print("No games available for weakness analysis.")rs = {
        'User-Agent': 'ChessGPT/1.0 (Educational chess analysis tool)',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    # Add a small delay to be respectful to the API
    import time
    time.sleep(1)
    
    response = requests.get(f"https://api.chess.com/pub/player/{user}/games/archives", headers=headers)
    response.raise_for_status()  # Raises an HTTPError for bad responses
    
    if response.text.strip() == "":
        print(f"Empty response for user {user}")
    else:
        archives = response.json()
        print(f"Found {len(archives['archives'])} archive months for {user}")
        
        # Get the most recent archive to avoid too much data
        if archives["archives"]:
            # Try the last few months to find games
            for i in range(1, min(4, len(archives["archives"]) + 1)):
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

#  NEED A DATABASE TO STORE THE PGN DATA

### STEP 2: Parse Games and Extract Openings ###

import chess.pgn
import io
from collections import defaultdict

# ECO code to opening name mapping for better identification
ECO_OPENINGS = {
    'A01': 'Nimzo-Larsen Attack',
    'A44': 'Old Benoni Defense',
    'B01': 'Scandinavian Defense',
    'B06': 'Modern Defense',
    'B12': 'Caro-Kann Defense',
    'B15': 'Caro-Kann Defense: Forgacs Variation',
    'B22': 'Sicilian Defense: Alapin Variation',
    'B23': 'Sicilian Defense: Closed',
    'C28': 'Vienna Game',
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
target_username = "Hikaru"  # Target player to analyze

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

else:
    print("No games found to analyze. Make sure PGN files exist.")
"""

### STEP 3: Identify Weakness Signals by Opening

# 1) Poor Results using results from the games
# 2) Low experience of openings with the help of ECO codes
# 3) Tactical mistakes using engine analysis
# 4) Evaluation trends using engine analysis

# Expected output: Opponent has played 50 games of the Sicilian Defense (ECO B20-B99) as Black and lost 40% of them. Many losses involve a critical error on move 5 in the Najdorf. They have only 3 games in the Ruy Lopez.” 


### STEP 4: Stockfish Evaluation for Move-by-Move Analysis

import chess.engine
import platform
import os
from pathlib import Path

def download_stockfish():
    """Download Stockfish if not available"""
    import urllib.request
    import zipfile
    
    system = platform.system().lower()
    stockfish_path = None
    
    if system == "windows":
        stockfish_url = "https://github.com/official-stockfish/Stockfish/releases/download/sf_16.1/stockfish-windows-x86-64-avx2.zip"
        stockfish_path = "stockfish/stockfish.exe"
    elif system == "darwin":  # macOS
        stockfish_url = "https://github.com/official-stockfish/Stockfish/releases/download/sf_16.1/stockfish-macos-x86-64-modern.zip" 
        stockfish_path = "stockfish/stockfish"
    else:  # Linux
        stockfish_url = "https://github.com/official-stockfish/Stockfish/releases/download/sf_16.1/stockfish-ubuntu-x86-64-avx2.zip"
        stockfish_path = "stockfish/stockfish"
    
    if not os.path.exists(stockfish_path):
        print("Downloading Stockfish engine...")
        try:
            urllib.request.urlretrieve(stockfish_url, "stockfish.zip")
            with zipfile.ZipFile("stockfish.zip", 'r') as zip_ref:
                zip_ref.extractall(".")
            os.remove("stockfish.zip")
            print("Stockfish downloaded successfully!")
        except Exception as e:
            print(f"Failed to download Stockfish: {e}")
            return None
    
    return stockfish_path

def get_stockfish_engine():
    """Get a working Stockfish engine instance"""
    # Try to find Stockfish in common locations
    stockfish_paths = [
        "stockfish.exe",           # Current directory (Windows)
        "stockfish",               # Current directory (Unix)
        "/usr/local/bin/stockfish", # Common install location
        "/opt/homebrew/bin/stockfish", # Homebrew on M1 Mac
        "C:\\Program Files\\Stockfish\\stockfish.exe",  # Windows install
        str(Path.home() / "stockfish" / "stockfish.exe"),  # User install Windows
        str(Path.home() / "stockfish" / "stockfish"),      # User install Unix
    ]
    
    # First, try to use the stockfish package if available
    try:
        # Install stockfish via pip if needed
        import subprocess
        import sys
        
        # Check if stockfish package is available
        try:
            import stockfish
        except ImportError:
            print("Installing stockfish package...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "stockfish"])
            import stockfish
        
        # Try to get the stockfish binary path from the package
        from stockfish import Stockfish
        sf = Stockfish()
        
        # Get the stockfish binary path 
        stockfish_path = sf._stockfish.get_stockfish_path() if hasattr(sf._stockfish, 'get_stockfish_path') else None
        
        if stockfish_path and os.path.exists(stockfish_path):
            try:
                engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
                return engine
            except:
                pass
                
    except Exception as e:
        print(f"Stockfish package approach failed: {e}")
    
    # Try system paths
    for path in stockfish_paths:
        try:
            if os.path.exists(path):
                engine = chess.engine.SimpleEngine.popen_uci(path)
                print(f"Found Stockfish at: {path}")
                return engine
        except Exception as e:
            continue
    
    # Try to download Stockfish
    print("Stockfish not found locally. Attempting to download...")
    downloaded_path = download_stockfish()
    if downloaded_path:
        try:
            engine = chess.engine.SimpleEngine.popen_uci(downloaded_path)
            print(f"Successfully downloaded and started Stockfish: {downloaded_path}")
            return engine
        except Exception as e:
            print(f"Failed to start downloaded Stockfish: {e}")
    
    print("Could not find or download Stockfish. Analysis will be limited.")
    return None

def analyze_position_with_stockfish(board, engine, depth=15):
    """Analyze a position with Stockfish"""
    try:
        info = engine.analyse(board, chess.engine.Limit(depth=depth))
        score = info["score"].relative.score(mate_score=10000)
        return score
    except Exception as e:
        print(f"Engine analysis error: {e}")
        return 0

def analyze_game_moves(game, target_player, max_ply=20):
    """
    Analyze the first max_ply moves of a game to identify blunders, mistakes, and inaccuracies.
    max_ply represents half-moves (ply), so 20 ply = 10 moves from each side.
    """
    
    engine = get_stockfish_engine()
    if not engine:
        print("No Stockfish engine available for analysis")
        return None
    
    try:
        analysis = {
            'blunders': [],      # Moves losing 200+ centipawns
            'mistakes': [],      # Moves losing 100-199 centipawns  
            'inaccuracies': [],  # Moves losing 50-99 centipawns
            'evaluations': [],   # Position evaluations
            'target_color': None,
            'avg_centipawn_loss': 0,
            'move_classifications': []
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
            engine.quit()
            return analysis
        
        board = chess.Board()
        ply_count = 0
        prev_score = None
        total_centipawn_loss = 0
        target_moves = 0
        
        # Get initial position evaluation
        prev_score = analyze_position_with_stockfish(board, engine)
        
        for move in game.mainline_moves():
            if ply_count >= max_ply:
                break
                
            # Make the move
            board.push(move)
            ply_count += 1
            
            # Get evaluation after the move
            current_score = analyze_position_with_stockfish(board, engine)
            
            # Determine whose move this was
            move_color = 'white' if ply_count % 2 == 1 else 'black'
            is_target_move = (analysis['target_color'] == move_color)
            
            # Calculate centipawn loss from the moving player's perspective
            if move_color == 'white':
                # For white, a decrease in score is bad
                centipawn_loss = max(0, prev_score - (-current_score))
            else:
                # For black, an increase in score (from white's perspective) is bad for black
                centipawn_loss = max(0, -prev_score - current_score)
            
            move_info = {
                'ply': ply_count,
                'move_number': (ply_count + 1) // 2,
                'move': move.uci(),
                'move_san': board.san(move) if ply_count < len(list(game.mainline_moves())) else move.uci(),
                'color': move_color,
                'is_target_player': is_target_move,
                'score_before': prev_score,
                'score_after': current_score,
                'centipawn_loss': centipawn_loss,
                'fen': board.fen()
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
                
                analysis['move_classifications'].append(move_info)
            
            prev_score = current_score
        
        # Calculate average centipawn loss
        if target_moves > 0:
            analysis['avg_centipawn_loss'] = total_centipawn_loss / target_moves
        
        engine.quit()
        return analysis
        
    except Exception as e:
        print(f"Game analysis error: {e}")
        if engine:
            engine.quit()
        return None

def perform_tactical_analysis(games, target_player, max_games=10):
    """Perform Stockfish analysis on multiple games to identify patterns"""
    
    print(f"\n### STEP 4: Stockfish Engine Analysis ###")
    print(f"Analyzing up to {max_games} games for tactical patterns...")
    
    tactical_stats = {
        'total_analyzed': 0,
        'blunder_count': 0,
        'mistake_count': 0,
        'inaccuracy_count': 0,
        'games_with_blunders': 0,
        'opening_blunders': defaultdict(list),
        'opening_mistakes': defaultdict(list),
        'avg_centipawn_loss': 0,
        'tactical_weaknesses': [],
        'best_openings': [],  # Openings with low error rates
        'worst_openings': []  # Openings with high error rates
    }
    
    total_centipawn_loss = 0
    analyzed_games = 0
    
    # Analyze a subset of games to avoid long processing time
    games_to_analyze = min(max_games, len(games))
    
    for i, game in enumerate(games[:games_to_analyze]):
        eco = game.headers.get('ECO', 'Unknown')
        opening_name = ECO_OPENINGS.get(eco, f"ECO {eco}")
        
        print(f"  [{i+1}/{games_to_analyze}] Analyzing: {opening_name} ({eco})")
        
        # Analyze this game
        game_analysis = analyze_game_moves(game, target_player, max_ply=20)
        
        if game_analysis and game_analysis['target_color']:
            analyzed_games += 1
            tactical_stats['total_analyzed'] += 1
            
            # Count tactical errors
            blunders = len(game_analysis['blunders'])
            mistakes = len(game_analysis['mistakes'])
            inaccuracies = len(game_analysis['inaccuracies'])
            
            tactical_stats['blunder_count'] += blunders
            tactical_stats['mistake_count'] += mistakes
            tactical_stats['inaccuracy_count'] += inaccuracies
            
            if blunders > 0:
                tactical_stats['games_with_blunders'] += 1
                tactical_stats['opening_blunders'][eco].extend(game_analysis['blunders'])
            
            if mistakes > 0:
                tactical_stats['opening_mistakes'][eco].extend(game_analysis['mistakes'])
            
            total_centipawn_loss += game_analysis['avg_centipawn_loss']
            
            # Determine game result for target player
            white_player = game.headers.get("White", "").lower()
            target_lower = target_player.lower()
            result = game.headers.get('Result', '*')
            
            if target_lower in white_player:
                if result == '1-0':
                    game_result = 'win'
                elif result == '0-1':
                    game_result = 'loss'
                else:
                    game_result = 'draw'
            else:
                if result == '0-1':
                    game_result = 'win'
                elif result == '1-0':
                    game_result = 'loss'
                else:
                    game_result = 'draw'
            
            # Store detailed analysis for this opening
            opening_stats = {
                'eco': eco,
                'opening': opening_name,
                'blunders': blunders,
                'mistakes': mistakes,
                'inaccuracies': inaccuracies,
                'total_errors': blunders + mistakes + inaccuracies,
                'avg_centipawn_loss': game_analysis['avg_centipawn_loss'],
                'game_result': game_result,
                'target_color': game_analysis['target_color']
            }
            
            # Classify as tactical weakness if many errors
            if blunders > 0 or mistakes > 1 or game_analysis['avg_centipawn_loss'] > 25:
                tactical_stats['tactical_weaknesses'].append(opening_stats)
            else:
                tactical_stats['best_openings'].append(opening_stats)
        
        else:
            print(f"    Could not analyze this game (target player not found or engine error)")
    
    # Calculate averages
    if analyzed_games > 0:
        tactical_stats['avg_centipawn_loss'] = total_centipawn_loss / analyzed_games
    
    # Print detailed analysis results
    print(f"\n### Tactical Analysis Results ###")
    print(f"Games analyzed: {analyzed_games}")
    
    if analyzed_games > 0:
        print(f"Average centipawn loss per move: {tactical_stats['avg_centipawn_loss']:.1f}")
        print(f"Total blunders: {tactical_stats['blunder_count']}")
        print(f"Total mistakes: {tactical_stats['mistake_count']}")
        print(f"Total inaccuracies: {tactical_stats['inaccuracy_count']}")
        print(f"Games with blunders: {tactical_stats['games_with_blunders']}/{analyzed_games} ({tactical_stats['games_with_blunders']/analyzed_games*100:.1f}%)")
        
        # Analysis by opening
        if tactical_stats['opening_blunders']:
            print(f"\n### Blunder Patterns by Opening ###")
            for eco, blunder_list in tactical_stats['opening_blunders'].items():
                opening_name = ECO_OPENINGS.get(eco, f"ECO {eco}")
                print(f"\n{opening_name} ({eco}): {len(blunder_list)} blunders")
                
                # Show specific blunder details
                for i, blunder in enumerate(blunder_list[:3]):  # Show first 3 blunders
                    print(f"  Blunder {i+1}: Move {blunder['move_number']}.{blunder['move_san'] if 'move_san' in blunder else blunder['move']} "
                          f"({blunder['color']}) - Lost {blunder['centipawn_loss']:.0f} centipawns")
        
        # Tactical weakness summary
        if tactical_stats['tactical_weaknesses']:
            print(f"\n### Openings with Tactical Issues ###")
            for weakness in sorted(tactical_stats['tactical_weaknesses'], 
                                 key=lambda x: x['total_errors'], reverse=True)[:5]:
                print(f"{weakness['opening']} ({weakness['eco']}) as {weakness['target_color'].title()}:")
                print(f"  Errors: {weakness['blunders']} blunders, {weakness['mistakes']} mistakes, {weakness['inaccuracies']} inaccuracies")
                print(f"  Average loss: {weakness['avg_centipawn_loss']:.1f} cp/move, Result: {weakness['game_result']}")
        
        # Best openings
        if tactical_stats['best_openings']:
            print(f"\n### Tactically Sound Openings ###")
            for good_opening in sorted(tactical_stats['best_openings'], 
                                     key=lambda x: x['avg_centipawn_loss'])[:3]:
                print(f"{good_opening['opening']} ({good_opening['eco']}) as {good_opening['target_color'].title()}:")
                print(f"  Clean play: {good_opening['avg_centipawn_loss']:.1f} cp/move average loss, Result: {good_opening['game_result']}")
    
    else:
        print("No games could be analyzed with Stockfish.")
    
    return tactical_stats

# Apply engine analysis to our parsed games
if all_games:
    print("\nStarting comprehensive Stockfish analysis...")
    tactical_analysis = perform_tactical_analysis(all_games, target_username, max_games=5)
    
    # Integrate tactical analysis with existing weakness analysis
    if 'weakness_report' in locals():
        weakness_report['tactical_analysis'] = tactical_analysis
        
        print(f"\n### INTEGRATED ANALYSIS SUMMARY ###")
        print(f"Total games analyzed: {len(all_games)}")
        print(f"Games with tactical analysis: {tactical_analysis['total_analyzed']}")
        print(f"Opening weaknesses identified: {len(weakness_report['opening_weaknesses'])}")
        print(f"Tactical patterns detected: {tactical_analysis['blunder_count']} blunders, {tactical_analysis['mistake_count']} mistakes")
        
        # Combine opening and tactical weaknesses
        combined_weaknesses = []
        for opening_weakness in weakness_report['opening_weaknesses'][:5]:
            eco = opening_weakness['eco']
            # Find corresponding tactical data
            tactical_data = next((t for t in tactical_analysis['tactical_weaknesses'] if t['eco'] == eco), None)
            
            if tactical_data:
                opening_weakness['tactical_errors'] = tactical_data['total_errors']
                opening_weakness['avg_centipawn_loss'] = tactical_data['avg_centipawn_loss']
                opening_weakness['combined_score'] = opening_weakness['weakness_score'] + tactical_data['total_errors'] * 10
            else:
                opening_weakness['tactical_errors'] = 0
                opening_weakness['avg_centipawn_loss'] = 0
                opening_weakness['combined_score'] = opening_weakness['weakness_score']
            
            combined_weaknesses.append(opening_weakness)
        
        # Sort by combined score
        combined_weaknesses.sort(key=lambda x: x['combined_score'], reverse=True)
        
        print(f"\n### TOP COMBINED WEAKNESSES (Results + Tactics) ###")
        for i, weakness in enumerate(combined_weaknesses[:3], 1):
            print(f"{i}. {weakness['opening']} ({weakness['eco']}) as {weakness['color'].replace('as_', '').title()}")
            print(f"   Win Rate: {weakness['win_rate']:.1f}% ({weakness['wins']}-{weakness['losses']}-{weakness.get('draws', 0)})")
            print(f"   Tactical: {weakness['tactical_errors']} errors, {weakness['avg_centipawn_loss']:.1f} cp/move")
            print(f"   Combined Score: {weakness['combined_score']:.1f}/100")
            print()
    
else:
    print("No games available for tactical analysis.")
### STEP 3: Identify Weakness Signals by Opening

import chess
import chess.pgn

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
        moves_analysis['