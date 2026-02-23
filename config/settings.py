"""Configuration settings and API endpoints for the NBA Parlay Model."""

# NBA API endpoints
NBA_API_BASE = "https://api.nba.com/v1"
STATS_API_BASE = "https://stats.nba.com/stats"

# Model configurations
MODEL_TEST_SIZE = 0.2
MODEL_RANDOM_STATE = 42
CROSS_VALIDATION_FOLDS = 5

# Parlay calculations
MIN_EV_THRESHOLD = 0.05  # Minimum expected value (5%)
MIN_ODDS_THRESHOLD = -200  # Minimum odds to consider
DEFAULT_PARLAY_LEGS = 2  # Default number of games in a parlay

# Data configuration
DATA_DIR = "data"
RAW_DATA_DIR = "data/raw"
PROCESSED_DATA_DIR = "data/processed"
MODEL_DIR = "models/trained"

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "logs/parlay_model.log"
