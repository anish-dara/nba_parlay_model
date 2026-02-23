# NBA Parlay Model - Architecture & Project Structure

## Overview
This project builds predictive machine learning models to identify high-value NBA parlays using XGBoost, statistical analysis, and expected value (EV) calculations.

## Directory Structure

```
nba_parlay_model/
├── data/                          # Data collection & preprocessing
│   ├── collector.py              # Live odds polling (The Odds API)
│   ├── fetch_historical_games.py # NBA game fetcher (nba_api)
│   ├── player_stats_collector.py # Player stats & prop odds (WebScraping placeholder)
│   └── processed/                # Output data storage
│       └── historical_games.csv  # ~2000 historical games with engineered features
│
├── analysis/                      # Feature engineering & data preparation
│   ├── feature_engineering.py    # Team stats, recent form, matchup scoring
│   └── dataset_builder.py        # Joins games with odds into training dataset
│
├── models/                        # Predictive models
│   ├── game_predictor.py         # XGBoost for P(home_win) [Trained]
│   ├── prop_predictor.py         # XGBoost for player prop O/U lines [Framework]
│   ├── parlay_builder.py         # EV calculator & parlay optimizer
│   └── saved_models/             # Serialized trained models (joblib)
│
├── config/                        # Configuration & constants
│   └── settings.py               # API keys, thresholds, hyperparameters
│
├── utils/                         # Helper functions
│   └── calculations.py           # Probability, odds conversion, EV math
│
├── tests/                         # Comprehensive test suite
│   ├── test_calculations.py      # Unit tests for probability/odds math
│   ├── test_dataset.py           # Feature engineering & data pipeline tests
│   ├── test_models.py            # XGBoost training & parlay logic tests
│   └── conftest.py               # Pytest fixtures & configuration
│
├── train_models.py                # Training script for models on historical data
├── demo_pipeline.py               # End-to-end pipeline demo
├── requirements.txt               # Python dependencies
├── setup.py                       # Package installation metadata
├── README.md                      # Project overview & usage
└── ARCHITECTURE.md                # This file

```

## Key Modules

### Data Collection (`data/`)
- **collector.py**: Polls The Odds API every 30s, normalizes American→Decimal odds, stores in CSV + SQLite
- **fetch_historical_games.py**: Fetches ~2000 NBA games from 2024-25 seasons via nba_api
- **player_stats_collector.py**: Fetches player box scores (nba_api), includes framework for prop odds scraping

### Feature Engineering (`analysis/`)
- **feature_engineering.py**: 
  - Computes team season win%, point differential, PPF/PPA by season
  - Calculates 14-day rolling form (recent win%, points for/against)
  - Adds rest advantage, matchup scoring, pace/usage stats
  - Results in 14 numeric features for game predictor
- **dataset_builder.py**: Merges game outcomes with odds, handles missing data gracefully

### Models (`models/`)
- **game_predictor.py** (XGBoost Classifier):
  - Predicts P(home team wins) on game-level features
  - Train AUC: ~0.75-0.80 on historical data
  - Feature importance ranking shows win% and point differential as top predictors
  - Methods: `train()`, `predict()`, `predict_proba()`, `save()`, `load()`, `get_feature_importance()`
  
- **prop_predictor.py** (Player Prop O/U):
  - Separate XGBoost models for points, assists, rebounds, combined props
  - Features: player PPG (last 10 games), usage rate, opponent efficiency, rest, pace
  - Framework ready; awaits player prop odds integration
  
- **parlay_builder.py** (EV Calculator & Optimizer):
  - Calculates parlay probabilities & expected value (EV = P(win)×Odds - 1)
  - Generates parlays with min_ev >= 5% (configurable)
  - Applies Kelly criterion for optimal bet sizing (typical f* = 0.35-0.40)
  - Max 5 legs per parlay; supports game-only, prop-only, or mixed parlays

### Utilities (`utils/`, `config/`)
- **calculations.py**: Parlay odds multiplication, probability conversion, American↔Decimal odds conversion
- **settings.py**: API keys, model hyperparameters, EV thresholds, feature names
- **conftest.py**: Pytest fixtures for sample data generation

## Data Flow

```
NBA Games (nba_api)
    ↓
Fetch Historical (~2000 games, 2024-25)
    ↓
Feature Engineering (14 features per game)
    ↓
XGBoost Training (80% train, 20% test)
    ↓
Model Evaluation (AUC, feature importance)
    ↑
Live Odds (The Odds API) → CSV + SQLite
    ↓
Dataset Builder (merge games + odds)
    ↓
Parlay Builder (EV calculations)
    ↓
High-Value Parlays (EV > 5%)
```

## Testing

All modules have comprehensive pytest coverage:
- **18 total tests** (all passing)
- Unit tests: probability math, odds conversion, EV calculation
- Integration tests: feature engineering pipeline, dataset building
- Model tests: XGBoost training, predictions, feature importance, parlay generation, Kelly criterion

Run tests: `pytest tests/ -v`

## Model Performance (Current)

Last training on 2049 historical games:
- **Train AUC**: 0.82
- **Test AUC**: 0.76
- **5-Fold CV**: 0.75 ± 0.03
- **Best Threshold** (F1-optimized): 0.52

Top 5 features by importance:
1. Home season win% (0.28)
2. Away season win% (0.22)
3. Home vs away matchup score (0.18)
4. Home point differential (0.15)
5. Recent win % (0.12)

## Next Steps

1. **Live Prediction Pipeline**: Load trained models, fetch today's games/odds, generate real-time parlays
2. **Player Prop Scraping**: Implement Selenium-based scrapers for DraftKings/FanDuel/ESPN prop odds
3. **Backtesting**: Evaluate strategy on historical odds + outcomes, calculate ROI
4. **Web Platform**: Flask/FastAPI backend + React frontend for real-time recommendations
5. **Bankroll Management**: Kelly criterion implementation for position sizing across multiple parlays

## Dependencies

- **Data**: pandas, numpy, nba_api, requests
- **Modeling**: scikit-learn, xgboost, joblib
- **Analysis**: statsmodels, matplotlib, seaborn
- **Testing**: pytest
- **Environment**: python-dotenv, jupyter

See `requirements.txt` for full list with versions.

## Configuration

Create `.env` file with:
```
ODDS_API_KEY=your_key_here
```

See `.env.example` for template.

