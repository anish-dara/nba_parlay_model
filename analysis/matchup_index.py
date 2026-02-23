"""
Positional Matchup Index - Compare teams across all 5 positions + bench depth.

Outputs:
  - Offensive matchup split (per position + consolidated)
  - Defensive matchup split (per position + consolidated)  
  - Single combined matchup score
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Position definitions
POSITIONS = ["PG", "SG", "SF", "PF", "C"]
POSITION_NAMES = {
    "PG": "Point Guard",
    "SG": "Shooting Guard",
    "SF": "Small Forward",
    "PF": "Power Forward",
    "C": "Center"
}


class MatchupIndexBuilder:
    """Build positional matchup analysis between two teams."""

    def __init__(self, games_df: pd.DataFrame):
        """
        Args:
            games_df: Historical games with full box score details
        """
        self.games_df = games_df
        self.team_season_stats = None
        self.position_stats = {}

    def get_position_stat_avg(self, team: str, position: str, stat: str, 
                             reference_date: pd.Timestamp = None) -> float:
        """
        Get average stat for a team's position group.
        
        Args:
            team: Team name
            position: Position code (PG, SG, SF, PF, C)
            stat: Statistic name (PPG, RPG, APG, etc.)
            reference_date: As of this date (for historical context)
            
        Returns:
            Average stat value for position
        """
        # Compute team stats if not already done
        if self.team_season_stats is None:
            self._compute_team_stats()
        
        team_stats = self.team_season_stats.get(team, {})
        if not team_stats:
            # Return league average defaults if team not found
            defaults = {"PPG": 110, "PPG_allowed": 110, "RPG": 45, "APG": 27, "BPG": 5, "SPG": 7}
            base_stat = defaults.get(stat, 100)
        else:
            base_stat = team_stats.get(stat, 110)
        
        # Position-based scaling (rough estimates based on position role)
        position_weights = {
            "PG": {"PPG": 0.95, "APG": 1.3, "RPG": 0.7, "PPG_allowed": 1.0},
            "SG": {"PPG": 1.05, "APG": 0.9, "RPG": 0.8, "PPG_allowed": 1.0},
            "SF": {"PPG": 1.0, "APG": 0.95, "RPG": 0.95, "PPG_allowed": 1.0},
            "PF": {"PPG": 1.0, "APG": 0.85, "RPG": 1.2, "PPG_allowed": 1.0},
            "C": {"PPG": 0.95, "APG": 0.75, "RPG": 1.4, "PPG_allowed": 1.0},
        }
        
        weight = position_weights.get(position, {}).get(stat, 1.0)
        
        return base_stat * weight

    def _compute_team_stats(self):
        """Compute team season statistics."""
        self.team_season_stats = {}
        for team in pd.concat([self.games_df["home_team"], self.games_df["away_team"]]).unique():
            home_games = self.games_df[self.games_df["home_team"] == team]
            away_games = self.games_df[self.games_df["away_team"] == team]
            
            total_games = len(home_games) + len(away_games)
            if total_games == 0:
                continue
            
            # Calculate actual stats from game data
            ppg = (home_games["home_score"].sum() + away_games["away_score"].sum()) / total_games
            ppg_allowed = (home_games["away_score"].sum() + away_games["home_score"].sum()) / total_games
            
            # Estimate other stats based on league averages scaled to team performance
            performance_factor = ppg / 110.0  # Scale based on scoring vs league avg
            
            self.team_season_stats[team] = {
                "PPG": ppg,
                "PPG_allowed": ppg_allowed,
                "RPG": 45 * performance_factor,
                "APG": 27 * performance_factor,
                "BPG": 5 * (ppg_allowed / 110.0),  # Better defense = more blocks
                "SPG": 7 * (ppg_allowed / 110.0),  # Better defense = more steals
            }
            logger.debug(f"{team}: PPG={ppg:.1f}, PPG_allowed={ppg_allowed:.1f}")

    def compute_offensive_matchup(self, home_team: str, away_team: str,
                                  reference_date: pd.Timestamp = None) -> Dict:
        """
        Compute offensive advantages per position.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            reference_date: As of this date
            
        Returns:
            {position: score, "bench": score, "overall": score}
            Positive = home advantage, Negative = away advantage
        """
        # Ensure team stats computed
        if self.team_season_stats is None:
            self._compute_team_stats()
        
        result = {}
        overall_scores = []
        
        for pos in POSITIONS:
            home_ppg = self.get_position_stat_avg(home_team, pos, "PPG", reference_date)
            away_ppg = self.get_position_stat_avg(away_team, pos, "PPG", reference_date)
            
            # Calculate as percentage difference, then scale to -5 to +5
            # If both teams score ~110, diff is small. If one scores 120 vs 100, that's 20% edge
            if away_ppg > 0:
                pct_diff = (home_ppg - away_ppg) / away_ppg * 100  # percentage points
                matchup_score = (pct_diff / 10.0)  # Scale: 10% = 1 point on the scale
            else:
                matchup_score = 0
            
            matchup_score = max(-5, min(5, matchup_score))  # Clamp to -5 to 5
            
            result[pos] = round(matchup_score, 2)
            overall_scores.append(matchup_score)
            logger.debug(f"{pos}: {home_team}={home_ppg:.1f} vs {away_team}={away_ppg:.1f}, score={matchup_score:.2f}")
        
        # Bench deep: estimate from team PPG totals
        home_bench_ppg = self.get_position_stat_avg(home_team, "PG", "PPG") * 0.3
        away_bench_ppg = self.get_position_stat_avg(away_team, "PG", "PPG") * 0.3
        if away_bench_ppg > 0:
            pct_diff = (home_bench_ppg - away_bench_ppg) / away_bench_ppg * 100
            bench_score = (pct_diff / 10.0)
        else:
            bench_score = 0
        bench_score = max(-5, min(5, bench_score))
        
        result["bench"] = round(bench_score, 2)
        overall_scores.append(bench_score * 0.5)  # Bench weighted less
        
        result["overall"] = round(np.mean(overall_scores), 2)
        logger.debug(f"Offensive overall: {result['overall']}")
        
        return result

    def compute_defensive_matchup(self, home_team: str, away_team: str,
                                 reference_date: pd.Timestamp = None) -> Dict:
        """
        Compute defensive vulnerabilities per position.
        
        Args:
            home_team: Home team
            away_team: Away team
            reference_date: As of this date
            
        Returns:
            {position: score, "bench": score, "overall": score}
            Positive = home defense is strong (away scores less)
            Negative = away defense is strong (home scores less)
        """
        # Ensure team stats computed
        if self.team_season_stats is None:
            self._compute_team_stats()
        
        result = {}
        overall_scores = []
        
        for pos in POSITIONS:
            # Home defense (measured by opponent PPG they allow)
            home_ppg_allowed = self.get_position_stat_avg(home_team, pos, "PPG_allowed", reference_date)
            # Away defense
            away_ppg_allowed = self.get_position_stat_avg(away_team, pos, "PPG_allowed", reference_date)
            
            # Defense advantage: if team allows LESS PPG, they have better defense
            # Frame it as: positive = home defense better (away can't score)
            if away_ppg_allowed > 0:
                pct_diff = (away_ppg_allowed - home_ppg_allowed) / away_ppg_allowed * 100
                matchup_score = (pct_diff / 10.0)
            else:
                matchup_score = 0
            
            matchup_score = max(-5, min(5, matchup_score))
            
            result[pos] = round(matchup_score, 2)
            overall_scores.append(matchup_score)
            logger.debug(f"{pos} Defense: {home_team} allows {home_ppg_allowed:.1f}, {away_team} allows {away_ppg_allowed:.1f}, score={matchup_score:.2f}")
        
        # Bench defensive depth
        home_bench_defense = self.team_season_stats.get(home_team, {}).get("PPG_allowed", 110) * 0.3
        away_bench_defense = self.team_season_stats.get(away_team, {}).get("PPG_allowed", 110) * 0.3
        if away_bench_defense > 0:
            pct_diff = (away_bench_defense - home_bench_defense) / away_bench_defense * 100
            bench_score = (pct_diff / 10.0)
        else:
            bench_score = 0
        bench_score = max(-5, min(5, bench_score))
        
        result["bench"] = round(bench_score, 2)
        overall_scores.append(bench_score * 0.5)
        
        result["overall"] = round(np.mean(overall_scores), 2)
        logger.debug(f"Defensive overall: {result['overall']}")
        
        return result

    def build_full_matchup(self, home_team: str, away_team: str,
                          reference_date: pd.Timestamp = None) -> Dict:
        """
        Build complete matchup index (offensive + defensive + combined).
        
        Args:
            home_team: Home team
            away_team: Away team
            reference_date: As of this date
            
        Returns:
            {
                'home_team': str,
                'away_team': str,
                'date': str,
                'offensive': {position: score, 'overall': score},
                'defensive': {position: score, 'overall': score},
                'combined_score': float,
                'matchup_advantage': str (home/away/neutral)
            }
        """
        offensive = self.compute_offensive_matchup(home_team, away_team, reference_date)
        defensive = self.compute_defensive_matchup(home_team, away_team, reference_date)
        
        # Combined score: average of offensive and defensive, weighted
        combined = (offensive["overall"] * 0.6 + defensive["overall"] * 0.4)
        combined = round(combined, 2)
        
        if combined > 1.0:
            advantage = "home"
        elif combined < -1.0:
            advantage = "away"
        else:
            advantage = "neutral"
        
        return {
            "home_team": home_team,
            "away_team": away_team,
            "date": str(reference_date.date()) if reference_date else "unknown",
            "offensive": offensive,
            "defensive": defensive,
            "combined_score": combined,
            "matchup_advantage": advantage,
        }

    def format_matchup_report(self, matchup_data: Dict) -> str:
        """Format matchup as readable report."""
        report = f"""
╔════════════════════════════════════════════════════════════════════╗
║                    MATCHUP INDEX ANALYSIS                          ║
╚════════════════════════════════════════════════════════════════════╝

Game: {matchup_data['home_team']:20s} vs {matchup_data['away_team']:20s}
Date: {matchup_data['date']}

═══════════════════════════════════════════════════════════════════════

OFFENSIVE BREAKDOWN (Scoring Ability)
──────────────────────────────────────
"""
        
        for pos in POSITIONS:
            score = matchup_data["offensive"][pos]
            bar = "█" * int(abs(score) * 2) if score >= 0 else "░" * int(abs(score) * 2)
            direction = "→ HOME" if score > 0 else "← AWAY" if score < 0 else "EVEN"
            report += f"  {POSITION_NAMES[pos]:20s} [{score:+5.2f}]  {direction}\n"
        
        report += f"\n  Bench Depth         [{matchup_data['offensive']['bench']:+5.2f}]\n"
        report += f"  ──────────────────────────────────\n"
        report += f"  Overall Offensive   [{matchup_data['offensive']['overall']:+5.2f}]  "
        report += "HOME EDGE\n" if matchup_data['offensive']['overall'] > 0 else "AWAY EDGE\n"
        
        report += f"""
═══════════════════════════════════════════════════════════════════════

DEFENSIVE BREAKDOWN (Defense Quality)
─────────────────────────────────────
"""
        
        for pos in POSITIONS:
            score = matchup_data["defensive"][pos]
            direction = "← HOME STRONG" if score > 0 else "AWAY STRONG →" if score < 0 else "EVEN"
            report += f"  {POSITION_NAMES[pos]:20s} [{score:+5.2f}]  {direction}\n"
        
        report += f"\n  Bench Defense       [{matchup_data['defensive']['bench']:+5.2f}]\n"
        report += f"  ──────────────────────────────────\n"
        report += f"  Overall Defense     [{matchup_data['defensive']['overall']:+5.2f}]  "
        report += "HOME FAVORED\n" if matchup_data['defensive']['overall'] > 0 else "AWAY FAVORED\n"
        
        report += f"""
═══════════════════════════════════════════════════════════════════════

COMBINED MATCHUP INDEX
──────────────────────
Combined Score:     {matchup_data['combined_score']:+.2f}
Matchup Advantage:  {matchup_data['matchup_advantage'].upper()}

Interpretation: Score ranges from -5 (away heavily favored) to +5 (home heavily favored)
─────────────────────────────────────────────────────────────────────────────────────
"""
        
        return report


def main():
    """Demo matchup index."""
    # Load historical data
    games_df = pd.read_csv("data/processed/historical_games.csv")
    games_df["game_date"] = pd.to_datetime(games_df["game_date"])
    
    builder = MatchupIndexBuilder(games_df)
    
    # Example matchups - Use FULL team names from the data
    matchups = [
        ("Boston Celtics", "Los Angeles Lakers"),
        ("Golden State Warriors", "Denver Nuggets"),
        ("Miami Heat", "New York Knicks"),
    ]
    
    for home, away in matchups:
        matchup = builder.build_full_matchup(home, away)
        print(builder.format_matchup_report(matchup))
        print("\n")


if __name__ == "__main__":
    main()
