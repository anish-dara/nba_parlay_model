"""Join historical games with collected odds to build training dataset."""
from __future__ import annotations

import pandas as pd
import os
import logging
from datetime import datetime, timedelta
from typing import Optional

LOGGER = logging.getLogger(__name__)


class DatasetBuilder:
    """Build training datasets by joining games with odds."""

    @staticmethod
    def load_historical_games(path: str = "data/processed/historical_games.csv") -> pd.DataFrame:
        """Load historical games CSV."""
        if not os.path.exists(path):
            LOGGER.warning(f"File not found: {path}")
            return pd.DataFrame()
        
        df = pd.read_csv(path)
        df["game_date"] = pd.to_datetime(df["game_date"])
        return df

    @staticmethod
    def load_odds_history(path: str = "data/processed/odds.csv") -> pd.DataFrame:
        """Load collected odds CSV."""
        if not os.path.exists(path):
            LOGGER.warning(f"File not found: {path}")
            return pd.DataFrame()
        
        df = pd.read_csv(path)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["start_time"] = pd.to_datetime(df["start_time"])
        return df

    @staticmethod
    def load_odds_sqlite(db_path: str = "data/processed/odds_history.sqlite") -> pd.DataFrame:
        """Load odds from SQLite database."""
        if not os.path.exists(db_path):
            LOGGER.warning(f"Database not found: {db_path}")
            return pd.DataFrame()
        
        import sqlite3
        conn = sqlite3.connect(db_path)
        try:
            df = pd.read_sql_query("SELECT * FROM odds_history", conn)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df["start_time"] = pd.to_datetime(df["start_time"])
        finally:
            conn.close()
        
        return df

    @staticmethod
    def aggregate_odds_for_game(odds_df: pd.DataFrame, game_date: pd.Timestamp, 
                               home_team: str, away_team: str) -> dict:
        """
        Find opening and closing odds for a game.
        
        Args:
            odds_df: Collected odds dataframe
            game_date: Game date to match (approx)
            home_team: Home team name
            away_team: Away team name
            
        Returns:
            {opening_odds_home, closing_odds_home, avg_odds_home, ...}
        """
        # Return defaults if no odds data
        if odds_df.empty:
            return {
                "opening_odds_home": None,
                "closing_odds_home": None,
                "avg_odds_home": None,
                "num_bookmakers": 0
            }
        
        # Try to find odds for this matchup within 48 hours before game
        start_search = game_date - timedelta(days=2)
        end_search = game_date
        
        relevant = odds_df[
            (odds_df["start_time"] >= start_search) & 
            (odds_df["start_time"] <= end_search)
        ].copy()
        
        if relevant.empty:
            return {
                "opening_odds_home": None,
                "closing_odds_home": None,
                "avg_odds_home": None,
                "num_bookmakers": 0
            }
        
        # Get opening (earliest) and closing (latest) odds
        relevant = relevant.sort_values("timestamp")
        
        opening = relevant.iloc[0]["odds_decimal"] if not relevant.empty else None
        closing = relevant.iloc[-1]["odds_decimal"] if not relevant.empty else None
        avg_odds = relevant["odds_decimal"].mean() if not relevant.empty else None
        num_books = relevant["provider"].nunique()
        
        return {
            "opening_odds_home": opening,
            "closing_odds_home": closing,
            "avg_odds_home": avg_odds,
            "num_bookmakers": num_books
        }

    @staticmethod
    def build_training_dataset(
        games_df: Optional[pd.DataFrame] = None,
        odds_df: Optional[pd.DataFrame] = None,
        include_features: bool = True
    ) -> pd.DataFrame:
        """
        Build a training dataset by joining games and odds.
        
        Args:
            games_df: Historical games (auto-loads if None)
            odds_df: Collected odds (auto-loads if None; tries CSV first, then SQLite)
            include_features: Whether to compute engineered features
            
        Returns:
            Training dataframe with columns: game_id, game_date, home_team, away_team,
                                           home_score, away_score, home_win,
                                           opening_odds_home, closing_odds_home, ...
        """
        if games_df is None:
            games_df = DatasetBuilder.load_historical_games()
        if odds_df is None:
            odds_df = DatasetBuilder.load_odds_history()
            if odds_df.empty:
                odds_df = DatasetBuilder.load_odds_sqlite()
        
        if games_df.empty:
            LOGGER.error("No games data available")
            return pd.DataFrame()
        
        LOGGER.info(f"Building dataset from {len(games_df)} games and {len(odds_df)} odds records")
        
        # Join odds to each game
        training = games_df.copy()
        
        def add_odds(row):
            odds_info = DatasetBuilder.aggregate_odds_for_game(
                odds_df, row["game_date"], row["home_team"], row["away_team"]
            )
            return pd.Series(odds_info)
        
        odds_cols = training.apply(add_odds, axis=1)
        training = pd.concat([training, odds_cols], axis=1)
        
        # Add features
        if include_features:
            from analysis.feature_engineering import FeatureEngineer
            training = FeatureEngineer.add_game_features(training)
        
        LOGGER.info(f"Built training dataset with {len(training)} rows and {len(training.columns)} columns")
        return training

    @staticmethod
    def save_dataset(df: pd.DataFrame, path: str = "data/processed/training_dataset.csv"):
        """Save training dataset to CSV."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df.to_csv(path, index=False)
        LOGGER.info(f"Saved training dataset to {path}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Build and save dataset
    dataset = DatasetBuilder.build_training_dataset(include_features=True)
    if not dataset.empty:
        print(f"\nDataset shape: {dataset.shape}")
        print(f"Columns: {list(dataset.columns)}")
        print(f"\n{dataset.head()}")
        DatasetBuilder.save_dataset(dataset)
    else:
        print("No data available to build dataset. Collect some game/odds data first.")
