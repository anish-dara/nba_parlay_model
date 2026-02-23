"""
Debug script to verify injury data is being loaded and applied correctly.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from models.team_data_loader import TeamDataLoader
import pandas as pd


def main():
    print("\n" + "="*70)
    print("INJURY DATA DEBUG")
    print("="*70)
    
    loader = TeamDataLoader()
    
    # Check if injury files exist
    injury_file = Path("data/injury_reports/current_injuries.csv")
    impact_file = Path("data/injury_reports/injury_impact.csv")
    
    print(f"\n1. Checking files:")
    print(f"   current_injuries.csv: {'✓ EXISTS' if injury_file.exists() else '✗ MISSING'}")
    print(f"   injury_impact.csv: {'✓ EXISTS' if impact_file.exists() else '✗ MISSING'}")
    
    # Load data
    print(f"\n2. Loading data...")
    loader.load_all_data()
    
    # Check raw injuries
    if loader._injuries is not None and not loader._injuries.empty:
        print(f"\n3. Raw Injuries Loaded:")
        print(f"   Total injuries: {len(loader._injuries)}")
        print(f"   Teams with injuries: {loader._injuries['team'].nunique()}")
        print(f"\n   Status breakdown:")
        print(loader._injuries['status'].value_counts())
        
        print(f"\n   Sample injuries:")
        print(loader._injuries.head(10)[['team', 'player', 'status', 'injury_type']])
    else:
        print(f"\n3. ✗ No raw injury data loaded")
        print(f"   Run: python data/espn_injury_collector.py")
    
    # Check injury impact
    if loader._injury_impact is not None and not loader._injury_impact.empty:
        print(f"\n4. Injury Impact Loaded:")
        print(f"   Teams: {len(loader._injury_impact)}")
        print(f"\n   Top 5 teams by severity:")
        top_injuries = loader._injury_impact.sort_values('severity_score', ascending=False).head(5)
        print(top_injuries[['team', 'key_players_out', 'severity_score']])
    else:
        print(f"\n4. ✗ No injury impact data loaded")
    
    # Test team factors
    print(f"\n5. Testing TeamFactors for teams with injuries:")
    
    if loader._injuries is not None and not loader._injuries.empty:
        # Get teams with most injuries
        injury_counts = loader._injuries.groupby('team').size().sort_values(ascending=False)
        test_teams = injury_counts.head(3).index.tolist()
        
        for team in test_teams:
            try:
                factors = loader.get_team_factors(team)
                team_injuries = loader._injuries[loader._injuries['team'] == team]
                
                print(f"\n   {team}:")
                print(f"     Raw injuries in CSV: {len(team_injuries)}")
                print(f"     Key players out (TeamFactors): {factors.key_players_out}")
                print(f"     Injury severity score: {factors.injury_severity_score:.1f}")
                print(f"     Minutes lost %: {factors.minutes_lost_pct:.1%}")
                
                # Show which players are out
                out_players = team_injuries[team_injuries['status'].str.contains('Out', case=False, na=False)]
                if not out_players.empty:
                    print(f"     Players OUT:")
                    for _, p in out_players.iterrows():
                        print(f"       - {p['player']} ({p['status']})")
            except Exception as e:
                print(f"   ✗ Error loading {team}: {e}")
    else:
        print(f"   ✗ No injury data to test")
    
    print("\n" + "="*70)
    print("DIAGNOSIS:")
    print("="*70)
    
    if injury_file.exists() and loader._injuries is not None and not loader._injuries.empty:
        print("✓ Injury data is being collected and loaded")
        print("✓ TeamFactors should include injury impact")
        print("\nIf predictions still don't show injuries:")
        print("  1. Make sure you ran: python collect_all_data.py")
        print("  2. Check team names match exactly (case-sensitive)")
        print("  3. Run: python test_tier_integration.py")
    else:
        print("✗ Injury data is NOT being loaded")
        print("\nTo fix:")
        print("  1. Run: python data/espn_injury_collector.py")
        print("  2. Or run: python collect_all_data.py")
        print("  3. Then test again")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
