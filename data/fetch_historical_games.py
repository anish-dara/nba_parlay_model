"""Fetch historical NBA game data from nba_api for training."""
from __future__ import annotations

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

LOGGER = logging.getLogger(__name__)

try:
    from nba_api.stats.endpoints import leaguegamelog
    NBA_API_AVAILABLE = True
except ImportError as e:
    LOGGER.error(f"nba_api not available: {e}")
    NBA_API_AVAILABLE = False


class HistoricalGameFetcher:
    """Fetch completed games from NBA for a given season."""

    def __init__(self, seasons: List[int] = None):
        """
        Args:
            seasons: List of seasons to fetch (e.g., [2025, 2026]). 
                     Season 2025 = 2024-25 season, 2026 = 2025-26 season
        """
        self.seasons = seasons or [2025, 2026]

    def fetch_season_games(self, season: int) -> pd.DataFrame:
        """
        Fetch all games for a given season.
        
        Args:
            season: Season year (e.g., 2024 for 2023-24 season)
            
        Returns:
            DataFrame with columns: game_id, game_date, home_team, away_team, 
                                    home_score, away_score, home_win
        """
        if not NBA_API_AVAILABLE:
            LOGGER.error("nba_api not available")
            return pd.DataFrame()
        
        LOGGER.info(f"Fetching games for season {season}...")
        
        try:
            # Fetch game log for entire league
            df = leaguegamelog.LeagueGameLog(
                season=season,
                season_type_all_star="Regular Season"
            ).get_data_frames()[0]
            
            # Normalize columns
            if "GAME_DATE_EST" in df.columns:
                df["game_date"] = pd.to_datetime(df["GAME_DATE_EST"])
            elif "GAME_DATE" in df.columns:
                df["game_date"] = pd.to_datetime(df["GAME_DATE"])
            
            df = df.sort_values("game_date")
            
            LOGGER.info(f"Fetched {len(df)} game records for season {season}")
            return df
        except Exception as e:
            LOGGER.error(f"Error fetching season {season}: {e}")
            return pd.DataFrame()

    def parse_games(self, season_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Parse raw nba_api data into game records.
        Handles both detailed game logs and summarized data.
        
        Args:
            season_df: DataFrame from LeagueGameLog
            
        Returns:
            List of game dicts with minimal info: 
            {game_id, game_date, home_team, away_team, home_score, away_score, home_win}
        """
        games = []
        
        # nba_api returns one row per team per game; group by game_id
        grouped = season_df.groupby("GAME_ID") if "GAME_ID" in season_df.columns else None
        
        if grouped:
            for game_id, group in grouped:
                if len(group) == 2:
                    # Sort so home team is first (if available; fall back to alphabetical)
                    row1, row2 = group.iloc[0], group.iloc[1]
                    
                    game_date = row1.get("game_date") or row1.get("GAME_DATE_EST")
                    home_team = row1.get("TEAM_NAME") or row1.get("TEAM_ABBREVIATION")
                    away_team = row2.get("TEAM_NAME") or row2.get("TEAM_ABBREVIATION")
                    home_score = int(row1.get("PTS", 0) or 0)
                    away_score = int(row2.get("PTS", 0) or 0)
                    home_win = home_score > away_score
                    
                    games.append({
                        "game_id": str(game_id),
                        "game_date": game_date,
                        "home_team": home_team,
                        "away_team": away_team,
                        "home_score": home_score,
                        "away_score": away_score,
                        "home_win": home_win
                    })
        
        return games

    def fetch_all(self) -> pd.DataFrame:
        """Fetch all games for configured seasons."""
        all_games = []
        
        for season in self.seasons:
            df = self.fetch_season_games(season)
            if not df.empty:
                games = self.parse_games(df)
                all_games.extend(games)
        
        result_df = pd.DataFrame(all_games)
        if not result_df.empty:
            result_df = result_df.sort_values("game_date").reset_index(drop=True)
        
        LOGGER.info(f"Total games fetched: {len(result_df)}")
        return result_df

    def save_csv(self, df: pd.DataFrame, path: str = "data/processed/historical_games.csv"):
        """Save games to CSV."""
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df.to_csv(path, index=False)
        LOGGER.info(f"Saved {len(df)} games to {path}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    fetcher = HistoricalGameFetcher(seasons=[2024, 2025])
    games_df = fetcher.fetch_all()
    print(f"\n{games_df.head(10)}")
    fetcher.save_csv(games_df)
