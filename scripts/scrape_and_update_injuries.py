"""Wrapper to run injury scraper and write a canonical CSV.

This script is suitable for running in CI (GitHub Actions) or locally.
It will attempt to scrape ESPN, and if that returns no data, leave existing CSV untouched.
If new data is found, it will overwrite `data/injury_reports/current_injuries.csv`.
"""
import csv
from datetime import datetime
from pathlib import Path
import logging

from data.game_context_collector import InjuryReportScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def write_csv(injuries_by_team, out_path: Path):
    rows = []
    today = datetime.now().strftime("%Y-%m-%d")
    for team, players in injuries_by_team.items():
        for p in players:
            rows.append({
                "team": team,
                "player": p.get("player") or p.get("name") or "",
                "status": p.get("status", ""),
                "details": p.get("details", ""),
                "date_updated": p.get("date_updated", today),
            })

    if not rows:
        logger.info("No injury rows to write.")
        return False

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["team", "player", "status", "details", "date_updated"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    logger.info(f"Wrote {len(rows)} injury rows to {out_path}")
    return True


def main():
    out_path = Path("data/injury_reports/current_injuries.csv")

    logger.info("Running ESPN injury scraper...")
    injuries = InjuryReportScraper.scrape_espn_injuries()

    if not injuries:
        logger.warning("ESPN scrape returned no data; using fallback if present.")
        # fallback loader will be used by the rest of the system; do not overwrite
        return 0

    success = write_csv(injuries, out_path)
    if not success:
        logger.warning("No data written.")
        return 1

    logger.info("Scrape complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
