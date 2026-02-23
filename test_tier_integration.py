"""
Test the integrated tier-based prediction system.

Run this after collecting data with collect_all_data.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from predictor import predict_game, format_prediction, init_model


def main():
    print("\n" + "="*70)
    print("TESTING TIER-BASED PREDICTION SYSTEM")
    print("="*70)
    
    # Initialize
    print("\n1. Initializing model...")
    try:
        init_model()
        print("   ✓ Model initialized")
    except Exception as e:
        print(f"   ✗ Failed to initialize: {e}")
        print("\n   Make sure you've run: python collect_all_data.py")
        return
    
    # Test predictions
    print("\n2. Testing predictions...")
    
    test_games = [
        ("Boston Celtics", "Los Angeles Lakers"),
        ("Golden State Warriors", "Denver Nuggets"),
        ("Miami Heat", "New York Knicks"),
    ]
    
    for home, away in test_games:
        print(f"\n   Predicting: {home} vs {away}")
        try:
            prediction = predict_game(home, away)
            print(format_prediction(prediction))
            
            # Show breakdown if available
            if 'breakdown' in prediction and prediction['breakdown']:
                print("\n   Component Scores:")
                breakdown = prediction['breakdown']
                if 'home_scores' in breakdown:
                    for category, score in breakdown['home_scores'].items():
                        away_score = breakdown['away_scores'].get(category, 0)
                        print(f"     {category:20s} {score:5.1%} vs {away_score:5.1%}")
            
        except Exception as e:
            print(f"   ✗ Prediction failed: {e}")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    print("\nIf predictions worked, the tier-based model is integrated!")
    print("You can now use:")
    print("  - python predict_cli.py 'Celtics vs Lakers'")
    print("  - from predictor import predict_game")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
