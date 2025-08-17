import requests
import json
import time
import chess
import chess.pgn
import chess.engine
import platform
import os
import io
import datetime
import urllib.parse
from pathlib import Path
from collections import defaultdict

### STEP 1: Get User Input and Platform Selection ###

import sys

# Get username and platform from user input
if len(sys.argv) > 2:
    user = sys.argv[1]
    platform = sys.argv[2].lower()
elif len(sys.argv) > 1:
    user = sys.argv[1]
    platform = None
else:
    user = None
    platform = None

# Interactive input if not provided via command line
if not user:
    user = input("Enter chess username to analyze: ").strip()
    if not user:
        print("❌ Username is required")
        sys.exit(1)

if not platform:
    print("\nSelect platform:")
    print("1. Chess.com")
    print("2. Lichess")
    
    while True:
        choice = input("Enter choice (1 or 2): ").strip()
        if choice == "1":
            platform = "chess.com"
            break
        elif choice == "2":
            platform = "lichess"
            break
        else:
            print("Please enter 1 or 2")

print(f"\n🎯 Analyzing games for {user} on {platform}")
print("=" * 50)

### STEP 2: Fetch Games from Selected Platform ###

def download_chess_com_games(username, max_games=50):
    """Download games from Chess.com"""
    print(f"🔍 Downloading Chess.com games for {username}...")
    
    try:
        # Add headers to make the request look more like a browser
        headers = {
            'User-Agent': 'ChessGPT/1.0 (Educational chess analysis tool)',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
        # Add a small delay to be respectful to the API
        time.sleep(1)
        
        response = requests.get(f"https://api.chess.com/pub/player/{username}/games/archives", headers=headers)
        response.raise_for_status()
        
        if response.text.strip() == "":
            print(f"❌ Empty response for user {username}")
            return False
        
        archives = response.json()
        print(f"📊 Found {len(archives['archives'])} archive months for {username}")
        
        # Get the most recent archive to avoid too much data
        if archives["archives"]:
            all_pgn_data = []
            games_found = 0
            
            # Try the last few months to find games
            for i in range(1, min(4, len(archives["archives"]) + 1)):
                if games_found >= max_games:
                    break
                    
                latest_url = archives["archives"][-i]
                print(f"📥 Fetching games from: {latest_url}")
                
                try:
                    time.sleep(1)  # Be respectful to the API
                    pgn_response = requests.get(latest_url + "/pgn", headers=headers)
                    pgn_response.raise_for_status()
                    pgn_data = pgn_response.text
                    
                    if pgn_data.strip():
                        all_pgn_data.append(pgn_data)
                        # Count games roughly by counting [Event headers
                        games_in_archive = pgn_data.count('[Event ')
                        games_found += games_in_archive
                        print(f"📄 Found {games_in_archive} games in archive")
                    else:
                        print(f"⚠️ No games found in {latest_url}")
                        
                except Exception as e:
                    print(f"⚠️ Error fetching archive {i}: {e}")
                    continue
            
            if all_pgn_data:
                combined_pgn = "\n\n".join(all_pgn_data)
                with open("chess_com_games.pgn", "w", encoding="utf-8") as f:
                    f.write(combined_pgn)
                print(f"✅ Saved {games_found} games to 'chess_com_games.pgn'")
                return True
            else:
                print(f"❌ No games found in recent months for user {username}")
                return False
        else:
            print(f"❌ No archives found for user {username}")
            return False
            
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP error occurred: {e}")
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
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error occurred: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def download_lichess_games(username, max_games=50):
    """Download games from Lichess"""
    print(f"🔍 Downloading Lichess games for {username}...")
    
    try:
        lichess_url = f"https://lichess.org/api/games/user/{username}"
        
        # Lichess API parameters
        params = {
            'max': max_games,
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
            # Count games
            games_count = pgn_data.count('[Event ')
            print(f"📊 Successfully fetched {games_count} games from Lichess")
            
            # Save the PGN data to a file for later use
            with open("lichess_games.pgn", "w", encoding="utf-8") as f:
                f.write(pgn_data)
            print("✅ PGN data saved to 'lichess_games.pgn'")
            return True
        else:
            print("❌ No game data found on Lichess")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Lichess API error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error with Lichess: {e}")
        return False

# Download games from selected platform
if platform == "chess.com":
    success = download_chess_com_games(user)
    if not success:
        print("❌ Failed to download Chess.com games")
        sys.exit(1)
elif platform == "lichess":
    success = download_lichess_games(user)
    if not success:
        print("❌ Failed to download Lichess games")
        sys.exit(1)
else:
    print("❌ Invalid platform selected")
    sys.exit(1)

print(f"✅ Successfully downloaded games for {user} from {platform}")
print("=" * 50)

### STEP 3: Parse Games and Extract Openings ###

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

# Parse PGN file based on selected platform
print(f"\n### STEP 4: Parsing PGN Files from {platform} ###")

all_games = []
target_username = user  # Use the input username for analysis

# Parse from the correct platform file
if platform == "chess.com":
    chess_com_games = parse_pgn_file("chess_com_games.pgn")
    all_games.extend(chess_com_games)
    print(f"📊 Loaded {len(chess_com_games)} games from Chess.com")
elif platform == "lichess":
    lichess_games = parse_pgn_file("lichess_games.pgn")
    all_games.extend(lichess_games)
    print(f"📊 Loaded {len(lichess_games)} games from Lichess")

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

### STEP 5: Identify Weakness Signals by Opening ###

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
    
    print(f"\n### STEP 5: Comprehensive Weakness Analysis for {target_player} ###")
    
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

### STEP 6: Stockfish Evaluation for Move-by-Move Analysis

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
    
    print(f"\n### STEP 6: Stockfish Engine Analysis ###")
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

print("\n### STEP 6 COMPLETE ###")
print("Move-by-move Stockfish analysis complete!")
print("Key findings:")
print("- Blunders: Moves losing 200+ centipawns")
print("- Mistakes: Moves losing 100-199 centipawns") 
print("- Inaccuracies: Moves losing 50-99 centipawns")
print("- Analysis covers the first 10 moves (20 ply) from each side")

### STEP 8: Generate Research Paper Visualizations ###

def generate_research_visualizations(all_games, player_stats, weakness_report, tactical_analysis, target_username):
    """Generate all visualizations for research paper"""
    
    print(f"\n### GENERATING RESEARCH VISUALIZATIONS ###")
    print("Creating visual analyses for research paper...")
    
    try:
        # Import visualization modules
        from visualization_generator import generate_all_visualizations
        from advanced_visualizations import generate_advanced_visualizations
        
        # Generate standard visualizations
        generate_all_visualizations(all_games, player_stats, weakness_report, tactical_analysis, target_username)
        
        # Generate advanced visualizations
        generate_advanced_visualizations(player_stats, weakness_report, tactical_analysis, target_username)
        
        print("\n🎉 ALL VISUALIZATIONS COMPLETE! 🎉")
        print("=" * 60)
        print("📁 Check the 'visualizations' folder for all generated charts")
        print("📄 Review 'visualization_report.md' for detailed descriptions")
        print("🔬 These visualizations are ready for your research paper!")
        
    except ImportError as e:
        print(f"⚠ Missing visualization modules: {e}")
        print("Make sure visualization_generator.py and advanced_visualizations.py are in the same directory")
        print("Install requirements: pip install matplotlib seaborn pandas networkx plotly")
    except Exception as e:
        print(f"❌ Error generating visualizations: {e}")
        import traceback
        traceback.print_exc()

# Call the visualization function at the very end of your analysis
if all_games and 'weakness_report' in locals() and 'tactical_analysis' in locals():
    generate_research_visualizations(all_games, player_stats, weakness_report, tactical_analysis, target_username)
else:
    print("⚠ Some analysis data missing - skipping visualizations")
    print("Available data:")
    print(f"  - Games: {'✓' if all_games else '✗'}")
    print(f"  - Player Stats: {'✓' if 'player_stats' in locals() else '✗'}")
    print(f"  - Weakness Report: {'✓' if 'weakness_report' in locals() else '✗'}")
    print(f"  - Tactical Analysis: {'✓' if 'tactical_analysis' in locals() else '✗'}")

print("\n### VISUALIZATION INTEGRATION COMPLETE ###")

### STEP 7: Generate LLM Training Data for Chess Strategy ###

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

def generate_opening_pgn_and_links(opening_name, variation_name=""):
    """Generate PGN and analysis links for specific opening lines"""
    
    # Opening move sequences mapped to their PGN
    opening_pgns = {
        # Sicilian Dragon variations
        "Sicilian Dragon": "1.e4 c5 2.Nf3 d6 3.d4 cxd4 4.Nxd4 Nf6 5.Nc3 g6 6.Be3 Bg7 7.f3 Nc6 8.Qd2 O-O 9.Bc4 Bd7 10.O-O-O",
        "Sicilian Najdorf": "1.e4 c5 2.Nf3 d6 3.d4 cxd4 4.Nxd4 Nf6 5.Nc3 a6 6.Bg5 e6 7.f4 Be7 8.Qf3 Qc7 9.O-O-O",
        "Accelerated Dragon": "1.e4 c5 2.Nf3 g6 3.d4 cxd4 4.Nxd4 Bg7 5.Nc3 Nc6 6.Be3 Nf6 7.Bc4 O-O 8.Bb3",
        "Yugoslav Attack": "1.e4 c5 2.Nf3 d6 3.d4 cxd4 4.Nxd4 Nf6 5.Nc3 g6 6.Be3 Bg7 7.f3 Nc6 8.Qd2 O-O 9.Bc4 Bd7 10.O-O-O Rc8 11.Bb3 Ne5 12.h4",
        
        # King's Indian Defense
        "King's Indian Defense": "1.d4 Nf6 2.c4 g6 3.Nc3 Bg7 4.e4 d6 5.Nf3 O-O 6.Be2 e5 7.O-O Nc6 8.d5 Ne7",
        "King's Indian setup": "1.d4 Nf6 2.c4 g6 3.Nc3 Bg7 4.e4 d6 5.Nf3 O-O",
        
        # Dutch Defense
        "Dutch Defense": "1.d4 f5 2.g3 Nf6 3.Bg2 e6 4.Nf3 Be7 5.O-O O-O 6.c4 d6",
        
        # Two Knights Defense
        "Two Knights Defense": "1.e4 e5 2.Nf3 Nc6 3.Bc4 Nf6 4.Ng5 d5 5.exd5 Na5 6.Bb5+ c6 7.dxc6 bxc6 8.Be2",
        
        # Berlin Defense
        "Berlin Defense": "1.e4 e5 2.Nf3 Nc6 3.Bb5 Nf6 4.O-O Nxe4 5.d4 Nd6 6.Bxc6 dxc6 7.dxe5 Nf5 8.Qxd8+ Kxd8",
        
        # Marshall Attack
        "Marshall Attack": "1.e4 e5 2.Nf3 Nc6 3.Bb5 a6 4.Ba4 Nf6 5.O-O Be7 6.Re1 b5 7.Bb3 O-O 8.c3 d5",
        
        # Caro-Kann variations
        "Caro-Kann Advance": "1.e4 c6 2.d4 d5 3.e5 Bf5 4.Nf3 e6 5.Be2 Nd7 6.O-O Ne7 7.Nbd2",
        "Panov-Botvinnik Attack": "1.e4 c6 2.d4 d5 3.exd5 cxd5 4.c4 Nf6 5.Nc3 e6 6.Nf3 Bb4 7.cxd5 Nxd5 8.Bd2",
        
        # French Defense
        "French Classical": "1.e4 e6 2.d4 d5 3.Nc3 Nf6 4.Bg5 Be7 5.e5 Nfd7 6.Bxe7 Qxe7 7.f4",
        "French Advance": "1.e4 e6 2.d4 d5 3.e5 c5 4.c3 Nc6 5.Nf3 Qb6 6.a3 c4",
        
        # Alekhine Defense
        "Alekhine Defense": "1.e4 Nf6 2.e5 Nd5 3.d4 d6 4.Nf3 dxe5 5.Nxe5 Nd7 6.Nxd7 Bxd7 7.Bd3",
        
        # Benoni Defense
        "Benoni Defense": "1.d4 Nf6 2.c4 c5 3.d5 e6 4.Nc3 exd5 5.cxd5 d6 6.e4 g6 7.Nf3 Bg7 8.Be2 O-O",
        
        # English Opening variations
        "English Opening": "1.c4 e5 2.Nc3 Nf6 3.g3 d5 4.cxd5 Nxd5 5.Bg2 Nb6 6.Nf3 Nc6 7.O-O Be7",
        "English Neo-Catalan": "1.c4 Nf6 2.g3 e6 3.Bg2 d5 4.Nf3 Be7 5.O-O O-O 6.b3 c5 7.Bb2",
        "Reversed Sicilian": "1.c4 e5 2.Nc3 Nc6 3.g3 g6 4.Bg2 Bg7 5.d3 d6 6.Nf3",
        
        # Common tactical lines
        "Sharp tactical play": "1.e4 c5 2.Nf3 d6 3.d4 cxd4 4.Nxd4 Nf6 5.Nc3 a6 6.f4 e5 7.Nf3 Nbd7 8.Bd3",
        "Complex middlegame": "1.d4 Nf6 2.c4 g6 3.Nc3 d5 4.cxd5 Nxd5 5.e4 Nxc3 6.bxc3 Bg7 7.Bc4 c5 8.Ne2 Nc6 9.Be3 O-O 10.O-O"
    }
    
    # Get PGN for the opening/variation
    pgn = opening_pgns.get(variation_name, opening_pgns.get(opening_name, ""))
    
    if not pgn:
        # Generate basic PGN based on opening name patterns
        if "Sicilian" in opening_name:
            pgn = "1.e4 c5 2.Nf3 d6 3.d4 cxd4 4.Nxd4 Nf6 5.Nc3"
        elif "French" in opening_name:
            pgn = "1.e4 e6 2.d4 d5 3.Nc3"
        elif "Caro-Kann" in opening_name:
            pgn = "1.e4 c6 2.d4 d5"
        elif "English" in opening_name:
            pgn = "1.c4 e5 2.Nc3 Nf6"
        elif "King's Indian" in opening_name:
            pgn = "1.d4 Nf6 2.c4 g6 3.Nc3 Bg7"
        else:
            pgn = "1.e4 e5 2.Nf3 Nc6"  # Default
    
    return pgn

def create_analysis_links(pgn, opening_name, variation_name=""):
    """Create analysis links for Lichess and Chess.com"""
    
    import urllib.parse
    
    # Create Lichess analysis link
    # Lichess accepts PGN in URL format
    lichess_pgn = pgn.replace(" ", "%20").replace(".", "%2E")
    lichess_url = f"https://lichess.org/analysis/pgn/{lichess_pgn}"
    
    # Create Chess.com analysis link (uses FEN from starting position)
    # For Chess.com, we'll create a simpler analysis board link
    chesscom_url = f"https://www.chess.com/analysis?pgn={urllib.parse.quote(pgn)}"
    
    # Create a more user-friendly opening explorer link for Lichess
    opening_explorer_url = f"https://lichess.org/analysis#{pgn.replace(' ', '_').replace('.', '')}"
    
    return {
        "lichess_analysis": lichess_url,
        "chesscom_analysis": chesscom_url,
        "lichess_explorer": f"https://lichess.org/analysis/standard/{pgn.split()[-1] if pgn else 'startpos'}",
        "opening_name": f"{opening_name} - {variation_name}" if variation_name else opening_name,
        "pgn": pgn
    }

def enhance_opening_recommendations(opening_recommendations):
    """Enhance opening recommendations with PGN and analysis links"""
    
    enhanced_recommendations = []
    
    for rec in opening_recommendations:
        enhanced_rec = rec.copy()
        enhanced_lines = []
        
        for line in rec.get('specific_lines', []):
            # Extract opening/variation name from the line description
            variation_name = ""
            opening_name = rec['target_opening']
            
            # Parse variation names from line descriptions
            if "Dragon" in line:
                variation_name = "Sicilian Dragon"
            elif "Najdorf" in line:
                variation_name = "Sicilian Najdorf"
            elif "Yugoslav Attack" in line:
                variation_name = "Yugoslav Attack"
            elif "Accelerated Dragon" in line:
                variation_name = "Accelerated Dragon"
            elif "Two Knights" in line:
                variation_name = "Two Knights Defense"
            elif "Berlin" in line:
                variation_name = "Berlin Defense"
            elif "Marshall" in line:
                variation_name = "Marshall Attack"
            elif "King's Indian" in line:
                variation_name = "King's Indian Defense"
            elif "Advance Variation" in line and "Caro" in opening_name:
                variation_name = "Caro-Kann Advance"
            elif "Panov-Botvinnik" in line:
                variation_name = "Panov-Botvinnik Attack"
            elif "Classical" in line and "French" in opening_name:
                variation_name = "French Classical"
            elif "Advance Variation" in line and "French" in opening_name:
                variation_name = "French Advance"
            elif "Alekhine" in line:
                variation_name = "Alekhine Defense"
            elif "Benoni" in line:
                variation_name = "Benoni Defense"
            elif "Dutch" in line:
                variation_name = "Dutch Defense"
            elif "Neo-Catalan" in line:
                variation_name = "English Neo-Catalan"
            elif "reversed Sicilian" in line:
                variation_name = "Reversed Sicilian"
            
            # Generate PGN and links
            pgn = generate_opening_pgn_and_links(opening_name, variation_name)
            links = create_analysis_links(pgn, opening_name, variation_name)
            
            enhanced_line = {
                "description": line,
                "pgn": pgn,
                "analysis_links": links
            }
            
            enhanced_lines.append(enhanced_line)
        
        enhanced_rec['specific_lines'] = enhanced_lines
        enhanced_recommendations.append(enhanced_rec)
    
    return enhanced_recommendations

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
    
    # Enhance opening recommendations with PGN and analysis links
    if counter_strategy['opening_recommendations']:
        counter_strategy['opening_recommendations'] = enhance_opening_recommendations(counter_strategy['opening_recommendations'])
    
    return counter_strategy

def create_training_data_entry(opponent_patterns, counter_strategy, target_player):
    """Create a single training data entry in input-output format"""
    
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
    
    print(f"\n### STEP 7: Generating LLM Training Dataset ###")
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

def display_enhanced_recommendations(training_dataset):
    """Display the enhanced recommendations with PGN and analysis links"""
    
    if not training_dataset:
        return
    
    main_entry = training_dataset[0]
    opening_choices = main_entry.get('output', {}).get('strategic_recommendations', {}).get('opening_choices', [])
    
    if not opening_choices:
        return
    
    print(f"\n### 🎯 ACTIONABLE STRATEGY RECOMMENDATIONS ###")
    print("Each recommendation includes PGN notation and analysis links for immediate study:")
    print("=" * 80)
    
    for i, rec in enumerate(opening_choices, 1):
        print(f"\n{i}. TARGET OPENING: {rec['target_opening']}")
        print(f"   STRATEGY: {rec['exploitation_method']}")
        print(f"   REASONING: {rec['reasoning']}")
        
        if rec.get('specific_lines'):
            print(f"\n   📚 RECOMMENDED LINES TO STUDY:")
            
            for j, line in enumerate(rec['specific_lines'], 1):
                if isinstance(line, dict):
                    print(f"\n   {i}.{j} {line['description']}")
                    print(f"        PGN: {line['pgn']}")
                    print(f"        🔗 Study on Lichess: {line['analysis_links']['lichess_analysis']}")
                    print(f"        🔗 Study on Chess.com: {line['analysis_links']['chesscom_analysis']}")
                else:
                    print(f"   {i}.{j} {line}")
        
        print(f"\n   ✅ EXPECTED SUCCESS RATE: {main_entry['output']['expected_success_rate']:.1f}")
        print("-" * 80)
    
    print(f"\n💡 TIP: Click the analysis links to open interactive boards where you can:")
    print("   • Explore variations with computer analysis")
    print("   • Practice the openings against the computer") 
    print("   • Study master games in these lines")
    print("   • Memorize key positions and ideas")

# Generate the training dataset
if all_games and 'weakness_report' in locals() and 'tactical_analysis' in locals():
    training_dataset = generate_llm_training_dataset(all_games, weakness_report, tactical_analysis, target_username)
    
    # Display enhanced recommendations for user
    display_enhanced_recommendations(training_dataset)
    
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
            
            if rec['specific_lines']:
                first_line = rec['specific_lines'][0]
                if isinstance(first_line, dict):
                    print(f"  - Specific line: {first_line['description']}")
                    print(f"    PGN: {first_line['pgn']}")
                    print(f"    📋 Lichess Analysis: {first_line['analysis_links']['lichess_analysis']}")
                    print(f"    📋 Chess.com Analysis: {first_line['analysis_links']['chesscom_analysis']}")
                else:
                    print(f"  - Specific lines: {first_line}")
        
        print(f"  - Expected success rate: {sample_entry['output']['expected_success_rate']:.1f}")
        
        print(f"\n### Enhanced Strategy Recommendations ###")
        print("Each opening line now includes:")
        print("✓ Complete PGN notation for the recommended variation")
        print("✓ Direct links to Lichess and Chess.com analysis boards") 
        print("✓ Click links to explore the opening with computer analysis")
        print("✓ Study the recommended lines interactively online")
        
        print(f"\n### Dataset Generation Complete ###")
        print(f"The dataset is ready for LLM training and contains structured input-output pairs")
        print(f"where the input describes opponent weaknesses and the output provides counter-strategies.")
        
        # Display overall dataset statistics
        display_dataset_statistics()
        
else:
    print("Cannot generate training dataset - missing game analysis data")

print("\n### STEP 7 COMPLETE ###")
print("LLM training dataset generation complete!")
print("\nTo analyze another player, run:")
print("  python chess_analyzer_complete.py <username> <platform>")
print("  Example: python chess_analyzer_complete.py magnus chess.com")
print("  Example: python chess_analyzer_complete.py DrNykterstein lichess")
print("or just run:")
print("  python chess_analyzer_complete.py")
print("and enter the username and platform when prompted.")

