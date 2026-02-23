"""Complete training and prediction pipeline for game outcomes."""
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from datetime import datetime
from models.game_predictor import GamePredictor
from analysis.feature_engineering import FeatureEngineer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class GamePredictionPipeline:
    """End-to-end pipeline for training and making game predictions."""

    def __init__(self, model_path: str = "models/saved_models/game_predictor.pkl"):
        """
        Args:
            model_path: Path to save/load trained model
        """
        self.model_path = Path(model_path)
        self.predictor = None
        self.games_df = None
        self.team_stats = None

    def train(self, data_path: str = "data/processed/historical_games.csv"):
        """
        Train game predictor on historical data.
        
        Args:
            data_path: Path to historical games CSV
            
        Returns:
            Dict with training metrics
        """
        logger.info("=" * 60)
        logger.info("PHASE 1: TRAINING GAME PREDICTION MODEL")
        logger.info("=" * 60)
        
        # Load historical games
        logger.info(f"Loading historical games from {data_path}...")
        games_df = pd.read_csv(data_path)
        logger.info(f"Loaded {len(games_df)} games")
        
        # Convert game_date to datetime
        games_df["game_date"] = pd.to_datetime(games_df["game_date"])
        games_df = games_df.sort_values("game_date").reset_index(drop=True)
        
        # Compute team season stats (cumulative as of each game)
        logger.info("Computing team season stats...")
        self.games_df = games_df.copy()
        
        # Feature engineering
        logger.info("Engineering features...")
        df_featured = FeatureEngineer.add_game_features(games_df)
        
        # Print feature summary
        required_features = [
            "home_season_win_pct", "away_season_win_pct",
            "home_pts_differential", "away_pts_differential",
            "home_recent_win_pct", "away_recent_win_pct", "home_win"
        ]
        
        logger.info(f"Dataset shape: {df_featured.shape}")
        logger.info(f"Features created: {[c for c in df_featured.columns if c not in games_df.columns]}")
        
        # Check for missing values
        missing = df_featured[required_features].isnull().sum()
        if missing.any():
            logger.warning(f"Missing values before dropna: {missing[missing > 0].to_dict()}")
            df_featured = df_featured.dropna(subset=required_features)
            logger.info(f"After dropna: {len(df_featured)} games remain")
        
        if len(df_featured) < 50:
            logger.error("Insufficient training data")
            return None
        
        # Train model
        logger.info(f"Training XGBoost classifier on {len(df_featured)} games...")
        self.predictor = GamePredictor()
        results = self.predictor.train(df_featured, test_size=0.2)
        
        # Results
        logger.info("\n" + "=" * 60)
        logger.info("TRAINING RESULTS")
        logger.info("=" * 60)
        logger.info(f"Train AUC:        {results['train_auc']:.4f}")
        logger.info(f"Test AUC:         {results['test_auc']:.4f}")
        logger.info(f"CV Mean:          {results['cv_mean']:.4f} (±{results['cv_std']:.4f})")
        logger.info(f"Best Threshold:   {results.get('best_threshold', 0.5):.4f}")
        
        # Feature importance
        importance_dict = self.predictor.get_feature_importance()
        if isinstance(importance_dict, dict):
            importance_df = pd.DataFrame([
                {"feature": k, "importance": v} for k, v in importance_dict.items()
            ]).sort_values("importance", ascending=False).reset_index(drop=True)
        else:
            importance_df = importance_dict.sort_values("importance", ascending=False).reset_index(drop=True)
        
        logger.info("\nTop 10 Feature Importances:")
        logger.info("-" * 40)
        for idx, row in importance_df.head(10).iterrows():
            logger.info(f"  {idx+1:2d}. {row['feature']:30s} {row['importance']:7.4f}")
        
        # Save model
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        self.predictor.save(str(self.model_path))
        logger.info(f"\nModel saved to: {self.model_path}")
        
        # Save feature importance
        importance_df.to_csv(self.model_path.parent / "feature_importance.csv", index=False)
        logger.info(f"Feature importance saved to: {self.model_path.parent / 'feature_importance.csv'}")
        
        logger.info("=" * 60)
        logger.info("TRAINING COMPLETE ✓")
        logger.info("=" * 60)
        
        return results

    def load_model(self):
        """Load trained model from disk."""
        if not self.model_path.exists():
            logger.error(f"Model not found at {self.model_path}")
            return False
        
        logger.info(f"Loading model from {self.model_path}...")
        self.predictor = GamePredictor()
        self.predictor.load(str(self.model_path))
        logger.info("Model loaded ✓")
        
        # Reload historical games for stats reference
        games_path = Path("data/processed/historical_games.csv")
        if games_path.exists():
            self.games_df = pd.read_csv(games_path)
            self.games_df["game_date"] = pd.to_datetime(self.games_df["game_date"])
        
        return True

    def predict_game(self, home_team: str, away_team: str, game_date: str = None) -> dict:
        """
        Predict outcome for a single game.
        
        Args:
            home_team: Home team name (e.g., "Lakers", "Celtics")
            away_team: Away team name
            game_date: Game date as "YYYY-MM-DD" (defaults to today)
            
        Returns:
            {home_win_prob, away_win_prob, confidence, features_used}
        """
        if self.predictor is None:
            raise ValueError("Model not loaded. Call load_model() or train() first.")
        
        # Validate team names
        if self.games_df is not None:
            all_teams = set(pd.concat([self.games_df["home_team"], self.games_df["away_team"]]).unique())
            if home_team not in all_teams:
                raise ValueError(f"Unknown home team: {home_team}. Available teams: {sorted(all_teams)}")
            if away_team not in all_teams:
                raise ValueError(f"Unknown away team: {away_team}. Available teams: {sorted(all_teams)}")
        
        if game_date is None:
            game_date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            game_date = pd.to_datetime(game_date)
        except Exception as e:
            raise ValueError(f"Invalid date format: {game_date}. Use YYYY-MM-DD format.") from e
        
        # Create game record
        game = pd.DataFrame({
            "home_team": [home_team],
            "away_team": [away_team],
            "game_date": [game_date],
            "home_score": [0],  # Placeholder
            "away_score": [0],  # Placeholder
            "home_win": [0],  # Placeholder
            "is_home": [1]  # Home court advantage
        })
        
        # Get historical data as of this game (using all historical for team stats)
        if self.games_df is not None:
            historical = self.games_df[self.games_df["game_date"] < game_date].copy()
        else:
            historical = game.copy()
        
        # Feature engineering on this game
        combined = pd.concat([historical, game], ignore_index=True)
        combined = combined.sort_values("game_date").reset_index(drop=True)
        featured = FeatureEngineer.add_game_features(combined)
        
        # Get the last row (our game)
        game_features = featured.iloc[-1:].copy()
        
        # Predict
        prob = self.predictor.predict(game_features, return_prob=True)[0]  # P(home_win)
        
        return {
            "home_team": home_team,
            "away_team": away_team,
            "game_date": str(game_date.date()),
            "home_win_probability": float(prob),
            "away_win_probability": float(1 - prob),
            "predicted_winner": home_team if prob > 0.5 else away_team,
            "confidence": float(abs(prob - 0.5) * 2),  # 0 = 50%, 1 = very confident
            "features": {
                "home_season_wp": float(game_features["home_season_win_pct"].iloc[0]),
                "away_season_wp": float(game_features["away_season_win_pct"].iloc[0]),
                "home_recent_wp": float(game_features["home_recent_win_pct"].iloc[0]),
                "away_recent_wp": float(game_features["away_recent_win_pct"].iloc[0]),
                "home_pt_diff": float(game_features["home_pts_differential"].iloc[0]),
                "away_pt_diff": float(game_features["away_pts_differential"].iloc[0]),
            }
        }

    def predict_batch(self, games: list) -> list:
        """
        Predict multiple games at once.
        
        Args:
            games: List of dicts with {home_team, away_team, game_date}
            
        Returns:
            List of prediction dicts
        """
        results = []
        for game in games:
            pred = self.predict_game(
                game["home_team"],
                game["away_team"],
                game.get("game_date")
            )
            if pred:
                results.append(pred)
        return results


def main():
    """Train model and show example predictions."""
    pipeline = GamePredictionPipeline()
    
    # Train
    results = pipeline.train()
    
    if results is None:
        logger.error("Training failed")
        return
    
    # Example predictions
    logger.info("\n" + "=" * 60)
    logger.info("EXAMPLE PREDICTIONS")
    logger.info("=" * 60)
    
    example_games = [
        ("Lakers", "Celtics", "2025-02-15"),
        ("Warriors", "Nuggets", "2025-02-16"),
        ("Heat", "Knicks", "2025-02-17"),
    ]
    
    for home, away, date in example_games:
        pred = pipeline.predict_game(home, away, date)
        if pred:
            logger.info(f"\n{home} vs {away} ({date})")
            logger.info(f"  {home} Win Prob:  {pred['home_win_probability']:.2%}")
            logger.info(f"  {away} Win Prob:  {pred['away_win_probability']:.2%}")
            logger.info(f"  Prediction:     {pred['predicted_winner']} (confidence: {pred['confidence']:.1%})")
            logger.info(f"  {home} Season W%:  {pred['features']['home_season_wp']:.1%}")
            logger.info(f"  {away} Season W%:  {pred['features']['away_season_wp']:.1%}")


if __name__ == "__main__":
    main()
