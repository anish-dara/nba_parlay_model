# NBA Parlay Model - Project Index

## 📚 Documentation (READ THESE FIRST)

| File | Purpose |
|------|---------|
| [README.md](README.md) | Project overview, features, setup instructions |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, module descriptions, data flow |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Development workflow, examples, debugging |
| [CLEANUP_SUMMARY.md](CLEANUP_SUMMARY.md) | Cleanup operations performed |

---

## 🎯 Core Modules

### Data Collection & Preprocessing
| File | Purpose |
|------|---------|
| [data/collector.py](data/collector.py) | Live odds polling (The Odds API) |
| [data/fetch_historical_games.py](data/fetch_historical_games.py) | Fetch ~2000 games from nba_api |
| [data/player_stats_collector.py](data/player_stats_collector.py) | Player stats + prop odds scraping framework |

### Feature Engineering
| File | Purpose |
|------|---------|
| [analysis/feature_engineering.py](analysis/feature_engineering.py) | Team stats, recent form, matchup scoring |
| [analysis/dataset_builder.py](analysis/dataset_builder.py) | Merge games with odds into training dataset |

### Predictive Models  
| File | Purpose |
|------|---------|
| [models/game_predictor.py](models/game_predictor.py) | **XGBoost** for P(home_win) prediction |
| [models/prop_predictor.py](models/prop_predictor.py) | XGBoost for player prop O/U lines |
| [models/parlay_builder.py](models/parlay_builder.py) | EV calculator & parlay optimizer |

### Utilities & Configuration
| File | Purpose |
|------|---------|
| [utils/calculations.py](utils/calculations.py) | Odds math, probability conversion, EV calculations |
| [config/settings.py](config/settings.py) | API keys, thresholds, hyperparameters |

### Tests (18 tests, all passing ✅)
| File | Purpose | Count |
|------|---------|-------|
| [tests/test_calculations.py](tests/test_calculations.py) | Unit tests for probability/odds math | 5 |
| [tests/test_dataset.py](tests/test_dataset.py) | Feature engineering & pipeline tests | 8 |
| [tests/test_models.py](tests/test_models.py) | XGBoost & parlay logic tests | 5 |

---

## 🚀 Main Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| [train_models.py](train_models.py) | Train XGBoost on historical data | `python train_models.py` |
| [demo_pipeline.py](demo_pipeline.py) | End-to-end pipeline demo | `python demo_pipeline.py` |

---

## ⚙️ Project Configuration

| File | Purpose |
|------|---------|
| [requirements.txt](requirements.txt) | Python dependencies (pip install -r) |
| [setup.py](setup.py) | Package metadata & installation |
| [.env.example](.env.example) | Environment variables template |
| [.gitignore](.gitignore) | Git ignore rules |

---

## 📊 Project Status

```
✅ Core Features:
   - XGBoost game prediction model
   - Player prop prediction framework
   - EV calculator with Kelly criterion
   - Live odds collector (The Odds API)
   - Historical game fetcher (nba_api)
   - Comprehensive feature engineering

✅ Code Quality:
   - 18/18 tests passing
   - PEP 8 compliant
   - Type hints on all functions
   - Comprehensive docstrings
   - Clean directory structure
   - No unused imports

⏳ In Progress:
   - Player prop odds scraping (placeholder)
   - Real-time prediction pipeline
   
📋 Future:
   - Backtesting engine
   - Flask/FastAPI backend
   - React dashboard
   - Bankroll management
```

---

## 🎮 Quick Commands

```bash
# Setup
python -m venv venv
pip install -r requirements.txt

# Test
pytest tests/ -v

# Train models
python train_models.py

# Demo
python demo_pipeline.py

# Explore
jupyter notebook
```

---

## 🔗 Key Data Files

| Path | Status | Format |
|------|--------|--------|
| `data/processed/historical_games.csv` | Ready | CSV (2049 games) |
| `data/processed/odds.csv` | Ready | CSV (live odds appends) |
| `data/processed/odds_history.sqlite` | Ready | SQLite (odds history) |
| `models/saved_models/game_predictor.pkl` | Not yet trained | joblib (XGBoost) |

---

## 📖 Reading Order

**For New Developers:**
1. [README.md](README.md) - What is this project?
2. [ARCHITECTURE.md](ARCHITECTURE.md) - How is it structured?
3. [DEVELOPMENT.md](DEVELOPMENT.md) - How do I develop?
4. Review [models/game_predictor.py](models/game_predictor.py) - Core model
5. Review [models/parlay_builder.py](models/parlay_builder.py) - EV logic

**For Data Scientists:**
1. [ARCHITECTURE.md](ARCHITECTURE.md) - Data flow section
2. [analysis/feature_engineering.py](analysis/feature_engineering.py)
3. [tests/test_dataset.py](tests/test_dataset.py) - See example workflows
4. [train_models.py](train_models.py) - Training pipeline

**For ML Engineers:**
1. [models/game_predictor.py](models/game_predictor.py) - XGBoost setup
2. [DEVELOPMENT.md](DEVELOPMENT.md) - Tuning section
3. [tests/test_models.py](tests/test_models.py) - Testing patterns

---

## 🐛 Troubleshooting

See [DEVELOPMENT.md#Common Issues & Solutions](DEVELOPMENT.md) for:
- ImportError solutions
- Data pipeline debugging
- Model training issues
- API rate limiting

---

**Last Updated:** February 15, 2026  
**Status:** 🟢 Ready for development and model training  
**Test Coverage:** 18/18 passing  

