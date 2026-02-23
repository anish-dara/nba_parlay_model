"""Player prop O/U (Over/Under) prediction model."""
from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Optional
import logging

LOGGER = logging.getLogger(__name__)

try:
    import xgboost as xgb
    from sklearn.preprocessing import StandardScaler
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False


class PlayerPropPredictor:
    """XGBoost model for predicting player prop Over/Under outcomes."""
    
    PROP_TYPES = ["points", "assists", "rebounds", "combined"]
    
    def __init__(self, prop_type: str = "points"):
        """
        Args:
            prop_type: Type of prop ("points", "assists", "rebounds", "combined")
        """
        if prop_type not in self.PROP_TYPES:
            raise ValueError(f"Invalid prop_type. Must be one of {self.PROP_TYPES}")
        
        self.prop_type = prop_type
        self.model = None
        self.scaler = None
        
        # Example features for points prop
        self.features = [
            # Player season stats
            f"{prop_type}_per_game",
            f"{prop_type}_per_game_last_10",
            f"{prop_type}_std_dev",
            
            # Usage
            "usage_rate",
            "minutes_per_game",
            
            # Matchup
            "opponent_defense_efficiency",
            "pace_factor",
            
            # Context
            "back_to_back",
            "rest_days",
        ]
    
    def prepare_data(self, player_stats: pd.DataFrame, 
                    prop_lines: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare training data from player stats and prop lines.
        
        Args:
            player_stats: Player box score data
            prop_lines: Historical prop lines with actual outcomes
            
        Returns:
            (X features, y targets)
        """
        # Merge stats with prop lines
        merged = player_stats.merge(prop_lines, on=["player_id", "game_date"], how="inner")
        
        if merged.empty:
            raise ValueError("No matching data between player stats and prop lines")
        
        # Calculate rolling stats
        merged = merged.sort_values(["player_id", "game_date"])
        for player_id in merged["player_id"].unique():
            player_data = merged[merged["player_id"] == player_id]
            if self.prop_type == "points":
                merged.loc[merged["player_id"] == player_id, "points_per_game_last_10"] = (
                    player_data["points"].rolling(window=10, min_periods=1).mean()
                )
            elif self.prop_type == "assists":
                merged.loc[merged["player_id"] == player_id, "assists_per_game_last_10"] = (
                    player_data["assists"].rolling(window=10, min_periods=1).mean()
                )
            # Similar for rebounds, combined, etc.
        
        # Extract features
        X = merged[[f for f in self.features if f in merged.columns]].fillna(0)
        
        # Create target: 1 if actual > line, 0 if actual <= line
        if self.prop_type == "points":
            y = (merged["points"] > merged["prop_line"]).astype(int)
        elif self.prop_type == "assists":
            y = (merged["assists"] > merged["prop_line"]).astype(int)
        elif self.prop_type == "rebounds":
            y = (merged["rebounds"] > merged["prop_line"]).astype(int)
        else:
            # Combined (points + assists + rebounds)
            combined_actual = merged["points"] + merged["assists"] + merged["rebounds"]
            y = (combined_actual > merged["prop_line"]).astype(int)
        
        return X, y
    
    def train(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """
        Train XGBoost model on prop data.
        
        Args:
            X: Features
            y: Targets (1=over, 0=under)
            
        Returns:
            Training metrics
        """
        if not XGB_AVAILABLE:
            raise ImportError("xgboost not installed")
        
        LOGGER.info(f"Training {self.prop_type} prop model on {len(X)} samples...")
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Train
        self.model = xgb.XGBClassifier(
            objective="binary:logistic",
            max_depth=6,
            learning_rate=0.05,
            n_estimators=150,
            random_state=42
        )
        self.model.fit(X_scaled, y)
        
        # Evaluate
        train_acc = self.model.score(X_scaled, y)
        LOGGER.info(f"Training accuracy: {train_acc:.4f}")
        
        return {"accuracy": train_acc, "samples": len(X)}
    
    def predict_ou(self, player_stats: pd.DataFrame, prop_line: float) -> float:
        """
        Predict probability of going Over on a prop line.
        
        Args:
            player_stats: Player feature row
            prop_line: The projected line (e.g., points: 25.5)
            
        Returns:
            Probability of Over (0-1)
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Create feature row
        X = player_stats[[f for f in self.features if f in player_stats.index]].fillna(0).values.reshape(1, -1)
        X_scaled = self.scaler.transform(X)
        
        prob_over = self.model.predict_proba(X_scaled)[0, 1]
        return prob_over
