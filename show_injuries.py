"""Show all active NBA injuries from ESPN"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.espn_stats_scraper import get_injuries

print("\n" + "="*80)
print("NBA INJURY REPORT - ALL ACTIVE INJURIES")
print("="*80)

injuries = get_injuries()

if not injuries:
    print("\n  No injury data available from ESPN API")
    print("  (Endpoint may require authentication or be temporarily unavailable)")
else:
    # Group by status
    by_status = {}
    for inj in injuries:
        status = inj.get("status", "Unknown")
        by_status.setdefault(status, []).append(inj)
    
    # Show each status category
    for status in ["Out", "Out For Season", "Out Indefinitely", "Doubtful", "Questionable", "Day-To-Day"]:
        if status in by_status:
            print(f"\n{'─'*80}")
            print(f"{status.upper()} ({len(by_status[status])} players)")
            print(f"{'─'*80}")
            print(f"{'TEAM':<6} {'PLAYER':<28} {'POS':<5} {'INJURY':<30}")
            print(f"{'─'*80}")
            
            for inj in by_status[status]:
                team = inj.get('team_abbr', '???')
                player = inj.get('player', 'Unknown')[:27]
                pos = inj.get('position', '?')
                
                # Build injury description
                injury_parts = []
                if inj.get('side'):
                    injury_parts.append(inj['side'])
                if inj.get('detail'):
                    injury_parts.append(inj['detail'])
                elif inj.get('type'):
                    injury_parts.append(inj['type'])
                
                injury_desc = ' '.join(injury_parts)[:29]
                
                print(f"{team:<6} {player:<28} {pos:<5} {injury_desc:<30}")
    
    # Show any other statuses
    other_statuses = [s for s in by_status.keys() 
                     if s not in ["Out", "Out For Season", "Out Indefinitely", 
                                  "Doubtful", "Questionable", "Day-To-Day"]]
    
    for status in other_statuses:
        print(f"\n{'─'*80}")
        print(f"{status.upper()} ({len(by_status[status])} players)")
        print(f"{'─'*80}")
        for inj in by_status[status]:
            print(f"  {inj.get('team_abbr', '???'):<6} {inj.get('player', 'Unknown'):<28} "
                  f"{inj.get('position', '?'):<5} {inj.get('detail', '')}")
    
    print(f"\n{'='*80}")
    print(f"TOTAL INJURIES: {len(injuries)} players")
    print(f"{'='*80}\n")
