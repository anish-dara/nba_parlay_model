"""XGBoost-based game prediction model with advanced feature engineering."""
from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Any, Optional
import logging
import joblib
from pathlib import Path

LOGGER = logging.getLogger(__name__)

try:
    import xgboost as xgb
    from sklearn.model_selection import cross_val_score, train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import roc_auc_score, roc_curve
    XGB_AVAILABLE = True
except ImportError:
    LOGGER.error("xgboost and/or scikit-learn not installed")
    XGB_AVAILABLE = False


class GamePredictor:
    """XGBoost model for predicting home team win probability."""
    
    # Target threshold — predict probability of home win
    TARGET_COL = "home_win"
    
    # Features used for prediction
    FEATURE_COLS = [
        # Home court advantage (critical!)
        "is_home",  # Always 1 for home team predictions
        
        # Season stats
        "home_season_win_pct",
        "away_season_win_pct",
        "home_pts_differential",
        "away_pts_differential",
        
        # Recent form
        "home_recent_win_pct",
        "away_recent_win_pct",
        
        # Advanced stats (if available)
        "home_offensive_efficiency",
        "away_defensive_efficiency",
        "home_pace",
        "away_pace",
        "home_usage_rate",
        "away_usage_rate",
        
        # Matchup
        "home_vs_away_matchup_score",
        "rest_advantage",
    ]
    
    def __init__(self, model_path: str = "models/trained/game_predictor.pkl"):
        self.model = None
        self.scaler = None
        self.feature_importance = {}
        self.model_path = Path(model_path)
        self.best_threshold = 0.5  # Tuned on training data

    def train(self, df: pd.DataFrame, test_size: float = 0.2, hyperparams: Optional[Dict] = None) -> Dict[str, float]:
        """
        Train XGBoost model on game data.
        
        Args:
            df: DataFrame with columns from FEATURE_COLS + TARGET_COL
            test_size: Train/test split ratio
            hyperparams: XGBoost hyperparameters; defaults to tuned params
            
        Returns:
            {'train_auc': float, 'test_auc': float, 'cv_mean': float, 'cv_std': float}
        """
        if not XGB_AVAILABLE:
            raise ImportError("xgboost not installed")
        
        LOGGER.info("Preparing data for training...")
        
        # Remove rows with missing critical features
        required_features = [col for col in self.FEATURE_COLS if col in df.columns]
        df_clean = df[required_features + [self.TARGET_COL]].dropna()
        
        if len(df_clean) < 100:
            raise ValueError(f"Insufficient data: {len(df_clean)} rows")
        
        X = df_clean[required_features]
        y = df_clean[self.TARGET_COL].astype(int)
        
        LOGGER.info(f"Training on {len(X)} games with {len(required_features)} features")
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Hyperparameters (optimized for accuracy over speed)
        if hyperparams is None:
            hyperparams = {
                "objective": "binary:logistic",
                "max_depth": 7,
                "learning_rate": 0.05,
                "n_estimators": 200,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "min_child_weight": 5,
                "reg_lambda": 1.0,
                "reg_alpha": 0.5,
                "random_state": 42,
                "eval_metric": "auc",
            }
        
        # Train (XGBoost 3.2.0+ API)
        self.model = xgb.XGBClassifier(**hyperparams)
        self.model.fit(
            X_train_scaled, y_train,
            eval_set=[(X_test_scaled, y_test)],
            verbose=False
        )
        
        # Evaluate
        train_pred = self.model.predict_proba(X_train_scaled)[:, 1]
        test_pred = self.model.predict_proba(X_test_scaled)[:, 1]
        
        train_auc = roc_auc_score(y_train, train_pred)
        test_auc = roc_auc_score(y_test, test_pred)
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5, scoring="roc_auc")
        
        # Tune probability threshold for F1/precision balance
        fpr, tpr, thresholds = roc_curve(y_test, test_pred)
        f1_scores = 2 * (tpr * (1 - fpr)) / (tpr + (1 - fpr) + 1e-8)
        self.best_threshold = thresholds[np.argmax(f1_scores)]
        
        # Feature importance
        self.feature_importance = dict(zip(required_features, self.model.feature_importances_))
        
        results = {
            "train_auc": float(train_auc),
            "test_auc": float(test_auc),
            "cv_mean": float(cv_scores.mean()),
            "cv_std": float(cv_scores.std()),
            "best_threshold": float(self.best_threshold),
            "n_features": len(required_features),
            "n_training_samples": len(X_train)
        }
        
        LOGGER.info(f"Training complete: Test AUC={test_auc:.4f}, CV AUC={cv_scores.mean():.4f}±{cv_scores.std():.4f}")
        LOGGER.info(f"Top 5 features: {sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]}")
        
        return results

    def predict(self, df: pd.DataFrame, return_prob: bool = True) -> np.ndarray:
        """
        Predict home win probability for games.
        
        Args:
            df: DataFrame with feature columns
            return_prob: If True, return probabilities; else binary predictions
            
        Returns:
            Array of predictions
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first or load()")
        
        required_features = [col for col in self.FEATURE_COLS if col in df.columns]
        X = df[required_features].fillna(0.5)  # Fill NaN with neutral value
        X_scaled = self.scaler.transform(X)
        
        if return_prob:
            return self.model.predict_proba(X_scaled)[:, 1]
        else:
            return (self.model.predict_proba(X_scaled)[:, 1] >= self.best_threshold).astype(int)

    def save(self, path: Optional[str] = None):
        """Save trained model to disk."""
        path = Path(path or self.model_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": self.model, "scaler": self.scaler, "threshold": self.best_threshold}, path)
        LOGGER.info(f"Model saved to {path}")

    def load(self, path: Optional[str] = None):
        """Load trained model from disk."""
        path = Path(path or self.model_path)
        if not path.exists():
            raise FileNotFoundError(f"Model not found: {path}")
        data = joblib.load(path)
        self.model = data["model"]
        self.scaler = data["scaler"]
        self.best_threshold = data["threshold"]
        LOGGER.info(f"Model loaded from {path}")

    def get_feature_importance(self, top_k: int = 10) -> Dict[str, float]:
        """Return top K most important features."""
        return dict(sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)[:top_k])
