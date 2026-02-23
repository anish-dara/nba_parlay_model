"""Test what stats ESPN provides in standings"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.espn_stats_scraper import get_standings
import json

standings = get_standings()

print("\n" + "="*70)
print("ESPN STANDINGS - ALL AVAILABLE STATS")
print("="*70)

for conf in ['East', 'West']:
    print(f"\n{conf}ern Conference - First Team:")
    if standings.get(conf):
        first_team = standings[conf][0]
        print(f"\nTeam: {first_team['team']}")
        print("\nAll available stats:")
        for key, value in first_team.items():
            print(f"  {key}: {value}")

print("\n" + "="*70)
print("FULL JSON OUTPUT (first team from each conference):")
print("="*70)
for conf in ['East', 'West']:
    if standings.get(conf):
        print(f"\n{conf}:")
        print(json.dumps(standings[conf][0], indent=2))
