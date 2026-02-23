"""Combine game predictions and player prop predictions into parlay recommendations."""
from __future__ import annotations

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
import logging
from itertools import combinations

LOGGER = logging.getLogger(__name__)


class ParlayBuilder:
    """Build and rank parlay combinations based on predicted probabilities and odds."""
    
    def __init__(self, min_ev_threshold: float = 0.05, min_odds: float = 1.5, max_legs: int = 5):
        """
        Args:
            min_ev_threshold: Minimum expected value % to recommend (e.g., 0.05 = 5%)
            min_odds: Minimum individual game odds to include
            max_legs: Maximum parlay legs to consider
        """
        self.min_ev = min_ev_threshold
        self.min_odds = min_odds
        self.max_legs = max_legs
    
    def calculate_parlay_ev(self, 
                           predicted_probs: List[float], 
                           odds_decimal: List[float],
                           wager: float = 100) -> Dict[str, float]:
        """
        Calculate EV for a parlay.
        
        Args:
            predicted_probs: Predicted win probabilities [0-1] for each leg
            odds_decimal: Decimal odds for each leg
            wager: Wager amount
            
        Returns:
            {ev_pct, implied_prob_market, actual_prob_model, odds_parlay, payout}
        """
        # Parlay probability (independent events)
        actual_prob = np.prod(predicted_probs)
        
        # Market implied probability (normalized for book margin)
        implied_probs = 1.0 / np.array(odds_decimal)
        market_prob = np.prod(implied_probs)
        
        # Parlay odds
        parlay_odds = np.prod(odds_decimal)
        
        # EV% = (P(win) * Odds) - 1
        ev_pct = (actual_prob * parlay_odds) - 1
        
        # Payout
        payout = wager * parlay_odds
        expected_return = wager * (actual_prob * parlay_odds - (1 - actual_prob))
        
        return {
            "ev_pct": ev_pct,
            "ev_dollars": expected_return,
            "implied_prob_market": float(market_prob),
            "actual_prob_model": float(actual_prob),
            "parlay_odds": float(parlay_odds),
            "payout": payout,
            "kelly_fraction": (actual_prob * parlay_odds - 1) / (parlay_odds - 1) if parlay_odds > 1 else 0
        }
    
    def build_game_parlays(self,
                          games: pd.DataFrame,
                          predicted_probs: np.ndarray,
                          odds_decimal: List[float],
                          team_names: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
        """
        Generate all possible game parlays with +EV.
        
        Args:
            games: Game dataframe
            predicted_probs: Predicted home win probabilities
            odds_decimal: Decimal odds for home team
            team_names: List of (home_team, away_team) tuples
            
        Returns:
            List of recommended parlays sorted by EV
        """
        recommendations = []
        
        # Filter valid games (odds >= min_odds)
        valid_indices = [i for i, o in enumerate(odds_decimal) if o >= self.min_odds]
        
        if len(valid_indices) < 2:
            LOGGER.warning("Not enough valid games for parlays")
            return []
        
        # Generate combinations of 2 to max_legs
        for num_legs in range(2, min(self.max_legs + 1, len(valid_indices) + 1)):
            for leg_combo in combinations(valid_indices, num_legs):
                probs = [predicted_probs[i] for i in leg_combo]
                odds = [odds_decimal[i] for i in leg_combo]
                
                ev_info = self.calculate_parlay_ev(probs, odds)
                
                # Filter by EV threshold
                if ev_info["ev_pct"] < self.min_ev:
                    continue
                
                parlay_desc = " & ".join([
                    f"{team_names[i][0]} ML" for i in leg_combo
                ])
                
                recommendations.append({
                    "parlay": parlay_desc,
                    "legs": num_legs,
                    "games": [leg_combo],
                    **ev_info
                })
        
        # Sort by EV (descending)
        recommendations.sort(key=lambda x: x["ev_pct"], reverse=True)
        
        LOGGER.info(f"Generated {len(recommendations)} +EV parlays")
        return recommendations
    
    def build_prop_parlays(self,
                          players: List[str],
                          props: List[str],  # e.g., ["points_over_25", "assists_over_8"]
                          predicted_probs: List[float],
                          odds_decimal: List[float]) -> List[Dict[str, Any]]:
        """
        Generate player prop parlays.
        
        Args:
            players: Player names
            props: Prop descriptions
            predicted_probs: Predicted O outcomes
            odds_decimal: Decimal odds
            
        Returns:
            List of recommended prop parlays
        """
        recommendations = []
        
        valid_indices = [i for i, o in enumerate(odds_decimal) if o >= self.min_odds]
        
        for num_legs in range(2, min(self.max_legs + 1, len(valid_indices) + 1)):
            for leg_combo in combinations(valid_indices, num_legs):
                probs = [predicted_probs[i] for i in leg_combo]
                odds = [odds_decimal[i] for i in leg_combo]
                
                ev_info = self.calculate_parlay_ev(probs, odds)
                
                if ev_info["ev_pct"] < self.min_ev:
                    continue
                
                prop_desc = " & ".join([props[i] for i in leg_combo])
                
                recommendations.append({
                    "parlay": prop_desc,
                    "legs": num_legs,
                    "players": [players[i] for i in leg_combo],
                    **ev_info
                })
        
        recommendations.sort(key=lambda x: x["ev_pct"], reverse=True)
        return recommendations
    
    def build_mixed_parlays(self,
                           game_probs: List[float],
                           game_odds: List[float],
                           game_names: List[str],
                           prop_probs: List[float],
                           prop_odds: List[float],
                           prop_names: List[str]) -> List[Dict[str, Any]]:
        """
        Generate mixed game + prop parlays (most flexible).
        
        Args:
            game_probs, game_odds, game_names: Game predictions
            prop_probs, prop_odds, prop_names: Prop predictions
            
        Returns:
            List of recommended mixed parlays
        """
        recommendations = []
        
        all_probs = game_probs + prop_probs
        all_odds = game_odds + prop_odds
        all_names = game_names + prop_names
        
        valid_indices = [i for i, o in enumerate(all_odds) if o >= self.min_odds]
        
        for num_legs in range(2, min(self.max_legs + 1, len(valid_indices) + 1)):
            for leg_combo in combinations(valid_indices, num_legs):
                probs = [all_probs[i] for i in leg_combo]
                odds = [all_odds[i] for i in leg_combo]
                
                ev_info = self.calculate_parlay_ev(probs, odds)
                
                if ev_info["ev_pct"] < self.min_ev:
                    continue
                
                mixed_desc = " & ".join([all_names[i] for i in leg_combo])
                
                recommendations.append({
                    "parlay": mixed_desc,
                    "legs": num_legs,
                    **ev_info
                })
        
        recommendations.sort(key=lambda x: x["ev_pct"], reverse=True)
        return recommendations[:10]  # Top 10
