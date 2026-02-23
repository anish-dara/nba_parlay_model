import pandas as pd
import logging
from analysis.matchup_index import MatchupIndexBuilder

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

# Load historical games
games_df = pd.read_csv('data/processed/historical_games.csv')
print(f"Total games loaded: {len(games_df)}")
print(f"\nFirst 5 rows:")
print(games_df.head())
print(f"\nColumns: {games_df.columns.tolist()}")

# Build matchup index
builder = MatchupIndexBuilder(games_df)

# Get stats for key teams
teams = ['Boston Celtics', 'Los Angeles Lakers', 'Golden State Warriors', 'Denver Nuggets']

for team in teams:
    stats = builder._compute_team_stats(team)
    print(f"\n{team}:")
    print(f"  PPG: {stats.get('ppg', 'N/A')}")
    print(f"  PPG Allowed: {stats.get('ppg_allowed', 'N/A')}")
    print(f"  Position Stats: {stats.get('position_stats', {})}")
