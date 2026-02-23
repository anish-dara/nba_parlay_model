# NBA Parlay Model

A machine learning model for identifying high-value NBA parlays through statistical analysis and predictive modeling.

## Project Overview

This project builds a system to:
- Collect and analyze NBA game data
- Build predictive models for game outcomes
- Calculate parlay probabilities and expected value
- Identify and recommend high-value betting opportunities

## Project Structure

```
nba_parlay_model/
├── data/                 # Data collection and preprocessing
├── models/               # Machine learning models and predictions
├── analysis/             # Statistical analysis and backtesting
├── config/               # Configuration and constants
├── utils/                # Helper functions and utilities
├── tests/                # Unit tests
├── requirements.txt      # Project dependencies
├── setup.py             # Package configuration
└── README.md            # This file
```

## Installation

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment:**
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install the package in development mode:**
   ```bash
   pip install -e .
   ```

## Development

### Running Tests

```bash
pytest tests/
```

### Working with Jupyter Notebooks

```bash
jupyter notebook
```

## Key Dependencies

- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computations
- **scikit-learn**: Machine learning models
- **requests**: HTTP requests for data collection
- **matplotlib/seaborn**: Data visualization
- **statsmodels**: Statistical modeling

## Getting Started

1. Start by creating data collection scripts in the `data/` module
2. Build exploratory analysis in `analysis/` to understand the data
3. Develop predictive models in the `models/` module
4. Implement parlay value calculations and recommendations
5. Add tests in `tests/` to ensure code reliability

## Configuration

Place configuration files and constants in the `config/` module. Use environment variables for sensitive data (API keys, credentials, etc.) with `python-dotenv`.

## Live data collectors

We provide a small polling collector for live odds at `data/collector.py` that uses The Odds API.

Quick start (Windows PowerShell):

```powershell
venv\Scripts\activate
copy .env.example .env
# Edit .env and set ODDS_API_KEY
python data/collector.py
```

The collector appends CSV rows into `data/processed/odds.csv` and stores history in `data/processed/odds_history.sqlite`.

## Training data pipeline

The project includes end-to-end training data creation:

1. **Fetch historical games** (`data/fetch_historical_games.py`):
   - Retrieves completed NBA games from nba_api for 2024-25 seasons
   - Saves to `data/processed/historical_games.csv`

2. **Feature engineering** (`analysis/feature_engineering.py`):
   - Computes season-to-date team stats (win%, point differential, etc.)
   - Calculates recent form (14-day rolling stats)
   - Prepares features for modeling

3. **Dataset builder** (`analysis/dataset_builder.py`):
   - Merges historical games with collected odds
   - Matches opening/closing odds with game outcomes
   - Produces `data/processed/training_dataset.csv` for model training

Quick start:

```powershell
# Run the full pipeline (fetches games, builds dataset)
python demo_pipeline.py
```

This will:
- Fetch ~2000 historical NBA games from nba_api
- Load any collected odds
- Engineer features and save training dataset
- Show sample data and next steps

## Contributing

Follow PEP 8 style guidelines and ensure all code is documented with docstrings.

## License

MIT
