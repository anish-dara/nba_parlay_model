"""Debug ESPN API responses"""

import requests
import json

BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

print("\n" + "="*70)
print("TESTING ESPN API ENDPOINTS")
print("="*70)

# Test standings
print("\n1. Testing standings endpoint...")
url = f"{BASE_URL}/standings"
try:
    resp = requests.get(url, headers=HEADERS, timeout=10)
    print(f"Status: {resp.status_code}")
    data = resp.json()
    print(f"Keys in response: {list(data.keys())}")
    
    # Save to file for inspection
    with open('espn_standings_raw.json', 'w') as f:
        json.dump(data, f, indent=2)
    print("✓ Saved raw response to espn_standings_raw.json")
    
    # Check structure
    if 'children' in data:
        print(f"  - Found {len(data['children'])} children")
        for child in data['children'][:2]:
            print(f"    - {child.get('name')}: {len(child.get('standings', {}).get('entries', []))} teams")
except Exception as e:
    print(f"✗ Error: {e}")

# Test teams
print("\n2. Testing teams endpoint...")
url = f"{BASE_URL}/teams"
try:
    resp = requests.get(url, headers=HEADERS, params={"limit": 40}, timeout=10)
    print(f"Status: {resp.status_code}")
    data = resp.json()
    print(f"Keys in response: {list(data.keys())}")
    
    # Count teams
    team_count = 0
    for sport in data.get("sports", []):
        for league in sport.get("leagues", []):
            team_count += len(league.get("teams", []))
    print(f"  - Found {team_count} teams")
except Exception as e:
    print(f"✗ Error: {e}")

# Test scoreboard
print("\n3. Testing scoreboard endpoint...")
url = f"{BASE_URL}/scoreboard"
try:
    resp = requests.get(url, headers=HEADERS, timeout=10)
    print(f"Status: {resp.status_code}")
    data = resp.json()
    print(f"Keys in response: {list(data.keys())}")
    print(f"  - Found {len(data.get('events', []))} games")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "="*70)
print("Check espn_standings_raw.json to see full structure")
print("="*70 + "\n")
