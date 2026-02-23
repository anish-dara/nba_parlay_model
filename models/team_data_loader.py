"""
Load collected data and build TeamFactors for tier-based predictions.

Reads from CSV files created by data collectors and constructs
TeamFactors objects for the tier-based predictor.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional
import logging

from models.tier_based_predictor import TeamFactors, Tier

logger = logging.getLogger(__name__)


class TeamDataLoader:
    """Load and aggregate team data from multiple sources"""
    
    def __init__(self, data_dir: str = "data/processed"):
        self.data_dir = Path(data_dir)
        self.injury_dir = Path("data/injury_reports")
        
        # Cache loaded data
        self._advanced_stats = None
        self._shooting_stats = None
        self._clutch_stats = None
        self._last_10 = None
        self._last_5 = None
        self._momentum = None
        self._injuries = None
        self._injury_impact = None
        self._schedule = None
    
    def load_all_data(self):
        """Load all CSV files into memory"""
        logger.info("Loading team data from CSV files...")
        
        try:
            self._advanced_stats = pd.read_csv(self.data_dir / 'team_advanced_stats.csv')
            logger.info(f"✓ Loaded advanced stats for {len(self._advanced_stats)} teams")
        except Exception as e:
            logger.warning(f"Could not load advanced stats: {e}")
            self._advanced_stats = pd.DataFrame()
        
        try:
            self._shooting_stats = pd.read_csv(self.data_dir / 'team_shooting_stats.csv')
            logger.info(f"✓ Loaded shooting stats for {len(self._shooting_stats)} teams")
        except Exception as e:
            logger.warning(f"Could not load shooting stats: {e}")
            self._shooting_stats = pd.DataFrame()
        
        try:
            self._clutch_stats = pd.read_csv(self.data_dir / 'team_clutch_stats.csv')
            logger.info(f"✓ Loaded clutch stats for {len(self._clutch_stats)} teams")
        except Exception as e:
            logger.warning(f"Could not load clutch stats: {e}")
            self._clutch_stats = pd.DataFrame()
        
        try:
            self._last_10 = pd.read_csv(self.data_dir / 'team_last_10_games.csv')
            logger.info(f"✓ Loaded last 10 games for {len(self._last_10)} teams")
        except Exception as e:
            logger.warning(f"Could not load last 10 games: {e}")
            self._last_10 = pd.DataFrame()
        
        try:
            self._last_5 = pd.read_csv(self.data_dir / 'team_last_5_games.csv')
            logger.info(f"✓ Loaded last 5 games for {len(self._last_5)} teams")
        except Exception as e:
            logger.warning(f"Could not load last 5 games: {e}")
            self._last_5 = pd.DataFrame()
        
        try:
            self._momentum = pd.read_csv(self.data_dir / 'team_momentum.csv')
            logger.info(f"✓ Loaded momentum for {len(self._momentum)} teams")
        except Exception as e:
            logger.warning(f"Could not load momentum: {e}")
            self._momentum = pd.DataFrame()
        
        try:
            self._injuries = pd.read_csv(self.injury_dir / 'current_injuries.csv')
            logger.info(f"✓ Loaded {len(self._injuries)} injuries")
        except Exception as e:
            logger.warning(f"Could not load injuries: {e}")
            self._injuries = pd.DataFrame()
        
        try:
            self._injury_impact = pd.read_csv(self.injury_dir / 'injury_impact.csv')
            logger.info(f"✓ Loaded injury impact for {len(self._injury_impact)} teams")
        except Exception as e:
            logger.warning(f"Could not load injury impact: {e}")
            self._injury_impact = pd.DataFrame()
    
    def _determine_tier(self, win_pct: float, net_rating: float) -> Tier:
        """Determine team tier based on win% and net rating"""
        # S Tier: Elite (top 3-5 teams)
        if win_pct >= 0.650 and net_rating >= 6.0:
            return Tier.S
        # A Tier: Contenders
        elif win_pct >= 0.550 and net_rating >= 2.0:
            return Tier.A
        # B Tier: Playoff teams
        elif win_pct >= 0.450 and net_rating >= -2.0:
            return Tier.B
        # C Tier: Fringe/lottery
        elif win_pct >= 0.350:
            return Tier.C
        # D Tier: Tanking
        else:
            return Tier.D
    
    def get_team_factors(self, team_name: str, is_home: bool = True, 
                        opponent: Optional[str] = None) -> TeamFactors:
        """
        Build TeamFactors for a team from loaded data
        
        Args:
            team_name: Team name (must match CSV data)
            is_home: Whether team is playing at home
            opponent: Opponent team name (for matchup-specific factors)
            
        Returns:
            TeamFactors object with all available data
        """
        if self._advanced_stats is None:
            self.load_all_data()
        
        factors = TeamFactors()
        
        # Advanced stats
        if not self._advanced_stats.empty:
            team_adv = self._advanced_stats[self._advanced_stats['team_name'] == team_name]
            if not team_adv.empty:
                row = team_adv.iloc[0]
                factors.offensive_rating = float(row.get('off_rating', 110.0))
                factors.defensive_rating = float(row.get('def_rating', 110.0))
                factors.net_rating = float(row.get('net_rating', 0.0))
                factors.pace = float(row.get('pace', 100.0))
                factors.turnover_rate = float(row.get('tov_pct', 14.0))
                factors.rebound_rate = float(row.get('oreb_pct', 50.0) + row.get('dreb_pct', 50.0)) / 2
                
                # Determine tier
                win_pct = float(row.get('win_pct', 0.500))
                factors.overall_tier = self._determine_tier(win_pct, factors.net_rating)
        
        # Shooting stats
        if not self._shooting_stats.empty:
            team_shoot = self._shooting_stats[self._shooting_stats['team_name'] == team_name]
            if not team_shoot.empty:
                row = team_shoot.iloc[0]
                factors.three_point_pct = float(row.get('fg3_pct', 0.35))
                # Estimate defense from opponent scoring
                factors.three_point_defense = 0.36  # League average default
        
        # Last 10 games
        if not self._last_10.empty:
            team_l10 = self._last_10[self._last_10['team_name'] == team_name]
            if not team_l10.empty:
                row = team_l10.iloc[0]
                wins = int(row.get('last_10_wins', 5))
                losses = int(row.get('last_10_losses', 5))
                factors.last_10_record = (wins, losses)
        
        # Last 5 games
        if not self._last_5.empty:
            team_l5 = self._last_5[self._last_5['team_name'] == team_name]
            if not team_l5.empty:
                row = team_l5.iloc[0]
                wins = int(row.get('last_5_wins', 2))
                losses = int(row.get('last_5_losses', 3))
                factors.last_5_record = (wins, losses)
        
        # Momentum
        if not self._momentum.empty:
            team_mom = self._momentum[self._momentum['team'] == team_name]
            if not team_mom.empty:
                row = team_mom.iloc[0]
                factors.momentum_score = float(row.get('momentum_score', 0.0))
                factors.recent_point_diff = float(row.get('recent_point_diff', 0.0))
        
        # Injuries - FIXED to properly account for all injury statuses
        # SUPERSTAR IMPACT: Losing a star should be DEVASTATING
        if not self._injury_impact.empty:
            team_inj = self._injury_impact[self._injury_impact['team'] == team_name]
            if not team_inj.empty:
                row = team_inj.iloc[0]
                # Get actual counts from injury impact
                factors.key_players_out = int(row.get('key_players_out', 0))
                factors.injury_severity_score = float(row.get('severity_score', 0.0))
                # Calculate minutes lost based on severity (0-80% max for catastrophic injuries)
                factors.minutes_lost_pct = min(factors.injury_severity_score / 25, 0.80)
        else:
            # If no injury impact data, check raw injuries
            if not self._injuries.empty:
                team_injuries = self._injuries[self._injuries['team'] == team_name]
                if not team_injuries.empty:
                    # Count Out/Out For Season as key players
                    out_statuses = ['Out', 'OUT', 'Out For Season', 'Out Indefinitely']
                    factors.key_players_out = len(team_injuries[team_injuries['status'].isin(out_statuses)])
                    
                    # Calculate severity manually - MUCH HIGHER WEIGHTS
                    # Assume any "Out" player is important (we don't have usage data)
                    severity = 0
                    for _, inj in team_injuries.iterrows():
                        status = inj.get('status', '')
                        # SUPERSTAR WEIGHTS (assume Out = important player)
                        if status in ['Out', 'OUT']:
                            severity += 8.0  # Was 3.0 - assume star player
                        elif status in ['Out For Season', 'Out Indefinitely']:
                            severity += 12.0  # Was 5.0 - franchise player gone
                        elif status in ['Doubtful']:
                            severity += 4.0  # Was 2.0
                        elif status in ['Questionable']:
                            severity += 2.5  # Was 1.5
                        elif status in ['Day-To-Day']:
                            severity += 1.5  # Was 1.0
                    
                    factors.injury_severity_score = severity
                    factors.minutes_lost_pct = min(severity / 25, 0.80)
        
        # Clutch stats
        if not self._clutch_stats.empty:
            team_clutch = self._clutch_stats[self._clutch_stats['team_name'] == team_name]
            if not team_clutch.empty:
                row = team_clutch.iloc[0]
                wins = int(row.get('clutch_wins', 10))
                losses = int(row.get('clutch_losses', 10))
                factors.clutch_record = (wins, losses)
        
        # Home/Away records (estimate from overall record)
        if not self._advanced_stats.empty:
            team_adv = self._advanced_stats[self._advanced_stats['team_name'] == team_name]
            if not team_adv.empty:
                row = team_adv.iloc[0]
                total_wins = int(row.get('wins', 20))
                total_losses = int(row.get('losses', 20))
                
                # Estimate home/away split (home teams typically win ~60% of their home games)
                home_wins = int(total_wins * 0.6)
                home_losses = int(total_losses * 0.4)
                away_wins = total_wins - home_wins
                away_losses = total_losses - home_losses
                
                factors.home_record = (home_wins, home_losses)
                factors.away_record = (away_wins, away_losses)
                
                # Point differentials
                factors.home_point_diff = factors.net_rating * 1.2  # Home boost
                factors.away_point_diff = factors.net_rating * 0.8  # Away penalty
        
        # Schedule factors (defaults - would need game-specific data)
        factors.days_rest = 1
        factors.back_to_back = False
        factors.games_in_last_7 = 3
        factors.travel_distance = 0.0
        
        # Coaching (defaults - would need manual data)
        factors.coach_win_pct = 0.500
        
        # ATS (defaults - would need scraping)
        factors.ats_record = (40, 40)
        
        # Situational (estimate from standings)
        if not self._advanced_stats.empty:
            team_adv = self._advanced_stats[self._advanced_stats['team_name'] == team_name]
            if not team_adv.empty:
                # Estimate playoff position from win%
                all_teams = self._advanced_stats.sort_values('win_pct', ascending=False)
                position = all_teams[all_teams['team_name'] == team_name].index[0] + 1
                factors.playoff_position = int(position)
        
        factors.motivation_factor = 0.0  # Neutral default
        
        return factors
    
    def get_available_teams(self) -> list:
        """Get list of teams with available data"""
        if self._advanced_stats is None:
            self.load_all_data()
        
        if not self._advanced_stats.empty:
            return sorted(self._advanced_stats['team_name'].unique().tolist())
        return []


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    loader = TeamDataLoader()
    loader.load_all_data()
    
    teams = loader.get_available_teams()
    print(f"\n✓ Loaded data for {len(teams)} teams")
    
    if teams:
        # Test with first team
        test_team = teams[0]
        factors = loader.get_team_factors(test_team)
        
        print(f"\nSample TeamFactors for {test_team}:")
        print(f"  Tier: {factors.overall_tier.name}")
        print(f"  Off Rating: {factors.offensive_rating:.1f}")
        print(f"  Def Rating: {factors.defensive_rating:.1f}")
        print(f"  Net Rating: {factors.net_rating:.1f}")
        print(f"  Last 10: {factors.last_10_record}")
        print(f"  Momentum: {factors.momentum_score:.1f}")
        print(f"  Injuries: {factors.key_players_out} key players out")
