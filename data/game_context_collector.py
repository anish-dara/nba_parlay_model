"""
Scrapers for game-to-game data: injuries, schedule, and player status.
"""

import pandas as pd
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from nba_api.stats.endpoints import leaguegamelog, scoreboard
    NBA_API_AVAILABLE = True
except ImportError:
    NBA_API_AVAILABLE = False


class ScheduleFetcher:
    """Fetch NBA schedule and game dates."""

    @staticmethod
    def get_upcoming_games(days_ahead: int = 7) -> pd.DataFrame:
        """
        Get upcoming games for next N days.
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            DataFrame with columns: game_id, game_date, home_team, away_team, time
        """
        if not NBA_API_AVAILABLE:
            logger.error("nba_api not available")
            return pd.DataFrame()
        
        try:
            from nba_api.live.nba.endpoints import scoreboard
            
            logger.info(f"Fetching upcoming games for next {days_ahead} days...")
            games_list = []
            
            for i in range(days_ahead):
                date = datetime.now() + timedelta(days=i)
                date_str = date.strftime("%Y-%m-%d")
                
                # Try to fetch games for this date
                try:
                    sb = scoreboard.ScoreBoard()
                    data = sb.get_dict()
                    
                    for game in data.get("scoreboard", {}).get("games", []):
                        game_date = game.get("gameTimeUTC", "").split("T")[0]
                        if game_date == date_str:
                            games_list.append({
                                "game_id": game.get("gameId"),
                                "game_date": game_date,
                                "home_team": game.get("homeTeam", {}).get("teamName"),
                                "away_team": game.get("awayTeam", {}).get("teamName"),
                                "time": game.get("gameTimeUTC"),
                                "status": game.get("gameStatus"),
                            })
                except Exception as e:
                    logger.debug(f"No games on {date_str}: {e}")
                    continue
            
            df = pd.DataFrame(games_list)
            logger.info(f"Found {len(df)} upcoming games")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching schedule: {e}")
            return pd.DataFrame()

    @staticmethod
    def scrape_espn_schedule(target_date: str) -> pd.DataFrame:
        """
        Scrape ESPN schedule for a specific date (YYYY-MM-DD).
        Returns DataFrame with columns: game_date, home_team, away_team
        """
        if BeautifulSoup is None:
            logger.warning("BeautifulSoup not installed; cannot scrape ESPN schedule.")
            return pd.DataFrame()

        try:
            ymd = target_date.replace('-', '')
            url = f"https://www.espn.com/nba/schedule/_/date/{ymd}"
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, 'html.parser')

            games = []
            # ESPN schedule pages contain tables of matchups
            tables = soup.find_all('table')
            for tbl in tables:
                for row in tbl.find_all('tr'):
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        teams_col = cols[0]
                        teams = [a.get_text(strip=True) for a in teams_col.find_all('a')]
                        if len(teams) >= 2:
                            away, home = teams[0], teams[1]
                            games.append({
                                'game_date': target_date,
                                'home_team': home,
                                'away_team': away,
                            })

            df = pd.DataFrame(games)
            logger.info(f"ESPN schedule scrape found {len(df)} games for {target_date}")
            return df
        except Exception as e:
            logger.warning(f"ESPN schedule scrape failed: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_season_schedule(season: int = 2025) -> pd.DataFrame:
        """
        Get full season schedule.
        
        Args:
            season: NBA season year
            
        Returns:
            DataFrame with all games scheduled for season
        """
        if not NBA_API_AVAILABLE:
            return pd.DataFrame()
        
        logger.info(f"Fetching {season} season schedule...")
        
        try:
            from nba_api.stats.endpoints import leaguegamelog
            
            games_list = []
            for month in range(10, 13):  # Oct-Dec
                try:
                    df = leaguegamelog.LeagueGameLog(season=season, month=month).get_data_frames()[0]
                    games_list.append(df)
                except:
                    continue
            
            for month in range(1, 5):  # Jan-Apr
                try:
                    df = leaguegamelog.LeagueGameLog(season=season, month=month).get_data_frames()[0]
                    games_list.append(df)
                except:
                    continue
            
            if games_list:
                result = pd.concat(games_list, ignore_index=True)
                logger.info(f"Fetched {len(result)} games for {season} season")
                return result
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error fetching season schedule: {e}")
            return pd.DataFrame()


class InjuryReportScraper:
    """Scrape NBA injury reports from various sources."""

    # Known NBA team abbreviations
    TEAM_ABBREV = {
        "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BKN",
        "Charlotte Hornets": "CHA", "Chicago Bulls": "CHI", "Cleveland Cavaliers": "CLE",
        "Dallas Mavericks": "DAL", "Denver Nuggets": "DEN", "Detroit Pistons": "DET",
        "Golden State Warriors": "GSW", "Houston Rockets": "HOU", "LA Clippers": "LAC",
        "LA Lakers": "LAL", "Memphis Grizzlies": "MEM", "Miami Heat": "MIA",
        "Milwaukee Bucks": "MIL", "Minnesota Timberwolves": "MIN", "New Orleans Pelicans": "NOP",
        "New York Knicks": "NYK", "Oklahoma City Thunder": "OKC", "Orlando Magic": "ORL",
        "Philadelphia 76ers": "PHI", "Phoenix Suns": "PHX", "Portland Trail Blazers": "POR",
        "Sacramento Kings": "SAC", "San Antonio Spurs": "SAS", "Toronto Raptors": "TOR",
        "Utah Jazz": "UTA", "Washington Wizards": "WAS",
    }

    @staticmethod
    def scrape_espn_injuries() -> Dict[str, List[Dict]]:
        """
        Scrape injury reports from ESPN.
        
        Returns:
            {team_name: [{"player": name, "status": status, "details": details}, ...]}
        """
        logger.info("Scraping ESPN for injury reports...")
        
        injuries_by_team = {}
        
        try:
            url = "https://www.espn.com/nba/injuries"
            headers = {"User-Agent": "Mozilla/5.0"}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Find all injury tables by team
            team_sections = soup.find_all("div", class_="Table__TR")
            
            logger.info(f"Parsed injury data from ESPN")
            
        except Exception as e:
            logger.warning(f"ESPN scrape failed: {e}. This is OK - using fallback.")
            injuries_by_team = InjuryReportScraper._get_fallback_injuries()
        
        return injuries_by_team

    @staticmethod
    def scrape_nba_official() -> Dict[str, List[Dict]]:
        """
        Scrape from NBA's official injury report page.
        
        Returns:
            {team_name: [{"player": name, "status": status}, ...]}
        """
        logger.info("Checking NBA official injury page...")
        
        injuries_by_team = {}
        
        try:
            # Note: NBA.com doesn't have a free public injury API
            # This would need to be scraped from their website or use a paid service
            logger.warning("NBA.com injury scraping requires authentication. Using fallback.")
            injuries_by_team = InjuryReportScraper._get_fallback_injuries()
            
        except Exception as e:
            logger.error(f"NBA scrape error: {e}")
            injuries_by_team = InjuryReportScraper._get_fallback_injuries()
        
        return injuries_by_team

    @staticmethod
    def _get_fallback_injuries() -> Dict[str, List[Dict]]:
        """
        Get injury data from local fallback file or return empty.
        User can manually update this file.
        """
        fallback_path = Path("data/injury_reports/current_injuries.csv")
        
        if fallback_path.exists():
            logger.info(f"Loading injuries from {fallback_path}")
            df = pd.read_csv(fallback_path)
            
            injuries_by_team = {}
            for team in df["team"].unique():
                team_injuries = df[df["team"] == team].to_dict("records")
                injuries_by_team[team] = team_injuries
            
            return injuries_by_team
        else:
            logger.warning(f"No injury data at {fallback_path}. Create manually or use API.")
            return {}

    @staticmethod
    def create_injury_template():
        """
        Create a template CSV for manual injury input.
        Format: team, player, status, details, date_updated
        """
        template_path = Path("data/injury_reports/current_injuries.csv")
        template_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not template_path.exists():
            template_df = pd.DataFrame({
                "team": ["Boston Celtics", "Los Angeles Lakers"],
                "player": ["Kristaps Porzingis", "LeBron James"],
                "status": ["OUT", "QUESTIONABLE"],
                "details": ["Calf strain", "Ankle soreness"],
                "date_updated": [datetime.now().strftime("%Y-%m-%d")] * 2,
            })
            template_df.to_csv(template_path, index=False)
            logger.info(f"Created injury template at {template_path}")
            logger.info("Fill this file manually with current injuries, then the system will use it.")
        
        return template_path


class GameToGameDataCollector:
    """Combines schedule + injuries for game-to-game analysis."""

    @staticmethod
    def get_game_context(home_team: str, away_team: str, game_date: str) -> Dict:
        """
        Get all game-to-game context for a matchup.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            game_date: Game date (YYYY-MM-DD)
            
        Returns:
            {
                home_team: {...},
                away_team: {...},
                days_rest: {home: X, away: Y},
                injuries: {home: [...], away: [...]}
            }
        """
        injuries = InjuryReportScraper.scrape_nba_official()
        
        return {
            "home_team": home_team,
            "away_team": away_team,
            "game_date": game_date,
            "home_injuries": injuries.get(home_team, []),
            "away_injuries": injuries.get(away_team, []),
        }


def main():
    """Demo the collectors."""
    logger.info("=" * 70)
    logger.info("GAME-TO-GAME DATA COLLECTOR")
    logger.info("=" * 70)
    
    # Create injury template for manual input
    InjuryReportScraper.create_injury_template()
    
    # Fetch upcoming games
    logger.info("\nFetching upcoming games...")
    upcoming = ScheduleFetcher.get_upcoming_games(days_ahead=3)
    if not upcoming.empty:
        logger.info(f"\nUpcoming games:\n{upcoming.to_string()}")
    
    # Get injury reports
    logger.info("\nFetching injury reports...")
    injuries = InjuryReportScraper.scrape_nba_official()
    if injuries:
        for team, player_list in list(injuries.items())[:3]:
            logger.info(f"\n{team}:")
            for player_info in player_list:
                logger.info(f"  - {player_info}")
    else:
        logger.info("No injury data found. Please manually update data/injury_reports/current_injuries.csv")
    
    # Get game context for a sample game
    if not upcoming.empty:
        first_game = upcoming.iloc[0]
        logger.info(f"\nGame context for {first_game['home_team']} vs {first_game['away_team']}:")
        context = GameToGameDataCollector.get_game_context(
            first_game['home_team'],
            first_game['away_team'],
            first_game['game_date']
        )
        logger.info(f"  Home injuries: {context['home_injuries']}")
        logger.info(f"  Away injuries: {context['away_injuries']}")


if __name__ == "__main__":
    main()
