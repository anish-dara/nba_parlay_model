"""
Generate predictions for all NBA games on specific dates.

Usage:
    python predict_date_range.py 2025-02-19 2025-02-21
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from predictor import predict_game, init_model, format_prediction


def fetch_schedule_for_dates(start_date: str, end_date: str):
    """
    Fetch NBA schedule for date range from NBA API.
    """
    try:
        from nba_api.live.nba.endpoints import scoreboard
        
        games = []
        current = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            try:
                # Fetch games for this date
                board = scoreboard.ScoreBoard()
                data = board.get_dict()
                
                if 'scoreboard' in data and 'games' in data['scoreboard']:
                    for game in data['scoreboard']['games']:
                        home_team = game['homeTeam']['teamName']
                        away_team = game['awayTeam']['teamName']
                        
                        games.append({
                            'date': date_str,
                            'home': home_team,
                            'away': away_team
                        })
            except Exception as e:
                print(f"  Warning: Could not fetch games for {date_str}: {e}")
            
            current += timedelta(days=1)
        
        return games
        
    except ImportError:
        print("  nba_api.live not available, using sample schedule")
        # Fallback to sample schedule
        return [
            # Feb 19, 2026
            {"date": "2026-02-19", "home": "Boston Celtics", "away": "Los Angeles Lakers"},
            {"date": "2026-02-19", "home": "Golden State Warriors", "away": "Denver Nuggets"},
            {"date": "2026-02-19", "home": "Miami Heat", "away": "Milwaukee Bucks"},
            {"date": "2026-02-19", "home": "Phoenix Suns", "away": "Dallas Mavericks"},
            {"date": "2026-02-19", "home": "New York Knicks", "away": "Philadelphia 76ers"},
            
            # Feb 20, 2026
            {"date": "2026-02-20", "home": "Brooklyn Nets", "away": "Atlanta Hawks"},
            {"date": "2026-02-20", "home": "Chicago Bulls", "away": "Toronto Raptors"},
            {"date": "2026-02-20", "home": "Cleveland Cavaliers", "away": "Detroit Pistons"},
            {"date": "2026-02-20", "home": "Indiana Pacers", "away": "Charlotte Hornets"},
            {"date": "2026-02-20", "home": "Houston Rockets", "away": "San Antonio Spurs"},
            
            # Feb 21, 2026
            {"date": "2026-02-21", "home": "Los Angeles Clippers", "away": "Sacramento Kings"},
            {"date": "2026-02-21", "home": "Portland Trail Blazers", "away": "Utah Jazz"},
            {"date": "2026-02-21", "home": "Oklahoma City Thunder", "away": "Memphis Grizzlies"},
            {"date": "2026-02-21", "home": "Minnesota Timberwolves", "away": "New Orleans Pelicans"},
            {"date": "2026-02-21", "home": "Washington Wizards", "away": "Orlando Magic"},
        ]


def generate_predictions_for_dates(start_date: str, end_date: str):
    """Generate predictions for all games in date range"""
    
    print("\n" + "="*80)
    print(f"NBA GAME PREDICTIONS: {start_date} to {end_date}")
    print("="*80)
    
    # Initialize model
    print("\nInitializing prediction model...")
    try:
        init_model()
        print("✓ Model ready\n")
    except Exception as e:
        print(f"✗ Model initialization failed: {e}")
        print("\nMake sure you've run: python collect_all_data.py")
        return
    
    # Fetch schedule
    print(f"Fetching schedule for {start_date} to {end_date}...")
    games = fetch_schedule_for_dates(start_date, end_date)
    
    if not games:
        print(f"✗ No games found for this date range")
        print("\nNote: Sample schedule only includes Feb 19-21, 2025")
        return
    
    print(f"✓ Found {len(games)} games\n")
    
    # Generate predictions
    predictions = []
    
    for game in games:
        try:
            pred = predict_game(game['home'], game['away'], game['date'])
            predictions.append(pred)
        except Exception as e:
            print(f"✗ Failed to predict {game['home']} vs {game['away']}: {e}")
    
    # Display results
    print("="*80)
    print("PREDICTIONS")
    print("="*80)
    
    # Group by date
    by_date = {}
    for pred in predictions:
        date = pred['game_date']
        if date not in by_date:
            by_date[date] = []
        by_date[date].append(pred)
    
    # Display each date
    for date in sorted(by_date.keys()):
        print(f"\n{'='*80}")
        print(f"📅 {date}")
        print('='*80)
        
        for pred in by_date[date]:
            print(f"\n{pred['home_team']} vs {pred['away_team']}")
            print(f"  {'HOME':15s} {pred['home_win_probability']:6.1%}")
            print(f"  {'AWAY':15s} {pred['away_win_probability']:6.1%}")
            print(f"  Prediction: {pred['predicted_winner']} (confidence: {pred['confidence']:5.1%})")
            
            # Show key factors
            if 'model_features' in pred:
                features = pred['model_features']
                if 'home_tier' in features:
                    print(f"  Tiers: {features['home_tier']} vs {features['away_tier']}")
                if 'home_injuries' in features:
                    if features['home_injuries'] > 0 or features['away_injuries'] > 0:
                        print(f"  Injuries: {features['home_injuries']} vs {features['away_injuries']}")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total games predicted: {len(predictions)}")
    print(f"Model type: {predictions[0].get('model_type', 'unknown') if predictions else 'N/A'}")
    
    # High confidence picks
    high_conf = [p for p in predictions if p['confidence'] > 0.30]
    if high_conf:
        print(f"\nHigh confidence picks (>30%):")
        for p in sorted(high_conf, key=lambda x: x['confidence'], reverse=True)[:5]:
            print(f"  {p['predicted_winner']:25s} {p['home_win_probability']:5.1%} (vs {p['away_team'] if p['predicted_winner'] == p['home_team'] else p['home_team']})")
    
    # Save to CSV
    output_file = f"predictions_{start_date}_to_{end_date}.csv"
    df = pd.DataFrame([{
        'date': p['game_date'],
        'home_team': p['home_team'],
        'away_team': p['away_team'],
        'home_win_prob': p['home_win_probability'],
        'away_win_prob': p['away_win_probability'],
        'predicted_winner': p['predicted_winner'],
        'confidence': p['confidence'],
        'model_type': p.get('model_type', 'unknown')
    } for p in predictions])
    
    df.to_csv(output_file, index=False)
    print(f"\n✓ Predictions saved to: {output_file}")
    print("="*80 + "\n")


def main():
    if len(sys.argv) < 3:
        print("\nUsage: python predict_date_range.py START_DATE END_DATE")
        print("Example: python predict_date_range.py 2026-02-19 2026-02-21")
        print("\nNote: Will attempt to fetch real schedule from NBA API.")
        print("      Falls back to sample schedule if API unavailable.\n")
        return
    
    start_date = sys.argv[1]
    end_date = sys.argv[2]
    
    # Validate dates
    try:
        pd.to_datetime(start_date)
        pd.to_datetime(end_date)
    except:
        print(f"\n✗ Invalid date format. Use YYYY-MM-DD")
        print(f"Example: 2026-02-19\n")
        return
    
    generate_predictions_for_dates(start_date, end_date)


if __name__ == "__main__":
    # If no args, use today's date (Feb 19-21, 2026)
    if len(sys.argv) == 1:
        print("\nNo dates provided. Using: 2026-02-19 to 2026-02-21")
        sys.argv = ["predict_date_range.py", "2026-02-19", "2026-02-21"]
    
    main()
