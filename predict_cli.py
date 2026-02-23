#!/usr/bin/env python
"""
CLI interface for NBA game predictions.

Usage:
    python predict_cli.py "Boston Celtics"
    python predict_cli.py lakers
    python predict_cli.py "vs Lakers"  # Shows prediction vs Lakers
"""

import sys
import os
from datetime import datetime, timedelta
try:
    from tabulate import tabulate
except Exception:
    def tabulate(rows, headers='keys', tablefmt=None):
        # Minimal fallback: rows is a list of dicts
        if not rows:
            return ""
        keys = list(rows[0].keys())
        lines = [" | ".join(keys)]
        for r in rows:
            lines.append(" | ".join(str(r.get(k, '')) for k in keys))
        return "\n".join(lines)
import pandas as pd
from predictor import predict_game, init_model
from data.game_context_collector import GameToGameDataCollector

# Team name normalization
TEAM_NAMES = {
    'celtics': 'Boston Celtics',
    'lakers': 'Los Angeles Lakers',
    'warriors': 'Golden State Warriors',
    'heat': 'Miami Heat',
    'nuggets': 'Denver Nuggets',
    'suns': 'Phoenix Suns',
    'mavericks': 'Dallas Mavericks',
    'bucks': 'Milwaukee Bucks',
    'nets': 'Brooklyn Nets',
    'grizzlies': 'Memphis Grizzlies',
    '76ers': 'Philadelphia 76ers',
    'sixers': 'Philadelphia 76ers',
    'kings': 'Sacramento Kings',
    'hawks': 'Atlanta Hawks',
    'spurs': 'San Antonio Spurs',
    'trail blazers': 'Portland Trail Blazers',
    'timberwolves': 'Minnesota Timberwolves',
    'rockets': 'Houston Rockets',
    'pelicans': 'New Orleans Pelicans',
    'cavaliers': 'Cleveland Cavaliers',
    'pacers': 'Indiana Pacers',
    'raptors': 'Toronto Raptors',
    'bulls': 'Chicago Bulls',
    'pistons': 'Detroit Pistons',
    'knicks': 'New York Knicks',
    'clippers': 'Los Angeles Clippers',
    'thunder': 'Oklahoma City Thunder',
    'jazz': 'Utah Jazz',
    'hornets': 'Charlotte Hornets',
    'wizards': 'Washington Wizards',
}

def normalize_team(team_str):
    """Convert user input to full team name."""
    team_lower = team_str.lower().strip()
    return TEAM_NAMES.get(team_lower, None)

def get_upcoming_games(team_name, days_ahead=7):
    """Get upcoming games for a team (placeholder - would use nba_api)."""
    # This would normally pull from nba_api
    # For now, returning a sample structure
    games = []
    today = datetime.now()
    for i in range(1, 4):
        game_date = today + timedelta(days=i)
        games.append({
            'date': game_date.strftime('%Y-%m-%d'),
            'opponent': 'Sample Opponent',
            'home': i % 2 == 0,  # Alternate home/away
        })
    return games

def load_injuries():
    """Load current injuries from CSV."""
    injury_file = os.path.join(os.path.dirname(__file__), 'data', 'injury_reports', 'current_injuries.csv')
    try:
        df = pd.read_csv(injury_file)
        return df
    except:
        return pd.DataFrame()

def display_header():
    """Display fancy header."""
    print("\n" + "="*80)
    print("       NBA PARLAY MODEL - GAME PREDICTIONS")
    print("="*80 + "\n")

def display_team_predictions(team_name):
    """Show all upcoming games for a team with predictions."""
    display_header()
    
    print(f"📊 UPCOMING GAMES - {team_name.upper()}")
    print("-" * 80)
    
    # Load injuries
    injuries_df = load_injuries()
    team_injuries = injuries_df[injuries_df['team'] == team_name] if not injuries_df.empty else pd.DataFrame()
    
    if not team_injuries.empty:
        print(f"\n⚠️  INJURY ALERT for {team_name}:")
        for _, row in team_injuries.iterrows():
            status_emoji = {'OUT': '❌', 'QUESTIONABLE': '⚠️', 'PROBABLE': '✓', 'DOUBTFUL': '?'}.get(row['status'], '•')
            print(f"   {status_emoji} {row['player']} - {row['status']} ({row['details']})")
        print()
    
    # Get games
    games = get_upcoming_games(team_name)
    
    if not games:
        print(f"❌ No upcoming games found for {team_name}")
        return
    
    predictions = []
    
    for game in games:
        opponent = game['opponent']
        home_team = team_name if game['home'] else opponent
        away_team = opponent if game['home'] else team_name
        try:
            pred = predict_game(home_team, away_team)
            # predict_game returns a dict with probabilities in 0-1 range
            prob_home = pred['home_win_probability'] * 100
            prob_away = pred['away_win_probability'] * 100

            team_prob = prob_home if game['home'] else prob_away

            predictions.append({
                'Date': game['date'],
                'Matchup': f"{away_team} @ {home_team}" if game['home'] else f"{home_team} @ {away_team}",
                f'{team_name} Win %': f"{team_prob:.1f}%",
                'Confidence': get_confidence_level(team_prob),
                'Parlay Odds': f"{format_parlay_odds(team_prob)}"
            })
        except Exception as e:
            print(f"⚠️  Error predicting {opponent}: {str(e)}")
    
    if predictions:
        print(tabulate(predictions, headers='keys', tablefmt='grid'))
    
    print("\n" + "="*80)
    print("💡 Tips:")
    print("   • Green confidence = >55% win probability")
    print("   • Yellow confidence = 45-55% win probability")
    print("   • Red confidence = <45% win probability")
    print("   • Update data/injury_reports/current_injuries.csv for latest injuries")
    print("="*80 + "\n")

    # Also show next game detail + best bets
    if games:
        next_game = games[0]
        display_next_game_detail(team_name, next_game)

def get_confidence_level(prob):
    """Return confidence level emoji."""
    if prob > 55:
        return "🟢 High"
    elif prob < 45:
        return "🔴 Low"
    else:
        return "🟡 Medium"


def format_parlay_odds(prob_percent: float) -> str:
    """Rudimentary conversion from probability percent to American odds string."""
    p = prob_percent / 100.0
    if p <= 0 or p >= 1:
        return "—"
    if p >= 0.5:
        # Positive odds
        odds = int((p / (1 - p)) * 100)
        return f"+{odds}"
    else:
        odds = int((-(100 / (p * 100 - 100))))
        # fallback - show implied negative odds approximation
        try:
            neg = int((100 * (1 - p)) / p)
            return f"-{neg}"
        except Exception:
            return "—"


def compute_expected_margin(prob_percent: float) -> float:
    """Estimate expected point margin from win probability (heuristic)."""
    p = prob_percent / 100.0
    # Scale factor chosen conservatively; this is heuristic only
    return (p - 0.5) * 15.0


def compute_best_bets(team_name: str, opponent: str, team_prob: float, opp_prob: float) -> list:
    """Return list of best-bet suggestions with rationale."""
    bets = []
    margin = compute_expected_margin(team_prob)

    # Moneyline suggestion
    if team_prob >= 60.0:
        bets.append((f"Moneyline: Bet on {team_name}", f"Estimated win% {team_prob:.1f}%"))
    elif team_prob <= 40.0:
        bets.append((f"Moneyline: Bet on {opponent}", f"Estimated win% {opp_prob:.1f}%"))
    else:
        bets.append(("Moneyline: No clear edge", f"Estimated win% {team_prob:.1f}% vs {opp_prob:.1f}%"))

    # Spread suggestion (heuristic)
    if abs(margin) >= 6.0:
        fav = team_name if margin > 0 else opponent
        bets.append((f"Spread: Bet {fav} by {abs(margin):.1f} pts (pred)", "Strong predicted margin"))
    else:
        bets.append(("Spread: No confident pick", f"Predicted margin {margin:.1f} pts"))

    # Over/Under suggestion based on team averages if available
    bets.append(("Total: Consider market lines vs model (not available)", "Model doesn't fetch market totals yet"))

    return bets


def display_next_game_detail(team_name: str, game: dict):
    """Show detailed info for the next scheduled game and best bets."""
    opponent = game.get('opponent') if 'opponent' in game else (game.get('away_team') if game.get('home') else game.get('home_team'))
    is_home = game.get('home', True)
    home_team = team_name if is_home else opponent
    away_team = opponent if is_home else team_name
    date = game.get('date') or game.get('game_date')

    print("\n" + "~" * 80)
    print(f"NEXT GAME DETAIL: {team_name} vs {opponent} — {date} {'(HOME)' if is_home else '(AWAY)'}")

    # Game context (injuries etc.)
    context = GameToGameDataCollector.get_game_context(home_team, away_team, date)

    print("\nInjuries:")
    if context.get('home_injuries'):
        print(f"  Home ({home_team}):")
        for p in context['home_injuries']:
            print(f"    - {p.get('player') or p.get('name')} — {p.get('status')} ({p.get('details')})")
    else:
        print(f"  Home ({home_team}): None listed")

    if context.get('away_injuries'):
        print(f"  Away ({away_team}):")
        for p in context['away_injuries']:
            print(f"    - {p.get('player') or p.get('name')} — {p.get('status')} ({p.get('details')})")
    else:
        print(f"  Away ({away_team}): None listed")

    # Prediction and bets
    try:
        pred = predict_game(home_team, away_team, date)
        prob_home = pred['home_win_probability'] * 100
        prob_away = pred['away_win_probability'] * 100

        team_prob = prob_home if is_home else prob_away
        opp_prob = prob_away if is_home else prob_home

        print(f"\nModel Prediction:\n  {home_team}: {prob_home:.1f}%  |  {away_team}: {prob_away:.1f}%")

        bets = compute_best_bets(team_name, opponent, team_prob, opp_prob)
        print("\nBest Bets:")
        for title, reason in bets:
            print(f"  - {title} — {reason}")

    except Exception as e:
        print(f"\nPrediction error: {e}")

    print("~" * 80 + "\n")

def display_head_to_head(team1, team2):
    """Show prediction for specific matchup."""
    display_header()
    
    print(f"📊 HEAD-TO-HEAD: {team1} vs {team2}")
    print("-" * 80)
    try:
        pred = predict_game(team1, team2)
        prob_home = pred['home_win_probability'] * 100
        prob_away = pred['away_win_probability'] * 100

        matchup = [
            {'Team': team1, 'Win %': f"{prob_home:.1f}%", 'Confidence': get_confidence_level(prob_home)},
            {'Team': team2, 'Win %': f"{prob_away:.1f}%", 'Confidence': get_confidence_level(prob_away)},
        ]

        print(tabulate(matchup, headers='keys', tablefmt='grid'))
        print("\n" + "="*80 + "\n")

    except Exception as e:
        print(f"❌ Error: {str(e)}\n")

def main():
    if len(sys.argv) < 2:
        print("\n" + "="*80)
        print("Usage:")
        print("  python predict_cli.py 'Boston Celtics'      # Show all games for Celtics")
        print("  python predict_cli.py lakers                # Show all games for Lakers")
        print("  python predict_cli.py 'Celtics vs Lakers'  # Head-to-head prediction")
        print("="*80 + "\n")
        return
    
    user_input = ' '.join(sys.argv[1:])
    
    # Check for vs matchup
    if ' vs ' in user_input.lower():
        parts = [p.strip() for p in user_input.lower().split(' vs ')]
        team1 = normalize_team(parts[0])
        team2 = normalize_team(parts[1])
        
        if team1 and team2:
            display_head_to_head(team1, team2)
        else:
            print(f"❌ Team not recognized: {user_input}")
    else:
        # Single team
        team_name = normalize_team(user_input)
        
        if team_name:
            display_team_predictions(team_name)
        else:
            print(f"❌ Team not recognized: {user_input}")
            print(f"\nAvailable teams: {', '.join(sorted(set(TEAM_NAMES.values())))}\n")

if __name__ == '__main__':
    main()
