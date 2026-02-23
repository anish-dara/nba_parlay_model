"""Collect player prop stats and O/U lines from multiple sources."""
from __future__ import annotations

import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import requests
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class PlayerStatsCollector:
    """Fetch player box scores and prop-relevant stats from nba_api."""
    
    def __init__(self):
        pass
    
    def fetch_player_box_scores(self, game_date: pd.Timestamp) -> pd.DataFrame:
        """
        Fetch all player box scores for a given date from nba_api.
        
        Args:
            game_date: Date to fetch games for (YYYY-MM-DD format)
            
        Returns:
            DataFrame with columns: player_id, player_name, team, game_id,
                                   points, assists, rebounds, fg%, 3p%, ft%,
                                   turnovers, steals, blocks, ...
        """
        try:
            from nba_api.stats.endpoints import boxscoretraditionalv2, playergeneralgamelog
            from nba_api.stats.endpoints import leaguegamelog
        except ImportError:
            LOGGER.error("nba_api not available")
            return pd.DataFrame()
        
        date_str = game_date.strftime("%m/%d/%Y")
        LOGGER.info(f"Fetching player stats for {date_str}...")
        
        try:
            # Get all games for this date
            games_df = leaguegamelog.LeagueGameLog(
                season=game_date.year,
                season_type_all_star="Regular Season"
            ).get_data_frames()[0]
            
            # Filter to this date
            games_df["GAME_DATE"] = pd.to_datetime(games_df.get("GAME_DATE", games_df.get("GAME_DATE_EST")))
            today_games = games_df[games_df["GAME_DATE"].dt.date == game_date.date()]
            
            if today_games.empty:
                LOGGER.warning(f"No games found for {date_str}")
                return pd.DataFrame()
            
            # Fetch box scores for each game
            all_players = []
            for game_id in today_games["GAME_ID"].unique():
                try:
                    box = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=str(game_id))
                    players = box.get_data_frames()[0]  # Player stats
                    
                    players["GAME_ID"] = game_id
                    all_players.append(players)
                except Exception as e:
                    LOGGER.warning(f"Error fetching box score {game_id}: {e}")
            
            if not all_players:
                return pd.DataFrame()
            
            df = pd.concat(all_players, ignore_index=True)
            LOGGER.info(f"Fetched stats for {len(df.groupby('PLAYER_ID')))} unique players")
            
            # Rename and clean
            df.columns = df.columns.str.lower()
            return df
            
        except Exception as e:
            LOGGER.error(f"Error fetching player stats: {e}")
            return pd.DataFrame()
    
    def extract_props(self, player_stats: pd.DataFrame) -> pd.DataFrame:
        """
        Extract prop-relevant columns from box scores.
        
        Args:
            player_stats: Raw box score data
            
        Returns:
            DataFrame with prop stats: player_id, player_name, team, 
                                       points, assists, rebounds, ...
        """
        if player_stats.empty:
            return pd.DataFrame()
        
        prop_cols = {
            "player_id": "player_id",
            "player_name": "player_name",
            "team_abbreviation": "team",
            "pts": "points",
            "ast": "assists",
            "reb": "rebounds",
            "fg_pct": "fg_pct",
            "fg3_pct": "three_pct",
            "ft_pct": "ft_pct",
            "tov": "turnovers",
            "stl": "steals",
            "blk": "blocks",
            "min": "minutes",
        }
        
        available_cols = [k for k in prop_cols.keys() if k in player_stats.columns]
        df = player_stats[available_cols + ["game_id", "game_date"]].copy()
        df.rename(columns={k: v for k, v in prop_cols.items() if k in available_cols}, inplace=True)
        
        return df
    
    def save_player_stats(self, df: pd.DataFrame, path: str = "data/processed/player_stats.csv"):
        """Save player stats to CSV."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
        LOGGER.info(f"Saved {len(df)} player stat records to {path}")


class PropOddsCollector:
    """Fetch prop odds from multiple sources."""
    
    # Known sportsbooks with player prop markets
    BOOKS = {
        "draftkings": "https://sportsbook-nash.draftkings.com/api/sportbooks/draftkings",
        "fanduel": "https://www.fanduel.com/api/odds",
        "betmgm": "https://betmgm.com/api/odds",
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})
    
    def fetch_from_the_odds_api(self, api_key: str, sport: str = "basketball_nba") -> List[Dict[str, Any]]:
        """
        Check if TheOddsAPI supports player props.
        
        Args:
            api_key: The Odds API key
            sport: Sport key
            
        Returns:
            List of prop events or empty if not available
        """
        # As of 2026, TheOddsAPI doesn't expose player props via free tier
        # This is a placeholder for if they add support
        LOGGER.info("Checking TheOddsAPI for player props...")
        
        url = f"https://api.the-odds-api.com/v4/sports/{sport}/events"
        params = {"apiKey": api_key}
        
        try:
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                LOGGER.info(f"TheOddsAPI response: {len(data)} events")
                return data
        except Exception as e:
            LOGGER.warning(f"TheOddsAPI not available: {e}")
        
        return []
    
    def fetch_player_props_web_scrape(self, game_date: pd.Timestamp) -> pd.DataFrame:
        """
        Scrape player prop odds from public bookmaker sites.
        
        This uses simple web scraping as a fallback when no API is available.
        
        Args:
            game_date: Date to fetch props for
            
        Returns:
            DataFrame with columns: player_name, prop_type, line, odds_american, book
        """
        LOGGER.warning("Web scraping player props not yet implemented (manual implementation required)")
        LOGGER.info("Recommended sources for scraping:")
        LOGGER.info("  - DraftKings: sportsbook.draftkings.com")
        LOGGER.info("  - FanDuel: fanduel.com/betting")
        LOGGER.info("  - ESPN: espn.com/nba/scoreboard")
        
        # Placeholder — scraping these sites requires handling JS, CAPTCHAs, etc.
        # For production, use a headless browser (Selenium/Playwright) or
        # subscribe to a prop odds API
        
        return pd.DataFrame({
            "player_name": [],
            "prop_type": ["points", "assists", "rebounds"],  # Example
            "line": [],
            "odds_american": [],
            "book": []
        })
    
    def get_available_sources(self) -> Dict[str, str]:
        """Return available prop odds sources and their status."""
        return {
            "the_odds_api": "Limited (free tier no player props)",
            "draftkings": "Requires scraping",
            "fanduel": "Requires scraping",
            "betmgm": "Requires scraping",
            "espn": "Public but limited odds",
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    collector = PlayerStatsCollector()
    print("Player Stats Collector ready.")
    print("Prop Odds sources:", PropOddsCollector().get_available_sources())
