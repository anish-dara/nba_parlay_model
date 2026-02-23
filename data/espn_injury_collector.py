"""
Collect NBA injury data from ESPN's unofficial API (FREE).

Fetches current injury reports for all teams.
"""

import requests
import pandas as pd
import logging
from typing import Dict, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ESPN team IDs mapping
ESPN_TEAM_IDS = {
    'Atlanta Hawks': 1, 'Boston Celtics': 2, 'Brooklyn Nets': 17,
    'Charlotte Hornets': 30, 'Chicago Bulls': 4, 'Cleveland Cavaliers': 5,
    'Dallas Mavericks': 6, 'Denver Nuggets': 7, 'Detroit Pistons': 8,
    'Golden State Warriors': 9, 'Houston Rockets': 10, 'Indiana Pacers': 11,
    'LA Clippers': 12, 'Los Angeles Lakers': 13, 'Memphis Grizzlies': 29,
    'Miami Heat': 14, 'Milwaukee Bucks': 15, 'Minnesota Timberwolves': 16,
    'New Orleans Pelicans': 3, 'New York Knicks': 18, 'Oklahoma City Thunder': 25,
    'Orlando Magic': 19, 'Philadelphia 76ers': 20, 'Phoenix Suns': 21,
    'Portland Trail Blazers': 22, 'Sacramento Kings': 23, 'San Antonio Spurs': 24,
    'Toronto Raptors': 28, 'Utah Jazz': 26, 'Washington Wizards': 27
}


class ESPNInjuryCollector:
    """Collect injury data from ESPN's unofficial API"""
    
    # Try multiple endpoints
    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/injuries"
    ALT_URL = "http://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}"
    SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_team_injuries(self, team_id: int, team_name: str = "") -> List[Dict]:
        """
        Fetch injuries for a specific team - tries multiple sources
        
        Args:
            team_id: ESPN team ID
            team_name: Team name for logging
            
        Returns:
            List of injury dicts
        """
        # Try primary endpoint
        url = self.BASE_URL.format(team_id=team_id)
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            injuries = []
            if 'injuries' in data and data['injuries']:
                for injury in data['injuries']:
                    athlete = injury.get('athlete', {})
                    status = injury.get('status', 'Unknown')
                    details = injury.get('details', {})
                    
                    injuries.append({
                        'player': athlete.get('displayName', 'Unknown'),
                        'position': athlete.get('position', {}).get('abbreviation', ''),
                        'status': status,
                        'type': details.get('type', ''),
                        'detail': details.get('detail', ''),
                        'side': details.get('side', ''),
                        'date': injury.get('date', '')
                    })
                return injuries
            
            # Try alternative endpoint (team roster with injury status)
            alt_url = self.ALT_URL.format(team_id=team_id)
            response = self.session.get(alt_url, timeout=10)
            data = response.json()
            
            if 'team' in data and 'injuries' in data['team']:
                for injury in data['team']['injuries']:
                    athlete = injury.get('athlete', {})
                    injuries.append({
                        'player': athlete.get('displayName', 'Unknown'),
                        'position': athlete.get('position', {}).get('abbreviation', ''),
                        'status': injury.get('status', 'Unknown'),
                        'type': injury.get('details', {}).get('type', ''),
                        'detail': injury.get('details', {}).get('detail', ''),
                        'side': injury.get('details', {}).get('side', ''),
                        'date': injury.get('date', '')
                    })
            
            return injuries
            
        except Exception as e:
            logger.warning(f"Failed to fetch injuries for {team_name}: {e}")
            return []
    
    def fetch_all_injuries(self) -> pd.DataFrame:
        """
        Fetch injuries for all NBA teams
        
        Returns:
            DataFrame with columns: team, player, position, status, type, detail
        """
        logger.info("Fetching injuries from ESPN API...")
        
        all_injuries = []
        
        for team_name, team_id in ESPN_TEAM_IDS.items():
            injuries = self.fetch_team_injuries(team_id, team_name)
            
            for injury in injuries:
                all_injuries.append({
                    'team': team_name,
                    'player': injury['player'],
                    'position': injury['position'],
                    'status': injury['status'],
                    'injury_type': injury['type'],
                    'details': f"{injury['side']} {injury['detail']}".strip(),
                    'date_updated': datetime.now().strftime('%Y-%m-%d')
                })
            
            if injuries:
                logger.info(f"{team_name}: {len(injuries)} injuries")
        
        # If ESPN fails completely, create sample data so model doesn't crash
        if not all_injuries:
            logger.warning("ESPN API returned 0 injuries - creating sample data")
            # Add a few sample injuries so the model has something to work with
            all_injuries = [
                {'team': 'Los Angeles Lakers', 'player': 'Sample Player 1', 'position': 'G', 
                 'status': 'Out', 'injury_type': 'Knee', 'details': 'Left knee', 
                 'date_updated': datetime.now().strftime('%Y-%m-%d')},
                {'team': 'Golden State Warriors', 'player': 'Sample Player 2', 'position': 'F',
                 'status': 'Questionable', 'injury_type': 'Ankle', 'details': 'Right ankle',
                 'date_updated': datetime.now().strftime('%Y-%m-%d')},
            ]
            logger.warning("Using sample injury data - UPDATE MANUALLY for real predictions")
        
        df = pd.DataFrame(all_injuries)
        logger.info(f"Total injuries collected: {len(df)}")
        
        return df
    
    def calculate_injury_impact(self, injuries_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate injury impact scores for each team
        MASSIVELY INCREASED - losing stars is devastating
        
        Returns:
            DataFrame with team-level injury metrics
        """
        if injuries_df.empty:
            return pd.DataFrame()
        
        # Count injuries by status
        impact = injuries_df.groupby(['team', 'status']).size().unstack(fill_value=0)
        
        # Calculate severity score (0-30+ scale)
        # ASSUME ANY "OUT" PLAYER IS A STAR (we don't have usage data)
        severity_weights = {
            'Out': 8.0,  # Was 3.0 - assume star player
            'Day-To-Day': 1.5,  # Was 1.0
            'Questionable': 2.5,  # Was 1.5
            'Doubtful': 4.0,  # Was 2.0
            'Out For Season': 12.0,  # Was 5.0 - franchise player gone
            'Out Indefinitely': 10.0,  # Was 4.0
        }
        
        impact['severity_score'] = 0.0
        for status, weight in severity_weights.items():
            if status in impact.columns:
                impact['severity_score'] += impact[status] * weight
        
        # Count key players (starters typically)
        impact['key_players_out'] = impact.get('Out', 0) + impact.get('Out For Season', 0)
        
        impact = impact.reset_index()
        
        return impact
    
    def save_injuries(self, output_path: str = "data/injury_reports/current_injuries.csv"):
        """Fetch and save current injuries to CSV"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Try ESPN API first
        injuries_df = self.fetch_all_injuries()
        
        # If ESPN fails, try loading manual CSV
        if injuries_df.empty or len(injuries_df) < 5:
            manual_path = "data/injury_reports/manual_injuries.csv"
            if Path(manual_path).exists():
                logger.warning(f"ESPN API failed, loading manual injuries from {manual_path}")
                injuries_df = pd.read_csv(manual_path)
                logger.info(f"Loaded {len(injuries_df)} manual injuries")
        
        if not injuries_df.empty:
            injuries_df.to_csv(output_path, index=False)
            logger.info(f"Saved {len(injuries_df)} injuries to {output_path}")
            
            # Also save impact summary
            impact_df = self.calculate_injury_impact(injuries_df)
            impact_path = output_path.replace('current_injuries', 'injury_impact')
            impact_df.to_csv(impact_path, index=False)
            logger.info(f"Saved injury impact to {impact_path}")
            
            return injuries_df, impact_df
        else:
            logger.error("No injuries available - create data/injury_reports/manual_injuries.csv")
            return pd.DataFrame(), pd.DataFrame()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    collector = ESPNInjuryCollector()
    injuries_df, impact_df = collector.save_injuries()
    
    if not injuries_df.empty:
        print("\n" + "="*70)
        print("INJURY REPORT SUMMARY")
        print("="*70)
        print(f"\nTotal injuries: {len(injuries_df)}")
        print(f"\nBy status:")
        print(injuries_df['status'].value_counts())
        print(f"\nTeams with most injuries:")
        print(injuries_df['team'].value_counts().head(5))
        
        print("\n" + "="*70)
        print("INJURY IMPACT BY TEAM")
        print("="*70)
        print(impact_df.sort_values('severity_score', ascending=False).head(10))
