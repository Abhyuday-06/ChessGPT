#!/usr/bin/env python3
"""
ChessGPT - Chess Game Analysis Tool
This script fetches chess games from Chess.com and Lichess, analyzes them for tactical patterns,
and provides insights about player performance and areas for improvement.
"""

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

def fetch_chess_com_games(username, max_archives=3):
    """Fetch games from Chess.com API"""
    print(f"Fetching games for {username} from Chess.com...")
    
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
            print(f"Empty response for user {username}")
            return None
            
        archives = response.json()
        print(f"Found {len(archives['archives'])} archive months for {username}")
        
        # Get the most recent archive to avoid too much data
        if archives["archives"]:
            for i in range(1, min(max_archives + 1, len(archives["archives"]) + 1)):
                latest_url = archives["archives"][-i]
                print(f"Fetching games from: {latest_url}")
                
                pgn_response = requests.get(latest_url + "/pgn", headers=headers)
                pgn_response.raise_for_status()
                pgn_data = pgn_response.text
                
                if pgn_data.strip():
                    print(f"Fetched {len(pgn_data.splitlines())} lines of PGN data for {username}")
                    
                    with open("chess_com_games.pgn", "w", encoding="utf-8") as f:
                        f.write(pgn_data)
                    print("PGN data saved to 'chess_com_games.pgn'")
                    return pgn_data
                    
        print(f"No games found for user {username}")
        return None
        
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
            if e.response.status_code == 403:
                print("Error: Chess.com is blocking automated requests.")
                print("Possible solutions:")
                print("1. Try again later (rate limiting may reset)")
                print("2. Use a different username")
                print("3. Consider using the Lichess API instead")
        return None
    except Exception as e:
        print(f"Error fetching from Chess.com: {e}")
        return None

def fetch_lichess_games(username, max_games=10):
    """Fetch games from Lichess API"""
    print(f"Fetching games for {username} from Lichess...")
    
    try:
        url = f"https://lichess.org/api/games/user/{username}"
        params = {
            'max': max_games,
            'format': 'pgn'
        }
        headers = {
            'User-Agent': 'ChessGPT/1.0 Educational Tool',
            'Accept': 'application/x-chess-pgn'
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        pgn_data = response.text
        if pgn_data.strip():
            print(f"Successfully fetched {len(pgn_data.splitlines())} lines of PGN data from Lichess")
            
            with open("lichess_games.pgn", "w", encoding="utf-8") as f:
                f.write(pgn_data)
            print("PGN data saved to 'lichess_games.pgn'")
            return pgn_data
        else:
            print("No game data found on Lichess")
            return None
            
    except Exception as e:
        print(f"Lichess API error: {e}")
        return None

### STEP 2: Parse Games and Extract Openings ###

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

### STEP 3: Stockfish Integration ###

def get_stockfish_engine():
    """Get a working Stockfish engine instance"""
    stockfish_paths = [
        "stockfish/stockfish.exe",  # Downloaded executable
        "stockfish.exe",            # Current directory (Windows)
        "stockfish",                # Current directory (Unix)
        "/usr/local/bin/stockfish", # Common install location
        "/opt/homebrew/bin/stockfish", # Homebrew on M1 Mac
        "C:\\Program Files\\Stockfish\\stockfish.exe",  # Windows install
    ]
    
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

def analyze_game_with_stockfish(game, engine, target_player, max_moves=20):
    """Analyze a single game with Stockfish for tactical errors"""
    board = game.board()
    analysis_results = {
        'blunders': 0,
        'mistakes': 0,
        'inaccuracies': 0,
        'total_centipawn_loss': 0,
        'moves_analyzed': 0
    }
    
    white_player = game.headers.get("White", "").lower()
    target_lower = target_player.lower()
    target_is_white = target_lower in white_player
    
    move_count = 0
    for move in game.mainline_moves():
        if move_count >= max_moves:
            break
            
        # Only analyze target player's moves
        is_target_move = (target_is_white and board.turn == chess.WHITE) or \
                        (not target_is_white and board.turn == chess.BLACK)
        
        if is_target_move:
            # Get evaluation before the move
            try:
                result_before = engine.analyse(board, chess.engine.Limit(time=0.1))
                eval_before = result_before['score'].relative.score(mate_score=10000)
                
                # Make the move
                board.push(move)
                
                # Get evaluation after the move
                result_after = engine.analyse(board, chess.engine.Limit(time=0.1))
                eval_after = result_after['score'].relative.score(mate_score=10000)
                
                # Calculate centipawn loss (from opponent's perspective, so flip sign)
                centipawn_loss = -(eval_after - eval_before)
                
                if centipawn_loss > 200:
                    analysis_results['blunders'] += 1
                elif centipawn_loss > 100:
                    analysis_results['mistakes'] += 1
                elif centipawn_loss > 50:
                    analysis_results['inaccuracies'] += 1
                
                analysis_results['total_centipawn_loss'] += max(0, centipawn_loss)
                analysis_results['moves_analyzed'] += 1
                
            except Exception as e:
                # If analysis fails, just make the move and continue
                board.push(move)
        else:
            # Just make the opponent's move
            board.push(move)
            
        move_count += 1
    
    return analysis_results

### STEP 4: Main Analysis Function ###

def analyze_player_performance(username):
    """Main function to analyze a player's performance"""
    print(f"Starting analysis for player: {username}")
    
    # Step 1: Fetch games
    chess_com_data = fetch_chess_com_games(username)
    lichess_data = fetch_lichess_games(username)
    
    # Step 2: Parse games
    all_games = []
    
    if os.path.exists("chess_com_games.pgn"):
        chess_com_games = parse_pgn_file("chess_com_games.pgn")
        all_games.extend(chess_com_games)
    
    if os.path.exists("lichess_games.pgn"):
        lichess_games = parse_pgn_file("lichess_games.pgn")
        all_games.extend(lichess_games)
    
    if not all_games:
        print("No games found to analyze.")
        return
    
    print(f"Total games loaded: {len(all_games)}")
    
    # Step 3: Basic statistics
    player_stats = {'wins': 0, 'losses': 0, 'draws': 0, 'total': 0}
    
    for game in all_games:
        white_player = game.headers.get("White", "").lower()
        black_player = game.headers.get("Black", "").lower()
        result = game.headers.get("Result", "*")
        username_lower = username.lower()
        
        if username_lower in white_player or username_lower in black_player:
            player_stats['total'] += 1
            
            if username_lower in white_player:
                if result == "1-0":
                    player_stats['wins'] += 1
                elif result == "0-1":
                    player_stats['losses'] += 1
                else:
                    player_stats['draws'] += 1
            else:  # Playing as black
                if result == "0-1":
                    player_stats['wins'] += 1
                elif result == "1-0":
                    player_stats['losses'] += 1
                else:
                    player_stats['draws'] += 1
    
    if player_stats['total'] > 0:
        win_rate = (player_stats['wins'] / player_stats['total']) * 100
        print(f"\nPlayer Statistics for {username}:")
        print(f"Total games: {player_stats['total']}")
        print(f"Wins: {player_stats['wins']} ({win_rate:.1f}%)")
        print(f"Losses: {player_stats['losses']} ({(player_stats['losses']/player_stats['total'])*100:.1f}%)")
        print(f"Draws: {player_stats['draws']} ({(player_stats['draws']/player_stats['total'])*100:.1f}%)")
    
    # Step 4: Stockfish analysis
    engine = get_stockfish_engine()
    if engine:
        print(f"\nStarting Stockfish tactical analysis...")
        
        total_analysis = {
            'games_analyzed': 0,
            'total_blunders': 0,
            'total_mistakes': 0,
            'total_inaccuracies': 0,
            'total_centipawn_loss': 0,
            'total_moves': 0
        }
        
        # Analyze up to 5 games for demonstration
        for i, game in enumerate(all_games[:5]):
            eco = game.headers.get('ECO', 'Unknown')
            opening_name = get_opening_name(eco, game.headers.get('Opening', 'Unknown'))
            
            print(f"  [{i+1}/5] Analyzing: {opening_name} ({eco})")
            
            analysis = analyze_game_with_stockfish(game, engine, username)
            
            total_analysis['games_analyzed'] += 1
            total_analysis['total_blunders'] += analysis['blunders']
            total_analysis['total_mistakes'] += analysis['mistakes']
            total_analysis['total_inaccuracies'] += analysis['inaccuracies']
            total_analysis['total_centipawn_loss'] += analysis['total_centipawn_loss']
            total_analysis['total_moves'] += analysis['moves_analyzed']
            
            if analysis['moves_analyzed'] > 0:
                avg_loss = analysis['total_centipawn_loss'] / analysis['moves_analyzed']
                if analysis['blunders'] > 0:
                    print(f"    💥 Found {analysis['blunders']} blunders")
                elif analysis['mistakes'] > 0:
                    print(f"    ⚡ Found {analysis['mistakes']} mistakes")
                else:
                    print(f"    ✓ Clean game (avg loss: {avg_loss:.1f} cp)")
        
        # Final results
        print(f"\n### Tactical Analysis Results ###")
        print(f"Games analyzed: {total_analysis['games_analyzed']}")
        
        if total_analysis['total_moves'] > 0:
            avg_centipawn_loss = total_analysis['total_centipawn_loss'] / total_analysis['total_moves']
            accuracy = max(0, 100 - avg_centipawn_loss / 10)  # Rough accuracy calculation
            
            print(f"Average centipawn loss per move: {avg_centipawn_loss:.1f}")
            print(f"Estimated accuracy: {accuracy:.1f}%")
            print(f"Total errors found:")
            print(f"  • Blunders (200+ cp): {total_analysis['total_blunders']}")
            print(f"  • Mistakes (100-199 cp): {total_analysis['total_mistakes']}")
            print(f"  • Inaccuracies (50-99 cp): {total_analysis['total_inaccuracies']}")
            
            if total_analysis['total_blunders'] > 0:
                print(f"\n⚠ PRIORITY: Address {total_analysis['total_blunders']} blunders found")
            if total_analysis['total_mistakes'] > 0:
                print(f"⚡ SECONDARY: Reduce {total_analysis['total_mistakes']} mistakes")
        
        engine.quit()
    else:
        print("Skipping engine analysis (Stockfish not available)")
    
    print(f"\n### Analysis Complete ###")
    print("Recommendations:")
    print("1. Focus on tactical training to reduce blunders")
    print("2. Study your most frequently played openings")
    print("3. Analyze games where you lost quickly (< 30 moves)")

if __name__ == "__main__":
    # You can change this username to analyze different players
    target_username = "hikaru"  # Chess.com username
    # For Lichess, try "DrNykterstein" (Hikaru's Lichess account)
    
    analyze_player_performance(target_username)
