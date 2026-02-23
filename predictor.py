"""
Simple prediction interface for NBA games.

Usage:
    from predictor import predict_game
    
    # Predict a game
    result = predict_game("Lakers", "Celtics", "2025-02-15")
    print(f"{result['home_team']} win probability: {result['home_win_probability']:.1%}")
"""

import pandas as pd
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model and data cache
_TIER_MODEL = None
_DATA_LOADER = None
_USE_TIER_MODEL = True  # Set to False to use simple fallback


def init_model(model_path: str = "models/saved_models/game_predictor.pkl",
               data_path: str = "data/processed/historical_games.csv"):
    """Initialize model and load historical data."""
    global _TIER_MODEL, _DATA_LOADER
    
    if _TIER_MODEL is not None:
        return  # Already initialized
    
    logger.info("Initializing tier-based prediction model...")
    
    try:
        from models.tier_based_predictor import TierBasedPredictor
        from models.team_data_loader import TeamDataLoader
        
        _TIER_MODEL = TierBasedPredictor()
        _DATA_LOADER = TeamDataLoader()
        _DATA_LOADER.load_all_data()
        
        logger.info("✓ Tier-based model initialized")
    except Exception as e:
        logger.error(f"Failed to load tier-based model: {e}")
        logger.info("Falling back to simple heuristic model")
        global _USE_TIER_MODEL
        _USE_TIER_MODEL = False


def get_team_stats(team: str) -> dict:
    """
    Get current season stats for a team.
    
    Args:
        team: Team name
        
    Returns:
        Dict with season stats or neutral defaults if team not found
    """
    if _DATA_LOADER is None:
        init_model()
    
    try:
        factors = _DATA_LOADER.get_team_factors(team)
        return {
            "win_pct": factors.last_10_record[0] / 10 if sum(factors.last_10_record) > 0 else 0.500,
            "off_rating": factors.offensive_rating,
            "def_rating": factors.defensive_rating,
            "net_rating": factors.net_rating,
            "tier": factors.overall_tier.name
        }
    except Exception:
        return {
            "win_pct": 0.500,
            "off_rating": 110.0,
            "def_rating": 110.0,
            "net_rating": 0.0,
            "tier": "C"
        }


def predict_game(home_team: str, away_team: str, game_date: str = None) -> dict:
    """
    Predict outcome for a single NBA game using tier-based model.
    
    Args:
        home_team: Home team name (e.g., "Lakers", "Celtics")
        away_team: Away team name
        game_date: Game date as "YYYY-MM-DD" (defaults to today)
        
    Returns:
        Dictionary with predictions and detailed breakdown
    """
    if _TIER_MODEL is None:
        init_model()
    
    # Parse date
    if game_date is None:
        game_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        game_date_dt = pd.to_datetime(game_date)
    except Exception:
        raise ValueError(f"Invalid date format: {game_date}. Use YYYY-MM-DD")
    
    # Use tier-based model if available
    if _USE_TIER_MODEL and _DATA_LOADER is not None:
        try:
            # Get team factors
            home_factors = _DATA_LOADER.get_team_factors(home_team, is_home=True, opponent=away_team)
            away_factors = _DATA_LOADER.get_team_factors(away_team, is_home=False, opponent=home_team)
            
            # Make prediction
            prediction = _TIER_MODEL.predict_game(home_factors, away_factors)
            
            return {
                "home_team": home_team,
                "away_team": away_team,
                "game_date": game_date,
                "home_win_probability": prediction['home_win_probability'],
                "away_win_probability": prediction['away_win_probability'],
                "predicted_winner": home_team if prediction['home_win_probability'] > 0.5 else away_team,
                "confidence": prediction['confidence'],
                "model_type": "tier_based",
                "breakdown": prediction.get('breakdown', {}),
                "model_features": {
                    "home_tier": home_factors.overall_tier.name,
                    "away_tier": away_factors.overall_tier.name,
                    "home_net_rating": home_factors.net_rating,
                    "away_net_rating": away_factors.net_rating,
                    "home_injuries": home_factors.key_players_out,
                    "away_injuries": away_factors.key_players_out,
                }
            }
        except Exception as e:
            logger.warning(f"Tier model failed: {e}. Using fallback.")
    
    # Fallback to simple heuristic
    home_stats = get_team_stats(home_team)
    away_stats = get_team_stats(away_team)
    
    home_wp = home_stats.get('win_pct', 0.5)
    away_wp = away_stats.get('win_pct', 0.5)
    home_prob = 0.5 + (home_wp - away_wp) * 0.5 + 0.035
    home_prob = max(0.01, min(0.99, home_prob))
    
    return {
        "home_team": home_team,
        "away_team": away_team,
        "game_date": game_date,
        "home_win_probability": float(home_prob),
        "away_win_probability": float(1 - home_prob),
        "predicted_winner": home_team if home_prob > 0.5 else away_team,
        "confidence": float(abs(home_prob - 0.5) * 2),
        "model_type": "simple_heuristic",
        "model_features": {
            "home_win_pct": home_wp,
            "away_win_pct": away_wp,
        }
    }


def format_prediction(prediction: dict) -> str:
    """Format prediction as readable string."""
    output = f"""
{prediction['home_team']} vs {prediction['away_team']} ({prediction['game_date']})
  {prediction['home_team']:15s} {prediction['home_win_probability']:6.1%} win
  {prediction['away_team']:15s} {prediction['away_win_probability']:6.1%} win
  
  Prediction: {prediction['predicted_winner']} (confidence: {prediction['confidence']:5.1%})
  Model: {prediction.get('model_type', 'unknown')}
"""
    
    # Add tier info if available
    if 'model_features' in prediction:
        features = prediction['model_features']
        if 'home_tier' in features:
            output += f"\n  Tiers: {features['home_tier']} vs {features['away_tier']}"
        if 'home_net_rating' in features:
            output += f"\n  Net Ratings: {features['home_net_rating']:+.1f} vs {features['away_net_rating']:+.1f}"
        if 'home_injuries' in features:
            output += f"\n  Key Injuries: {features['home_injuries']} vs {features['away_injuries']}"
    
    return output.strip()


if __name__ == "__main__":
    # Demo usage
    init_model()
    
    # Test predictions
    games = [
        ("Celtics", "Lakers", "2025-02-15"),
        ("Warriors", "Nuggets", "2025-02-16"),
        ("Heat", "Knicks", "2025-02-17"),
        ("Suns", "Mavericks", None),  # Today's date
    ]
    
    print("\n" + "=" * 70)
    print("NBA GAME PREDICTIONS")
    print("=" * 70)
    
    for home, away, date in games:
        try:
            pred = predict_game(home, away, date)
            print("\n" + format_prediction(pred))
        except Exception as e:
            print(f"\nError predicting {home} vs {away}: {e}")
    
    print("\n" + "=" * 70)
