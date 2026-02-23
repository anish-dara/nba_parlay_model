"""Check team names in data."""
import pandas as pd

df = pd.read_csv('data/processed/historical_games.csv')
teams = sorted(pd.concat([df['home_team'], df['away_team']]).unique())

print('Teams in historical data:')
for i, team in enumerate(teams, 1):
    print(f"  {i:2d}. {team}")

print(f'\nTotal: {len(teams)} teams')

# Test with actual teams
print("\n\nSample games:")
print(df[['home_team', 'away_team', 'home_score', 'away_score']].head(5))
