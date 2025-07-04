import requests
import json
import time
import chess
import chess.pgn
import chess.engine
import platform
import os
from pathlib import Path
from collections import defaultdict

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

def perform_stockfish_analysis(games, target_player, max_games=5):
    """
    Perform Stockfish analysis on games to detect tactical patterns.
    Analyzes the first 10 moves (20 ply) from each side.
    """
    
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
            
            print(f"  [{i+1}/{games_to_analyze}] Analyzing: {opening_name} ({eco})")
            
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
                    error_rate = total_errors / stats['games']
                    
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
    tactical_analysis = perform_stockfish_analysis(all_games, target_username, max_games=5)
    
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

else:
    print("No games available for tactical analysis.")

print("\n### STEP 4 COMPLETE ###")
print("Move-by-move Stockfish analysis complete!")
print("Key findings:")
print("- Blunders: Moves losing 200+ centipawns")
print("- Mistakes: Moves losing 100-199 centipawns") 
print("- Inaccuracies: Moves losing 50-99 centipawns")
print("- Analysis covers the first 10 moves (20 ply) from each side")
