"""Polling collector for live odds using The Odds API.

Usage:
  - Put your API key in a `.env` file as `ODDS_API_KEY=your_key` or pass it to
    the `OddsCollector` constructor.
  - Run as a script to continuously poll and persist odds to CSV and SQLite.

This module intentionally avoids external DB dependencies and writes to local
storage so it's easy to run on a low budget machine.
"""
from __future__ import annotations

import os
import time
import logging
import sqlite3
from typing import Any, Dict, List, Optional
from datetime import datetime

import requests
from dotenv import load_dotenv

from utils.calculations import american_to_decimal

load_dotenv()

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class OddsCollector:
    BASE = "https://api.the-odds-api.com/v4/sports"

    def __init__(self, api_key: Optional[str] = None, out_csv: str = "data/processed/odds.csv", sqlite_db: str = "data/processed/odds_history.sqlite", sport_key: str = "basketball_nba"):
        self.api_key = api_key or os.getenv("ODDS_API_KEY")
        if not self.api_key:
            raise ValueError("ODDS_API_KEY not provided; set it via env or pass to OddsCollector")
        self.out_csv = out_csv
        self.sqlite_db = sqlite_db
        self.sport_key = sport_key
        os.makedirs(os.path.dirname(self.out_csv), exist_ok=True)

    def fetch_odds(self, regions: str = "us", odds_format: str = "american") -> List[Dict[str, Any]]:
        # The Odds API doesn't support 'moneyline' market name directly; use h2h (head-to-head) instead
        # Note: basketball_nba may not have active games during off-season; try _all_stars if needed
        url = f"{self.BASE}/{self.sport_key}/odds"
        params = {"apiKey": self.api_key, "regions": regions, "oddsFormat": odds_format}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def normalize(self, raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for ev in raw:
            event_id = ev.get("id")
            commence = ev.get("commence_time")
            for bookmaker in ev.get("bookmakers", []):
                provider = bookmaker.get("key")
                for market in bookmaker.get("markets", []):
                    mkey = market.get("key")
                    for outcome in market.get("outcomes", []):
                        am = outcome.get("price")
                        try:
                            dec = american_to_decimal(am) if am is not None else None
                        except Exception:
                            dec = None
                        rows.append({
                            "event_id": event_id,
                            "start_time": commence,
                            "provider": provider,
                            "market": mkey,
                            "selection": outcome.get("name"),
                            "odds_american": am,
                            "odds_decimal": dec,
                            "timestamp": datetime.utcnow().isoformat(),
                        })
        return rows

    def save_csv(self, rows: List[Dict[str, Any]]):
        import csv

        if not rows:
            return
        write_header = not os.path.exists(self.out_csv)
        with open(self.out_csv, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            if write_header:
                writer.writeheader()
            writer.writerows(rows)

    def save_sqlite(self, rows: List[Dict[str, Any]]):
        if not rows:
            return
        conn = sqlite3.connect(self.sqlite_db)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS odds_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT,
                start_time TEXT,
                provider TEXT,
                market TEXT,
                selection TEXT,
                odds_american REAL,
                odds_decimal REAL,
                timestamp TEXT
            )
            """
        )
        insert_sql = "INSERT INTO odds_history (event_id, start_time, provider, market, selection, odds_american, odds_decimal, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        to_insert = [(
            r.get("event_id"), r.get("start_time"), r.get("provider"), r.get("market"), r.get("selection"), r.get("odds_american"), r.get("odds_decimal"), r.get("timestamp")
        ) for r in rows]
        cur.executemany(insert_sql, to_insert)
        conn.commit()
        conn.close()

    def run(self, poll_seconds: int = 30):
        backoff = 1
        while True:
            try:
                raw = self.fetch_odds()
                rows = self.normalize(raw)
                self.save_csv(rows)
                self.save_sqlite(rows)
                LOGGER.info("Appended %d rows", len(rows))
                backoff = 1
            except requests.HTTPError as e:
                LOGGER.warning("HTTP error: %s", e)
                backoff = min(backoff * 2, 300)
            except Exception as e:
                LOGGER.exception("Error collecting odds: %s", e)
                backoff = min(backoff * 2, 300)
            time.sleep(poll_seconds + backoff)


if __name__ == "__main__":
    # Allow running with direct key for convenience, but prefer .env
    key = os.getenv("ODDS_API_KEY")
    collector = OddsCollector(api_key=key)
    collector.run()
