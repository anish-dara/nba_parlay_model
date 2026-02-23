# NBA Parlay Model - Development Guide

## Quick Start

### 1. Setup Environment
```bash
python -m venv venv
source venv/Scripts/activate  # Windows
pip install -r requirements.txt
```

### 2. Configure API Keys
```bash
cp .env.example .env
# Edit .env with your The Odds API key from https://the-odds-api.com
```

### 3. Run Tests
```bash
pytest tests/ -v
```

### 4. Fetch Historical Data & Train Models
```bash
python train_models.py
```

## Key Commands

| Command | Purpose |
|---------|---------|
| `pytest tests/ -v` | Run all 18 tests |
| `python train_models.py` | Train XGBoost on historical games |
| `python demo_pipeline.py` | Show end-to-end data pipeline |
| `python -m jupyter notebook` | Start Jupyter for exploration |

## Code Style & Standards

### Python Style
- Follow **PEP 8** guidelines
- Use type hints: `def func(x: int) -> str:`
- Docstrings: Google-style for all module, class, function definitions
- Max line length: 100 characters

### Module Organization
```python
"""Module docstring explaining purpose."""
# Imports (sorted: stdlib, 3rd-party, local)
import os
import sys
from pathlib import Path

import pandas as pd
import numpy as np

from config import settings
from utils import calculations

# Constants
DEFAULT_VALUE = 42

# Classes
class MyClass:
    """Class docstring."""
    pass

# Functions
def my_function(x: int) -> int:
    """Function docstring."""
    return x * 2

# Main
if __name__ == "__main__":
    main()
```

### Documentation
- All public functions/classes require docstrings
- Include Args, Returns, Raises, Examples sections
- Example:
```python
def calculate_parlay_odds(odds: List[float]) -> float:
    """Calculate combined odds for parlay.
    
    Args:
        odds: List of decimal odds for each leg.
        
    Returns:
        Combined decimal odds.
        
    Raises:
        ValueError: If odds contain invalid values.
        
    Example:
        >>> calculate_parlay_odds([2.0, 1.5])
        3.0
    """
```

## Adding New Features

### Step 1: Create Feature Engineering Function
```python
# analysis/feature_engineering.py
def add_new_feature(df: pd.DataFrame) -> pd.DataFrame:
    """Add new feature to dataset."""
    df['new_feature'] = df['col_a'] / df['col_b']
    return df
```

### Step 2: Write Unit Test
```python
# tests/test_dataset.py
def test_new_feature():
    df = pd.DataFrame({'col_a': [10], 'col_b': [2]})
    result = add_new_feature(df)
    assert result['new_feature'].iloc[0] == 5
```

### Step 3: Integrate into Pipeline
```python
# analysis/dataset_builder.py
games_df = add_game_features(games_df)
games_df = add_new_feature(games_df)  # Add here
```

### Step 4: Update Model Features
```python
# models/game_predictor.py
FEATURE_COLS = [
    ...,
    'new_feature',  # Add here
]
```

## Model Training Workflow

### 1. Prepare Dataset
```python
from analysis.dataset_builder import build_dataset

df = build_dataset(
    games_csv='data/processed/historical_games.csv',
    odds_csv='data/processed/odds.csv'
)
```

### 2. Train Game Predictor
```python
from models.game_predictor import GamePredictor

predictor = GamePredictor()
results = predictor.train(df, test_size=0.2, hyperparams={
    'max_depth': 7,
    'learning_rate': 0.05,
    'n_estimators': 200,
})

print(f"Test AUC: {results['test_auc']:.4f}")
```

### 3. Evaluate & Save
```python
# Get feature importance
importance_df = predictor.get_feature_importance()
print(importance_df.head(10))

# Save trained model
predictor.save('models/saved_models/game_predictor.pkl')
```

### 4. Make Predictions
```python
probabilities = predictor.predict_proba(new_games_df)  # ndarray of [0, 1]
binary_predictions = predictor.predict(new_games_df)   # ndarray of 0 or 1
```

## Parlay Generation Workflow

### 1. Load Model & Get Predictions
```python
from models.game_predictor import GamePredictor

predictor = GamePredictor()
predictor.load('models/saved_models/game_predictor.pkl')
probs = predictor.predict_proba(today_games_df)
```

### 2. Get Today's Odds
```python
# Could come from API or database
odds = {
    'game_1': {'home': 1.91, 'away': 1.91},
    'game_2': {'home': 1.83, 'away': 1.98},
}
```

### 3. Build Parlays
```python
from models.parlay_builder import ParlayBuilder

builder = ParlayBuilder(min_ev_pct=5.0, max_legs=5)
parlays = builder.build_game_parlays(probs, odds)

for parlay in parlays:
    print(f"Legs: {parlay['legs']}")
    print(f"EV%: {parlay['ev_pct']:.2f}%")
    print(f"Kelly %: {parlay['kelly_fraction']:.2%}")
    print()
```

## Debugging

### Check Data Pipeline
```python
import pandas as pd

games = pd.read_csv('data/processed/historical_games.csv')
print(games.shape)
print(games.columns)
print(games.isnull().sum())
```

### Validate Model Training
```python
from models.game_predictor import GamePredictor
import logging

logging.basicConfig(level=logging.DEBUG)
predictor = GamePredictor()
results = predictor.train(df)
```

### Test Individual Functions
```python
from utils.calculations import calculate_parlay_odds

odds = [2.0, 1.5]
result = calculate_parlay_odds(odds)
assert result == 3.0, f"Expected 3.0, got {result}"
```

## Common Issues & Solutions

### Issue: "xgboost not installed"
**Solution:** `pip install xgboost`

### Issue: "nba_api unavailable"
**Solution:** Models handle gracefully; feature engineering fills NaN with neutral values

### Issue: Tests fail with low AUC
**Solution:** Ensure sample data has correlation to target (see `test_models.py` fixture)

### Issue: "The Odds API rate limit exceeded"
**Solution:** Collector uses exponential backoff; check `.env` for valid API key

## Continuous Integration

Run this before commits:
```bash
# Format code (optional, for future)
# black . --line-length 100

# Lint (optional, for future)
# pylint models/ data/ analysis/ utils/

# Test
pytest tests/ -v

# Type check (optional, for future)
# mypy models/ data/ analysis/ utils/
```

## Performance Optimization

### XGBoost Hyperparameter Tuning
```python
hyperparams = {
    'max_depth': 7,           # ↑ increases complexity (overfit risk)
    'learning_rate': 0.05,    # ↓ slower learning (underfitting risk)
    'n_estimators': 200,      # ↑ more trees (training time)
    'subsample': 0.8,         # Data sampling per iteration
    'colsample_bytree': 0.8,  # Feature sampling per tree
    'min_child_weight': 5,    # Min samples per leaf
    'reg_lambda': 1.0,        # L2 regularization (prevents overfitting)
    'reg_alpha': 0.5,         # L1 regularization
}
```

### Parallel Training
XGBoost uses n_jobs=-1 automatically. For large datasets, consider:
```python
predictor = GamePredictor()
results = predictor.train(
    df,
    hyperparams={'n_jobs': -1, 'tree_method': 'gpu_hist'}  # GPU acceleration
)
```

## Future Enhancements

- [ ] Player prop odds scraping (Selenium/Playwright)
- [ ] Real-time odds polling & database storage
- [ ] Backtesting engine with equity curves
- [ ] Flask/FastAPI REST API for parlay generation
- [ ] React dashboard for real-time recommendations
- [ ] Bankroll & position sizing optimization
- [ ] Prop correlations (handle dependent bets)
- [ ] Line movement analysis

