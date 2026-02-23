"""Helper utilities for data handling and calculations."""

import numpy as np
from typing import List, Tuple


def calculate_parlay_odds(individual_odds: List[float]) -> float:
    """
    Calculate combined parlay odds from individual game odds.
    
    Args:
        individual_odds: List of decimal odds for each leg
        
    Returns:
        Combined parlay decimal odds
    """
    if not individual_odds:
        raise ValueError("individual_odds cannot be empty")
    if any(odd <= 0 for odd in individual_odds):
        raise ValueError("All odds must be positive")
    return float(np.prod(individual_odds))


def calculate_parlay_probability(individual_probs: List[float]) -> float:
    """
    Calculate the probability of a parlay winning from individual game probabilities.
    
    Args:
        individual_probs: List of win probabilities for each leg (0-1)
        
    Returns:
        Overall parlay win probability (0-1)
    """
    if not individual_probs:
        raise ValueError("individual_probs cannot be empty")
    return float(np.prod(individual_probs))
 

def calculate_expected_value(probability: float, odds: float, wager: float = 100) -> float:
    """
    Calculate expected value of a bet.
    
    Args:
        probability: Probability of winning (0-1)
        odds: Decimal odds
        wager: Wager amount (default 100) 
        
    Returns:
        Expected value in currency units
    """
    if not 0 <= probability <= 1:
        raise ValueError("Probability must be between 0 and 1")
    if odds <= 0:
        raise ValueError("Odds must be positive")
    return wager * (probability * (odds - 1) - (1 - probability))


def american_to_decimal(american_odds: float) -> float:
    """Convert American odds to decimal odds."""
    if american_odds > 0:
        return (american_odds / 100) + 1
    else:
        return (100 / abs(american_odds)) + 1


def decimal_to_american(decimal_odds: float) -> float:
    """Convert decimal odds to American odds."""
    if decimal_odds >= 2:
        return (decimal_odds - 1) * 100
    else:
        return -100 / (decimal_odds - 1)
