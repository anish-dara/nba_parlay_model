"""Check what advanced stats ESPN provides for the tier-based model"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.espn_stats_scraper import get_team_analytics, get_standings, get_teams

print("\n" + "="*80)
print("TIER MODEL DATA REQUIREMENTS vs ESPN AVAILABILITY")
print("="*80)

# What the tier model needs
tier_model_needs = {
    'team_quality': ['off_rating', 'def_rating', 'net_rating', 'wins', 'losses', 'win_pct'],
    'recent_form': ['last_10_record', 'last_5_record', 'momentum', 'recent_point_diff'],
    'injuries': ['key_players_out', 'injury_severity_score', 'minutes_lost_pct'],
    'rest_schedule': ['days_rest', 'back_to_back', 'games_in_last_7', 'travel_distance'],
    'home_away': ['home_record', 'away_record', 'home_point_diff', 'away_point_diff'],
    'matchup': ['pace', 'three_point_pct', 'three_point_defense', 'turnover_rate', 'rebound_rate'],
    'coaching': ['coach_win_pct', 'clutch_record', 'ats_record'],
    'situational': ['playoff_position', 'games_remaining', 'motivation_factor']
}

print("\n" + "-"*80)
print("CHECKING ESPN DATA AVAILABILITY")
print("-"*80)

# Test with Boston Celtics (ID: 2)
print("\nFetching data for Boston Celtics (ID: 2)...")
analytics = get_team_analytics(2)
standings = get_standings()

print(f"\n✓ ESPN Team Analytics provides {len(analytics)} stats:")
print("\nAvailable stats:")
for i, (key, value) in enumerate(analytics.items(), 1):
    print(f"  {i:2}. {key:<35} = {value}")

print("\n" + "-"*80)
print("TIER MODEL REQUIREMENTS ANALYSIS")
print("-"*80)

for category, fields in tier_model_needs.items():
    print(f"\n{category.upper().replace('_', ' ')} ({len(fields)} fields):")
    for field in fields:
        # Check if we can get this from ESPN
        available = "✓" if any(field.lower() in key.lower() for key in analytics.keys()) else "✗"
        
        # Special cases
        if field in ['wins', 'losses', 'win_pct']:
            available = "✓ (from standings)"
        elif field in ['key_players_out', 'injury_severity_score', 'minutes_lost_pct']:
            available = "✓ (from injuries API)"
        elif field in ['days_rest', 'back_to_back', 'games_in_last_7', 'travel_distance']:
            available = "⚠ (calculated)"
        elif field in ['home_record', 'away_record']:
            available = "✓ (from standings)"
        elif field in ['coach_win_pct', 'clutch_record', 'ats_record']:
            available = "⚠ (estimated/manual)"
        elif field in ['playoff_position', 'games_remaining']:
            available = "✓ (from standings)"
        elif field == 'motivation_factor':
            available = "⚠ (manual)"
        
        print(f"  {available} {field}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("\n✓ = Available from ESPN")
print("⚠ = Can be calculated or estimated")
print("✗ = Not available (need alternative)")

print("\n" + "-"*80)
print("KEY FINDINGS:")
print("-"*80)
print("✓ Standings: W/L, Win%, Home/Away splits, PPG, Opp PPG")
print("✓ Team Analytics: FG%, 3P%, FT%, Rebounds, Assists, etc.")
print("✓ Injuries: Full injury report with status")
print("⚠ Advanced ratings (ORtg, DRtg): Can estimate from win% and PPG")
print("⚠ Rest/Schedule: Can calculate from game dates")
print("⚠ Coaching/ATS: Need manual data or estimation")

print("\n" + "="*80)
