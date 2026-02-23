"""Feature engineering for NBA games: team stats, form, etc."""
from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

LOGGER = logging.getLogger(__name__)


class FeatureEngineer:
    """Compute features from historical games for modeling."""

    @staticmethod
    def compute_team_season_stats(games_df: pd.DataFrame, reference_date: pd.Timestamp = None) -> Dict[str, Dict[str, float]]:
        """
        Compute season-to-date stats per team up to reference_date.
        
        Args:
            games_df: DataFrame with columns game_date, home_team, away_team, 
                      home_score, away_score, home_win
            reference_date: Only include games before this date (prevents data leakage)
            
        Returns:
            Dict {team_name: {win_pct, avg_pts_for, avg_pts_against, ...}}
        """
        # Filter games before reference date to prevent data leakage
        if reference_date is not None:
            games_df = games_df[games_df["game_date"] < reference_date].copy()
        
        team_stats = {}
        
        for team in pd.concat([games_df["home_team"], games_df["away_team"]]).unique():
            # Games where team played
            home_games = games_df[games_df["home_team"] == team].copy()
            away_games = games_df[games_df["away_team"] == team].copy()
            
            home_wins = home_games["home_win"].sum()
            away_wins = (away_games["home_win"] == False).sum()
            total_wins = home_wins + away_wins
            
            home_gp = len(home_games)
            away_gp = len(away_games)
            total_gp = home_gp + away_gp
            
            if total_gp == 0:
                continue
            
            # Points for / against
            pts_for = (home_games["home_score"].sum() + away_games["away_score"].sum()) / total_gp
            pts_against = (home_games["away_score"].sum() + away_games["home_score"].sum()) / total_gp
            
            team_stats[team] = {
                "wins": total_wins,
                "games_played": total_gp,
                "win_pct": total_wins / total_gp if total_gp > 0 else 0,
                "home_win_pct": home_wins / home_gp if home_gp > 0 else 0,
                "away_win_pct": away_wins / away_gp if away_gp > 0 else 0,
                "avg_pts_for": pts_for,
                "avg_pts_against": pts_against,
                "point_differential": pts_for - pts_against
            }
        
        return team_stats

    @staticmethod
    def compute_recent_form(games_df: pd.DataFrame, team: str, reference_date: pd.Timestamp, 
                           days_back: int = 14) -> Dict[str, float]:
        """
        Compute 2-week form: recent win%, recent scoring, etc.
        
        Args:
            games_df: Historical games
            team: Team name
            reference_date: Date to compute form as of
            days_back: Number of days to look back (default 14)
            
        Returns:
            {recent_win_pct, recent_scored, recent_allowed, ...}
        """
        cutoff = reference_date - pd.Timedelta(days=days_back)
        
        home_games = games_df[(games_df["home_team"] == team) & 
                              (games_df["game_date"] >= cutoff) & 
                              (games_df["game_date"] <= reference_date)].copy()
        away_games = games_df[(games_df["away_team"] == team) & 
                              (games_df["game_date"] >= cutoff) & 
                              (games_df["game_date"] <= reference_date)].copy()
        
        recent_wins = home_games["home_win"].sum() + (away_games["home_win"] == False).sum()
        recent_gp = len(home_games) + len(away_games)
        
        if recent_gp == 0:
            return {
                "recent_win_pct": 0.5,  # Neutral default
                "recent_scored": 100,
                "recent_allowed": 100
            }
        
        recent_scored = (home_games["home_score"].sum() + away_games["away_score"].sum()) / recent_gp
        recent_allowed = (home_games["away_score"].sum() + away_games["home_score"].sum()) / recent_gp
        
        return {
            "recent_win_pct": recent_wins / recent_gp,
            "recent_scored": recent_scored,
            "recent_allowed": recent_allowed
        }

    @staticmethod
    def add_game_features(games_df: pd.DataFrame) -> pd.DataFrame:
        """
        Add computed features to games dataframe.
        
        Args:
            games_df: Original games dataframe
            
        Returns:
            Enhanced dataframe with feature columns
        """
        df = games_df.copy()
        df = df.sort_values("game_date").reset_index(drop=True)
        
        # Home court advantage indicator (always 1 for home team)
        df["is_home"] = 1
        
        # Initialize feature columns
        df["home_season_win_pct"] = 0.5
        df["away_season_win_pct"] = 0.5
        df["home_pts_differential"] = 0.0
        df["away_pts_differential"] = 0.0
        df["home_recent_win_pct"] = 0.5
        df["away_recent_win_pct"] = 0.5
        
        # Compute features for each game using only prior games (no data leakage)
        for idx, row in df.iterrows():
            game_date = row["game_date"]
            home_team = row["home_team"]
            away_team = row["away_team"]
            
            # Get stats from games BEFORE this one
            team_stats = FeatureEngineer.compute_team_season_stats(df, reference_date=game_date)
            
            # Season stats
            df.at[idx, "home_season_win_pct"] = team_stats.get(home_team, {}).get("win_pct", 0.5)
            df.at[idx, "away_season_win_pct"] = team_stats.get(away_team, {}).get("win_pct", 0.5)
            df.at[idx, "home_pts_differential"] = team_stats.get(home_team, {}).get("point_differential", 0)
            df.at[idx, "away_pts_differential"] = team_stats.get(away_team, {}).get("point_differential", 0)
            
            # Recent form
            home_recent = FeatureEngineer.compute_recent_form(df, home_team, game_date)
            away_recent = FeatureEngineer.compute_recent_form(df, away_team, game_date)
            df.at[idx, "home_recent_win_pct"] = home_recent["recent_win_pct"]
            df.at[idx, "away_recent_win_pct"] = away_recent["recent_win_pct"]
        
        # Spread indicator (if you have odds available)
        if "odds_decimal" in df.columns:
            df["implied_home_prob"] = 1 / df["odds_decimal"]
        
        return df
