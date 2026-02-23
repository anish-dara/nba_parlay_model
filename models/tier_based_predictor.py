"""
Comprehensive tier-based NBA game prediction model with 50+ factors.

This model uses a weighted tier system across multiple categories:
- Team Quality (S/A/B/C/D tiers)
- Recent Form & Momentum
- Injuries & Availability
- Rest & Schedule
- Matchup-Specific Factors
- Situational Context
"""

from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Tier(Enum):
    """Team tier classification"""
    S = 5  # Elite (top 3-5 teams)
    A = 4  # Contenders (top 10)
    B = 3  # Playoff teams
    C = 2  # Fringe/lottery
    D = 1  # Tanking/rebuilding


@dataclass
class TeamFactors:
    """All factors for a single team"""
    # TIER 1: Core Team Quality (Weight: 30%)
    overall_tier: Tier = Tier.C
    offensive_rating: float = 110.0  # Points per 100 possessions
    defensive_rating: float = 110.0
    net_rating: float = 0.0
    
    # TIER 2: Recent Performance (Weight: 20%)
    last_10_record: Tuple[int, int] = (5, 5)
    last_5_record: Tuple[int, int] = (2, 3)
    momentum_score: float = 0.0  # -10 to +10
    recent_point_diff: float = 0.0
    
    # TIER 3: Injuries & Availability (Weight: 15%)
    key_players_out: int = 0  # Number of starters/key rotation out
    injury_severity_score: float = 0.0  # 0-10 scale
    minutes_lost_pct: float = 0.0  # % of total minutes unavailable
    
    # TIER 4: Rest & Schedule (Weight: 10%)
    days_rest: int = 1
    back_to_back: bool = False
    games_in_last_7: int = 3
    travel_distance: float = 0.0  # Miles traveled
    
    # TIER 5: Home/Away Splits (Weight: 8%)
    home_record: Tuple[int, int] = (20, 20)
    away_record: Tuple[int, int] = (20, 20)
    home_point_diff: float = 0.0
    away_point_diff: float = 0.0
    
    # TIER 6: Matchup-Specific (Weight: 7%)
    pace: float = 100.0  # Possessions per game
    three_point_pct: float = 0.35
    three_point_defense: float = 0.35
    turnover_rate: float = 14.0
    rebound_rate: float = 50.0
    
    # TIER 7: Coaching & Intangibles (Weight: 5%)
    coach_win_pct: float = 0.500
    clutch_record: Tuple[int, int] = (10, 10)  # Games within 5 pts in last 5 min
    ats_record: Tuple[int, int] = (40, 40)  # Against the spread
    
    # TIER 8: Situational (Weight: 5%)
    playoff_position: int = 8  # Current seed (1-15)
    games_remaining: int = 82
    motivation_factor: float = 0.0  # -5 to +5 (rivalry, revenge, etc.)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for feature engineering"""
        return {
            'tier_value': self.overall_tier.value,
            'off_rating': self.offensive_rating,
            'def_rating': self.defensive_rating,
            'net_rating': self.net_rating,
            'last_10_wp': self.last_10_record[0] / 10 if sum(self.last_10_record) > 0 else 0.5,
            'last_5_wp': self.last_5_record[0] / 5 if sum(self.last_5_record) > 0 else 0.5,
            'momentum': self.momentum_score,
            'recent_pt_diff': self.recent_point_diff,
            'injury_impact': self.injury_severity_score,
            'minutes_lost': self.minutes_lost_pct,
            'days_rest': self.days_rest,
            'b2b': 1 if self.back_to_back else 0,
            'games_last_7': self.games_in_last_7,
            'travel_miles': self.travel_distance,
            'home_wp': self.home_record[0] / sum(self.home_record) if sum(self.home_record) > 0 else 0.5,
            'away_wp': self.away_record[0] / sum(self.away_record) if sum(self.away_record) > 0 else 0.5,
            'home_pt_diff': self.home_point_diff,
            'away_pt_diff': self.away_point_diff,
            'pace': self.pace,
            'three_pct': self.three_point_pct,
            'three_def': self.three_point_defense,
            'tov_rate': self.turnover_rate,
            'reb_rate': self.rebound_rate,
            'coach_wp': self.coach_win_pct,
            'clutch_wp': self.clutch_record[0] / sum(self.clutch_record) if sum(self.clutch_record) > 0 else 0.5,
            'ats_wp': self.ats_record[0] / sum(self.ats_record) if sum(self.ats_record) > 0 else 0.5,
            'seed': self.playoff_position,
            'motivation': self.motivation_factor,
        }


class TierBasedPredictor:
    """Advanced tier-based prediction model"""
    
    # Category weights (must sum to 1.0)
    # Injuries MASSIVELY increased - losing stars is devastating
    WEIGHTS = {
        'team_quality': 0.25,
        'recent_form': 0.15,
        'injuries': 0.30,  # INCREASED from 0.15 - injuries are HUGE
        'rest_schedule': 0.10,
        'home_away': 0.08,
        'matchup': 0.05,
        'coaching': 0.04,
        'situational': 0.03,
    }
    
    # Home court advantage base
    HOME_COURT_BASE = 0.035  # 3.5% base advantage
    
    def __init__(self):
        self.team_factors_cache: Dict[str, TeamFactors] = {}
    
    def calculate_team_quality_score(self, factors: TeamFactors) -> float:
        """
        Calculate team quality component (0-1 scale)
        Considers: tier, ratings, net rating
        """
        # Tier contribution (40% of this category)
        tier_score = factors.overall_tier.value / 5.0
        
        # Net rating contribution (60% of this category)
        # NBA net ratings typically range from -10 to +10
        net_rating_normalized = (factors.net_rating + 10) / 20
        net_rating_normalized = max(0, min(1, net_rating_normalized))
        
        return 0.4 * tier_score + 0.6 * net_rating_normalized
    
    def calculate_recent_form_score(self, factors: TeamFactors) -> float:
        """
        Calculate recent form component (0-1 scale)
        Considers: L10, L5, momentum, recent point differential
        """
        l10_wp = factors.last_10_record[0] / 10 if sum(factors.last_10_record) > 0 else 0.5
        l5_wp = factors.last_5_record[0] / 5 if sum(factors.last_5_record) > 0 else 0.5
        
        # Weight recent games more heavily
        form_wp = 0.4 * l10_wp + 0.6 * l5_wp
        
        # Momentum score normalized (-10 to +10 → 0 to 1)
        momentum_normalized = (factors.momentum_score + 10) / 20
        
        # Recent point differential normalized (-15 to +15 → 0 to 1)
        pt_diff_normalized = (factors.recent_point_diff + 15) / 30
        pt_diff_normalized = max(0, min(1, pt_diff_normalized))
        
        return 0.5 * form_wp + 0.3 * momentum_normalized + 0.2 * pt_diff_normalized
    
    def calculate_injury_impact(self, factors: TeamFactors) -> float:
        """
        Calculate injury impact (0-1 scale, where 1 = healthy)
        MASSIVELY INCREASED - losing stars is devastating
        
        Examples:
        - 1 superstar out (severity 8-10): ~40-50% impact
        - 2 key players out (severity 12-15): ~60-75% impact  
        - Multiple stars (severity 20+): ~90%+ impact (team is cooked)
        """
        # Penalty for each key player out (MUCH HIGHER)
        # Each star out = ~25-30% penalty
        player_penalty = min(factors.key_players_out * 0.30, 0.90)
        
        # Severity score (0-30 scale now, was 0-10)
        # Superstar out = 8-10 points, role player = 2-3 points
        severity_penalty = min(factors.injury_severity_score / 30, 0.90)
        
        # Minutes lost percentage (direct impact)
        minutes_penalty = factors.minutes_lost_pct * 0.8
        
        # Take the MAXIMUM penalty (not sum) - one superstar out is enough
        total_penalty = max(player_penalty, severity_penalty, minutes_penalty)
        
        return max(0.1, 1 - total_penalty)  # Min 10% (team is destroyed)
    
    def calculate_rest_schedule_score(self, factors: TeamFactors) -> float:
        """
        Calculate rest/schedule component (0-1 scale)
        Considers: days rest, B2B, games in last 7, travel
        """
        # Days rest score (optimal = 2 days)
        if factors.days_rest == 0:
            rest_score = 0.3  # Back to back penalty
        elif factors.days_rest == 1:
            rest_score = 0.7
        elif factors.days_rest == 2:
            rest_score = 1.0
        elif factors.days_rest == 3:
            rest_score = 0.95
        else:
            rest_score = 0.85  # Too much rest can be bad
        
        # Games in last 7 penalty (ideal = 3)
        if factors.games_in_last_7 <= 2:
            schedule_score = 1.0
        elif factors.games_in_last_7 == 3:
            schedule_score = 0.95
        elif factors.games_in_last_7 == 4:
            schedule_score = 0.8
        else:
            schedule_score = 0.6  # Brutal schedule
        
        # Travel penalty (0-3000 miles)
        travel_score = 1 - min(factors.travel_distance / 3000, 0.2)
        
        return 0.5 * rest_score + 0.3 * schedule_score + 0.2 * travel_score
    
    def calculate_home_away_score(self, factors: TeamFactors, is_home: bool) -> float:
        """
        Calculate home/away performance (0-1 scale)
        """
        if is_home:
            wp = factors.home_record[0] / sum(factors.home_record) if sum(factors.home_record) > 0 else 0.5
            pt_diff = factors.home_point_diff
        else:
            wp = factors.away_record[0] / sum(factors.away_record) if sum(factors.away_record) > 0 else 0.5
            pt_diff = factors.away_point_diff
        
        # Point differential normalized (-10 to +10)
        pt_diff_normalized = (pt_diff + 10) / 20
        pt_diff_normalized = max(0, min(1, pt_diff_normalized))
        
        return 0.7 * wp + 0.3 * pt_diff_normalized
    
    def calculate_matchup_score(self, home_factors: TeamFactors, away_factors: TeamFactors) -> float:
        """
        Calculate matchup-specific advantages (0-1 scale for home team)
        Considers: pace, shooting, defense, turnovers, rebounds
        """
        # Pace matchup (teams that control pace have advantage)
        pace_diff = home_factors.pace - away_factors.pace
        pace_score = 0.5 + (pace_diff / 20) * 0.1  # Small impact
        
        # Shooting matchup (offense vs defense)
        home_shooting_advantage = home_factors.three_point_pct - away_factors.three_point_defense
        away_shooting_advantage = away_factors.three_point_pct - home_factors.three_point_defense
        shooting_score = 0.5 + (home_shooting_advantage - away_shooting_advantage) * 2
        
        # Turnover battle
        tov_diff = away_factors.turnover_rate - home_factors.turnover_rate
        tov_score = 0.5 + (tov_diff / 10) * 0.2
        
        # Rebounding battle
        reb_diff = home_factors.rebound_rate - away_factors.rebound_rate
        reb_score = 0.5 + (reb_diff / 10) * 0.2
        
        # Weighted average
        matchup = 0.2 * pace_score + 0.4 * shooting_score + 0.2 * tov_score + 0.2 * reb_score
        return max(0, min(1, matchup))
    
    def calculate_coaching_intangibles(self, factors: TeamFactors) -> float:
        """
        Calculate coaching/intangibles (0-1 scale)
        """
        coach_score = factors.coach_win_pct
        clutch_wp = factors.clutch_record[0] / sum(factors.clutch_record) if sum(factors.clutch_record) > 0 else 0.5
        ats_wp = factors.ats_record[0] / sum(factors.ats_record) if sum(factors.ats_record) > 0 else 0.5
        
        return 0.4 * coach_score + 0.4 * clutch_wp + 0.2 * ats_wp
    
    def calculate_situational_score(self, factors: TeamFactors) -> float:
        """
        Calculate situational factors (0-1 scale)
        """
        # Playoff position (1-15, where 1 is best)
        seed_score = 1 - (factors.playoff_position - 1) / 14
        
        # Motivation normalized (-5 to +5)
        motivation_score = (factors.motivation_factor + 5) / 10
        
        return 0.6 * seed_score + 0.4 * motivation_score
    
    def predict_game(self, home_factors: TeamFactors, away_factors: TeamFactors) -> Dict:
        """
        Predict game outcome using comprehensive tier-based model.
        
        Returns:
            {
                'home_win_probability': float,
                'away_win_probability': float,
                'confidence': float,
                'breakdown': dict with component scores
            }
        """
        # Calculate component scores for each team
        home_scores = {
            'team_quality': self.calculate_team_quality_score(home_factors),
            'recent_form': self.calculate_recent_form_score(home_factors),
            'injuries': self.calculate_injury_impact(home_factors),
            'rest_schedule': self.calculate_rest_schedule_score(home_factors),
            'home_away': self.calculate_home_away_score(home_factors, is_home=True),
            'coaching': self.calculate_coaching_intangibles(home_factors),
            'situational': self.calculate_situational_score(home_factors),
        }
        
        away_scores = {
            'team_quality': self.calculate_team_quality_score(away_factors),
            'recent_form': self.calculate_recent_form_score(away_factors),
            'injuries': self.calculate_injury_impact(away_factors),
            'rest_schedule': self.calculate_rest_schedule_score(away_factors),
            'home_away': self.calculate_home_away_score(away_factors, is_home=False),
            'coaching': self.calculate_coaching_intangibles(away_factors),
            'situational': self.calculate_situational_score(away_factors),
        }
        
        # Matchup score (relative to home team)
        matchup_score = self.calculate_matchup_score(home_factors, away_factors)
        
        # Calculate weighted advantage for home team
        home_advantage = 0.0
        for category, weight in self.WEIGHTS.items():
            if category == 'matchup':
                home_advantage += weight * (matchup_score - 0.5) * 2  # Convert 0-1 to -1 to +1
            else:
                home_advantage += weight * (home_scores[category] - away_scores[category])
        
        # Add home court advantage
        home_advantage += self.HOME_COURT_BASE
        
        # Convert advantage to probability (sigmoid-like function)
        # Advantage ranges roughly -0.5 to +0.5, map to probability
        home_win_prob = 0.5 + home_advantage
        home_win_prob = max(0.01, min(0.99, home_win_prob))
        
        # Confidence based on magnitude of advantage
        confidence = abs(home_win_prob - 0.5) * 2
        
        return {
            'home_win_probability': float(home_win_prob),
            'away_win_probability': float(1 - home_win_prob),
            'confidence': float(confidence),
            'home_advantage': float(home_advantage),
            'breakdown': {
                'home_scores': home_scores,
                'away_scores': away_scores,
                'matchup_score': float(matchup_score),
                'home_court_boost': self.HOME_COURT_BASE,
            }
        }
    
    def format_prediction_report(self, prediction: Dict, home_team: str, away_team: str) -> str:
        """Generate detailed prediction report"""
        report = f"""
╔══════════════════════════════════════════════════════════════════════╗
║                    TIER-BASED PREDICTION ANALYSIS                    ║
╚══════════════════════════════════════════════════════════════════════╝

{home_team} (HOME) vs {away_team} (AWAY)

PREDICTION:
  {home_team:20s} {prediction['home_win_probability']:6.1%} win probability
  {away_team:20s} {prediction['away_win_probability']:6.1%} win probability
  
  Confidence: {prediction['confidence']:5.1%}
  Home Advantage: {prediction['home_advantage']:+.3f}

═══════════════════════════════════════════════════════════════════════

COMPONENT BREAKDOWN:
                          {home_team:^15s}  {away_team:^15s}  Weight
  ─────────────────────────────────────────────────────────────────────
"""
        
        home_scores = prediction['breakdown']['home_scores']
        away_scores = prediction['breakdown']['away_scores']
        
        for category, weight in self.WEIGHTS.items():
            if category != 'matchup':
                h_score = home_scores[category]
                a_score = away_scores[category]
                report += f"  {category.replace('_', ' ').title():20s} {h_score:6.1%}        {a_score:6.1%}      {weight:5.1%}\n"
        
        matchup = prediction['breakdown']['matchup_score']
        report += f"  {'Matchup Edge':20s} {matchup:6.1%}        {1-matchup:6.1%}      {self.WEIGHTS['matchup']:5.1%}\n"
        report += f"  {'Home Court':20s} {self.HOME_COURT_BASE:+6.1%}        {'—':>6s}      {'—':>5s}\n"
        
        report += "\n═══════════════════════════════════════════════════════════════════════\n"
        
        return report


# Example usage
if __name__ == "__main__":
    predictor = TierBasedPredictor()
    
    # Example: Elite home team vs good away team
    celtics = TeamFactors(
        overall_tier=Tier.S,
        offensive_rating=118.5,
        defensive_rating=110.2,
        net_rating=8.3,
        last_10_record=(8, 2),
        last_5_record=(4, 1),
        momentum_score=6.0,
        key_players_out=0,
        days_rest=2,
        home_record=(28, 8),
        away_record=(22, 14),
        pace=98.5,
        three_point_pct=0.378,
        coach_win_pct=0.625,
        playoff_position=1,
    )
    
    lakers = TeamFactors(
        overall_tier=Tier.A,
        offensive_rating=115.0,
        defensive_rating=112.5,
        net_rating=2.5,
        last_10_record=(6, 4),
        last_5_record=(3, 2),
        momentum_score=1.0,
        key_players_out=1,
        injury_severity_score=3.0,
        days_rest=1,
        home_record=(24, 12),
        away_record=(18, 18),
        pace=101.2,
        three_point_pct=0.358,
        coach_win_pct=0.580,
        playoff_position=6,
    )
    
    prediction = predictor.predict_game(celtics, lakers)
    print(predictor.format_prediction_report(prediction, "Boston Celtics", "Los Angeles Lakers"))
