"""
Analyze NBA schedule for rest days, back-to-backs, and travel distance.

Uses team city coordinates to calculate travel miles (FREE).
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

# Team city coordinates (latitude, longitude)
TEAM_LOCATIONS = {
    'Atlanta Hawks': (33.7573, -84.3963),
    'Boston Celtics': (42.3662, -71.0621),
    'Brooklyn Nets': (40.6826, -73.9754),
    'Charlotte Hornets': (35.2251, -80.8392),
    'Chicago Bulls': (41.8807, -87.6742),
    'Cleveland Cavaliers': (41.4965, -81.6882),
    'Dallas Mavericks': (32.7905, -96.8103),
    'Denver Nuggets': (39.7487, -105.0077),
    'Detroit Pistons': (42.3410, -83.0550),
    'Golden State Warriors': (37.7680, -122.3878),
    'Houston Rockets': (29.7508, -95.3621),
    'Indiana Pacers': (39.7640, -86.1555),
    'LA Clippers': (34.0430, -118.2673),
    'Los Angeles Lakers': (34.0430, -118.2673),
    'Memphis Grizzlies': (35.1382, -90.0505),
    'Miami Heat': (25.7814, -80.1870),
    'Milwaukee Bucks': (43.0436, -87.9170),
    'Minnesota Timberwolves': (44.9795, -93.2760),
    'New Orleans Pelicans': (29.9490, -90.0821),
    'New York Knicks': (40.7505, -73.9934),
    'Oklahoma City Thunder': (35.4634, -97.5151),
    'Orlando Magic': (28.5392, -81.3839),
    'Philadelphia 76ers': (39.9012, -75.1720),
    'Phoenix Suns': (33.4457, -112.0712),
    'Portland Trail Blazers': (45.5316, -122.6668),
    'Sacramento Kings': (38.5802, -121.4997),
    'San Antonio Spurs': (29.4270, -98.4375),
    'Toronto Raptors': (43.6435, -79.3791),
    'Utah Jazz': (40.7683, -111.9011),
    'Washington Wizards': (38.8981, -77.0209)
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points on Earth in miles
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
        
    Returns:
        Distance in miles
    """
    # Earth radius in miles
    R = 3959.0
    
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    
    return R * c


class ScheduleAnalyzer:
    """Analyze NBA schedule for rest and travel factors"""
    
    def __init__(self, games_df: pd.DataFrame):
        """
        Args:
            games_df: DataFrame with columns: game_date, home_team, away_team
        """
        self.games_df = games_df.copy()
        self.games_df['game_date'] = pd.to_datetime(self.games_df['game_date'])
        self.games_df = self.games_df.sort_values('game_date')
    
    def calculate_days_rest(self, team: str, game_date: pd.Timestamp) -> int:
        """
        Calculate days of rest before a game
        
        Args:
            team: Team name
            game_date: Date of the game
            
        Returns:
            Number of days since last game (0 = back-to-back)
        """
        # Find previous game for this team
        team_games = self.games_df[
            ((self.games_df['home_team'] == team) | (self.games_df['away_team'] == team)) &
            (self.games_df['game_date'] < game_date)
        ].sort_values('game_date')
        
        if team_games.empty:
            return 3  # Default for first game
        
        last_game_date = team_games.iloc[-1]['game_date']
        days_rest = (game_date - last_game_date).days - 1
        
        return max(0, days_rest)
    
    def calculate_games_in_period(self, team: str, game_date: pd.Timestamp, days: int = 7) -> int:
        """
        Calculate number of games in last N days
        
        Args:
            team: Team name
            game_date: Reference date
            days: Number of days to look back
            
        Returns:
            Number of games played in period
        """
        start_date = game_date - timedelta(days=days)
        
        team_games = self.games_df[
            ((self.games_df['home_team'] == team) | (self.games_df['away_team'] == team)) &
            (self.games_df['game_date'] >= start_date) &
            (self.games_df['game_date'] < game_date)
        ]
        
        return len(team_games)
    
    def calculate_travel_distance(self, team: str, game_date: pd.Timestamp, 
                                  is_home: bool) -> float:
        """
        Calculate travel distance to this game
        
        Args:
            team: Team name
            game_date: Date of the game
            is_home: Whether team is home
            
        Returns:
            Travel distance in miles
        """
        if team not in TEAM_LOCATIONS:
            return 0.0
        
        # Find previous game location
        team_games = self.games_df[
            ((self.games_df['home_team'] == team) | (self.games_df['away_team'] == team)) &
            (self.games_df['game_date'] < game_date)
        ].sort_values('game_date')
        
        if team_games.empty:
            return 0.0  # First game, no travel
        
        last_game = team_games.iloc[-1]
        
        # Determine previous location
        if last_game['home_team'] == team:
            prev_location = TEAM_LOCATIONS[team]  # Was at home
        else:
            prev_team = last_game['home_team']
            prev_location = TEAM_LOCATIONS.get(prev_team, TEAM_LOCATIONS[team])
        
        # Determine current location
        if is_home:
            curr_location = TEAM_LOCATIONS[team]
        else:
            # Find opponent
            curr_game = self.games_df[
                (self.games_df['game_date'] == game_date) &
                ((self.games_df['home_team'] == team) | (self.games_df['away_team'] == team))
            ]
            if not curr_game.empty:
                opponent = curr_game.iloc[0]['home_team'] if not is_home else curr_game.iloc[0]['away_team']
                curr_location = TEAM_LOCATIONS.get(opponent, TEAM_LOCATIONS[team])
            else:
                curr_location = TEAM_LOCATIONS[team]
        
        # Calculate distance
        distance = haversine_distance(
            prev_location[0], prev_location[1],
            curr_location[0], curr_location[1]
        )
        
        return distance
    
    def add_schedule_features(self) -> pd.DataFrame:
        """
        Add schedule-related features to games dataframe
        
        Returns:
            Enhanced dataframe with rest/travel features
        """
        df = self.games_df.copy()
        
        logger.info("Calculating schedule features...")
        
        # Initialize columns
        df['home_days_rest'] = 0
        df['away_days_rest'] = 0
        df['home_back_to_back'] = False
        df['away_back_to_back'] = False
        df['home_games_last_7'] = 0
        df['away_games_last_7'] = 0
        df['home_travel_miles'] = 0.0
        df['away_travel_miles'] = 0.0
        
        # Calculate for each game
        for idx, row in df.iterrows():
            game_date = row['game_date']
            home_team = row['home_team']
            away_team = row['away_team']
            
            # Days rest
            home_rest = self.calculate_days_rest(home_team, game_date)
            away_rest = self.calculate_days_rest(away_team, game_date)
            df.at[idx, 'home_days_rest'] = home_rest
            df.at[idx, 'away_days_rest'] = away_rest
            
            # Back-to-back
            df.at[idx, 'home_back_to_back'] = (home_rest == 0)
            df.at[idx, 'away_back_to_back'] = (away_rest == 0)
            
            # Games in last 7 days
            df.at[idx, 'home_games_last_7'] = self.calculate_games_in_period(home_team, game_date, 7)
            df.at[idx, 'away_games_last_7'] = self.calculate_games_in_period(away_team, game_date, 7)
            
            # Travel distance
            df.at[idx, 'home_travel_miles'] = self.calculate_travel_distance(home_team, game_date, is_home=True)
            df.at[idx, 'away_travel_miles'] = self.calculate_travel_distance(away_team, game_date, is_home=False)
        
        logger.info("Schedule features calculated")
        
        return df
    
    def get_team_schedule_summary(self, team: str) -> Dict:
        """
        Get schedule summary for a team
        
        Returns:
            Dict with schedule metrics
        """
        team_games = self.games_df[
            (self.games_df['home_team'] == team) | (self.games_df['away_team'] == team)
        ]
        
        if team_games.empty:
            return {}
        
        # Calculate metrics
        is_home = team_games['home_team'] == team
        
        total_games = len(team_games)
        home_games = is_home.sum()
        away_games = total_games - home_games
        
        return {
            'team': team,
            'total_games': total_games,
            'home_games': home_games,
            'away_games': away_games,
            'avg_days_rest': team_games.apply(
                lambda row: self.calculate_days_rest(team, row['game_date']), axis=1
            ).mean(),
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Load historical games
    games_df = pd.read_csv("data/processed/historical_games.csv")
    
    analyzer = ScheduleAnalyzer(games_df)
    
    # Add schedule features
    enhanced_df = analyzer.add_schedule_features()
    
    # Save
    enhanced_df.to_csv("data/processed/games_with_schedule.csv", index=False)
    
    print("\n" + "="*70)
    print("SCHEDULE ANALYSIS COMPLETE")
    print("="*70)
    print(f"\nGames analyzed: {len(enhanced_df)}")
    print(f"\nAverage days rest:")
    print(f"  Home teams: {enhanced_df['home_days_rest'].mean():.2f}")
    print(f"  Away teams: {enhanced_df['away_days_rest'].mean():.2f}")
    print(f"\nBack-to-back games:")
    print(f"  Home teams: {enhanced_df['home_back_to_back'].sum()}")
    print(f"  Away teams: {enhanced_df['away_back_to_back'].sum()}")
    print(f"\nAverage travel distance:")
    print(f"  Home teams: {enhanced_df['home_travel_miles'].mean():.0f} miles")
    print(f"  Away teams: {enhanced_df['away_travel_miles'].mean():.0f} miles")
