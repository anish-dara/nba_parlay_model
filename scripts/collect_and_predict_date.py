"""Fetch schedule + injuries for a date and predict odds for each game.

Usage:
  python scripts/collect_and_predict_date.py 2026-02-19
"""
import sys
from datetime import datetime
from pathlib import Path
import logging

# Ensure repo root is on sys.path so imports like `data` and `models` work
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd

from data.game_context_collector import ScheduleFetcher, InjuryReportScraper, GameToGameDataCollector
from predictor import predict_game, init_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_schedule_for_date(target_date: str):
    """Return list of games for target_date. Each game is dict with home_team, away_team, game_date."""
    logger.info(f"Fetching schedule for {target_date}...")
    # Try ScheduleFetcher.get_upcoming_games for the next few days and filter
    df = ScheduleFetcher.get_upcoming_games(days_ahead=3)
    if df is None or df.empty:
        logger.warning("ScheduleFetcher returned no games (nba_api may be unavailable).")
        return []

    # Normalize column names
    if 'game_date' not in df.columns and 'date' in df.columns:
        df = df.rename(columns={'date': 'game_date'})

    games = []
    for _, row in df.iterrows():
        gd = str(row.get('game_date'))
        if gd.startswith(target_date):
            games.append({
                'game_date': target_date,
                'home_team': row.get('home_team') or row.get('home') or row.get('homeTeam'),
                'away_team': row.get('away_team') or row.get('away') or row.get('awayTeam'),
            })

    logger.info(f"Found {len(games)} games on {target_date}")
    return games


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/collect_and_predict_date.py YYYY-MM-DD")
        return

    target_date = sys.argv[1]
    try:
        datetime.strptime(target_date, "%Y-%m-%d")
    except Exception:
        print("Invalid date format. Use YYYY-MM-DD")
        return

    # Run injury scraper (attempt)
    logger.info("Running injury scraper (ESPN)...")
    injuries = InjuryReportScraper.scrape_espn_injuries()
    if not injuries:
        logger.info("No scraped injuries; fallback to local CSV if present.")

    # Fetch schedule
    games = fetch_schedule_for_date(target_date)
    # If no games found via nba_api, attempt ESPN scrape fallback
    if not games:
        logger.info("Attempting ESPN schedule scrape fallback...")
        df_espn = ScheduleFetcher.scrape_espn_schedule(target_date)
        games = []
        if not df_espn.empty:
            for _, r in df_espn.iterrows():
                games.append({'game_date': r['game_date'], 'home_team': r['home_team'], 'away_team': r['away_team']})
    if not games:
        print(f"No games found for {target_date}")
        return

    # Ensure model/data loaded
    try:
        init_model()
    except Exception as e:
        logger.warning(f"init_model raised: {e} — continuing with fallback model if available")

    # Predict for each game
    rows = []
    for g in games:
        home = g['home_team']
        away = g['away_team']
        try:
            pred = predict_game(home, away, g['game_date'])
            rows.append({
                'date': g['game_date'],
                'home': home,
                'away': away,
                'home_win%': f"{pred['home_win_probability']*100:.1f}%",
                'away_win%': f"{pred['away_win_probability']*100:.1f}%",
                'predicted_winner': pred['predicted_winner'],
                'confidence': f"{pred['confidence']*100:.1f}%",
            })
        except Exception as e:
            logger.error(f"Prediction failed for {home} vs {away}: {e}")

    if rows:
        df_out = pd.DataFrame(rows)
        print(df_out.to_string(index=False))
    else:
        print("No predictions produced.")


if __name__ == '__main__':
    main()
