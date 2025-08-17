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

engine = chess.engine.SimpleEngine.popen_uci("/path/to/stockfish")

board = chess.Board()
for move in game.mainline_moves():
    board.push(move)
    # After each move (or at chosen depths), get evaluation:
    info = engine.analyse(board, chess.engine.Limit(depth=16))
    score = info["score"]
    # score is a PovScore object, relative to the side to move.

# eg:  if in Sicilian games the opponent blundered with evaluation swings >200 cp two times, that signals tactical weakness in the Sicilian. These counts can be turned into percentages (e.g. “Blunder rate: 20% of Sicilian games”)

engine.quit()



### STEP 5: Summarize Opponent Profile and Weak Lines

#eg: “Against 1.e4 as Black: They favor the Sicilian (ECO B20-B99) but have only a 55% score and frequent tactical errors on move 5. They rarely see the Vienna Game as White (3 games) and lost in those. They often play the Queen’s Gambit Declined (ECO D30-D69) as Black, with a solid 80% score and few mistakes.”

def summarize_opponent(opening_stats, blunders, game_count):
    summary = []
    for eco, games in opening_stats.items():
        total = len(games)
        win_rate = sum(1 for g in games if result_for_opponent(g) == "win") / total * 100
        blunder_rate = blunders.get(eco, 0) / total * 100
        if total < 5:
            summary.append(f"- Rarely plays {eco} ({total} games).")
        elif win_rate < 40 or blunder_rate > 20:
            summary.append(f"- Weak in {eco}: Win rate {win_rate:.1f}%, blunder rate {blunder_rate:.1f}%.")
    return "\n".join(summary)




### STEP 5.5: Create input-output pairs for LLM training

"""
{
  "input": "Opponent has a 35% win rate with the Sicilian (B40-B99) as Black. Frequent errors on move 5, especially in the Najdorf (B90). Blundered 12 times in 20 games. Average Stockfish eval after 10 moves: -0.6 (White better).\nPrepare against: Sicilian Najdorf.\nYour goal: Suggest best preparation line and rationale.",
  "output": "Play 1.e4. If opponent plays c5, aim for the Najdorf with 6.Be3. Known weakness in ...e5 setups. Line: 1.e4 c5 2.Nf3 d6 3.d4 cxd4 4.Nxd4 Nf6 5.Nc3 a6 6.Be3 e5? 7.Nb3 Be6 8.f3. This line forces opponent into unfamiliar positions. Summary: Aim for early f3 and queenside attack. Avoid deep theory."
}

"""

from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments
from peft import LoraConfig, get_peft_model
from datasets import load_dataset

model_name = "mistralai/Mistral-7B-v0.1"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, load_in_8bit=True, device_map="auto")

lora_config = LoraConfig(
    r=8,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.1,
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, lora_config)

# Load your chess fine-tuning dataset
dataset = load_dataset("json", data_files="chess_opening_preparation.json")["train"]
tokenized = dataset.map(lambda x: tokenizer(x["input"] + tokenizer.eos_token + x["output"], truncation=True, padding="max_length"), batched=True)

trainer = Trainer(
    model=model,
    args=TrainingArguments(
        output_dir="./chess-prep-lora",
        per_device_train_batch_size=2,
        num_train_epochs=3,
        save_steps=500,
        logging_steps=100
    ),
    train_dataset=tokenized
)

trainer.train()




### STEP 6: Generating the LLM Prompt

"""

"""  Prepare chess opening preparation against opponent {username}:
- Opponent profile: [Summary of weaknesses and tendencies per opening, as above].
- Recommended strategy: [E.g., “Play 1.e4 and aim for the Sicilian Najdorf (B90) where the opponent struggles, focusing on ...”].
- Move-by-move lines: [List specific move sequences to play and why].
- Alternative lines: [e.g., “If they avoid Najdorf, try 6.Be3 in Scheveningen...”]. """
"""

def build_prompt(opponent_username, opening_summary, target_openings):
    prompt = f"""
""" You are a chess preparation assistant. Your user is preparing against {opponent_username}.

Opponent tendencies:
{opening_summary}

Target preparation: {", ".join(target_openings)}

Provide:
1. Summary of best lines to play.
2. Concrete move-by-move sequences.
3. Short explanation of why they are effective.
""" """
    return prompt.strip()

from transformers import pipeline


generator = pipeline("text-generation", model=model, tokenizer=tokenizer)
response = generator(prompt, max_length=1024, temperature=0.7)[0]["generated_text"]


### STEP 7: Real-time Integration and Adaptation


def full_opponent_prep(username):
   
    games = fetch_games(username)
    stats, blunders = analyze_games(games)
    summary = summarize_opponent(stats, blunders, len(games))
    prompt = build_prompt(username, summary, target_openings=["Sicilian Najdorf", "Ruy Lopez"])
    output = run_llm(prompt)
   
    return output