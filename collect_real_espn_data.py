"""
ESPN data collector - ONLY uses verified working endpoints with real data.
NO placeholders, NO estimates. If data doesn't exist, we skip it.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.espn_stats_scraper import get_scoreboard, get_injuries, get_teams, get_team_analytics
import pandas as pd

print("\n" + "="*80)
print("ESPN DATA COLLECTION - REAL DATA ONLY")
print("="*80)

# 1. Get team records from scoreboard (VERIFIED WORKING)
print("\n1. Extracting team records from today's scoreboard...")
games = get_scoreboard()
team_records = {}

for game in games:
    home_team = game['home_team']
    home_record = game.get('home_record', '')
    if home_record and '-' in home_record:
        wins, losses = home_record.split('-')
        team_records[home_team] = {
            'wins': int(wins),
            'losses': int(losses),
            'win_pct': int(wins) / (int(wins) + int(losses))
        }
    
    away_team = game['away_team']
    away_record = game.get('away_record', '')
    if away_record and '-' in away_record:
        wins, losses = away_record.split('-')
        team_records[away_team] = {
            'wins': int(wins),
            'losses': int(losses),
            'win_pct': int(wins) / (int(wins) + int(losses))
        }

print(f"✓ Extracted records for {len(team_records)} teams")

# 2. Get all teams (VERIFIED WORKING)
print("\n2. Getting team list...")
all_teams = get_teams()
print(f"✓ Found {len(all_teams)} teams")

# 3. Get team analytics for each team (VERIFIED WORKING)
print("\n3. Collecting team analytics from ESPN...")
team_data = []

for team in all_teams:
    team_name = team['name']
    team_id = team['id']
    
    # Get record if available
    record = team_records.get(team_name)
    if not record:
        print(f"  ⚠ Skipping {team_name} - no record data from today's games")
        continue
    
    # Get analytics (REAL DATA from ESPN)
    analytics = get_team_analytics(team_id)
    if not analytics:
        print(f"  ⚠ Skipping {team_name} - no analytics available")
        continue
    
    # Build team data using ONLY real ESPN data
    team_data.append({
        'team_id': team_id,
        'team_name': team_name,
        'wins': record['wins'],
        'losses': record['losses'],
        'win_pct': round(record['win_pct'], 3),
        'ppg': analytics.get('PPG'),
        'fg_pct': analytics.get('FG%'),
        'three_pct': analytics.get('3P%'),
        'ft_pct': analytics.get('FT%'),
        'rpg': analytics.get('RPG'),
        'apg': analytics.get('APG'),
        'topg': analytics.get('TOPG'),
        'spg': analytics.get('SPG'),
        'bpg': analytics.get('BPG'),
    })

df = pd.DataFrame(team_data)
print(f"✓ Collected REAL data for {len(df)} teams")

# 4. Get injuries (VERIFIED WORKING)
print("\n4. Collecting injuries...")
injuries = get_injuries()
print(f"✓ Found {len(injuries)} injuries")

# Save
output_dir = Path('data/processed')
output_dir.mkdir(parents=True, exist_ok=True)

if not df.empty:
    df.to_csv(output_dir / 'espn_team_stats.csv', index=False)
    print(f"\n✓ Saved to {output_dir / 'espn_team_stats.csv'}")
else:
    print("\n✗ No team data collected")

if injuries:
    injury_df = pd.DataFrame(injuries)
    injury_df.to_csv(output_dir / 'espn_injuries.csv', index=False)
    print(f"✓ Saved to {output_dir / 'espn_injuries.csv'}")

print("\n" + "="*80)
print("SUMMARY - REAL ESPN DATA")
print("="*80)
print(f"Teams with complete data: {len(df)}")
print(f"Injuries: {len(injuries)}")

if not df.empty:
    print("\nSample (first 5 teams):")
    print(df[['team_name', 'wins', 'losses', 'ppg', 'fg_pct', 'three_pct']].head())

print("\n" + "="*80)
print("NOTE: Only teams playing today have records.")
print("For full standings, ESPN API doesn't provide it.")
print("="*80 + "\n")
