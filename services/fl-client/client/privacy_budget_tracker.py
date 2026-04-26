"""
SecureDx AI — Privacy Budget Tracker

For a 15-year-old:
Privacy is like a battery 🔋. Every time we share information (even with noise),
we use up some battery:
- Start: 100% battery (ε_max = 10.0)
- After 1 FL round: 90% left (spent ε = 1.0)
- After 10 FL rounds: 0% left (spent ε = 10.0) ❌ STOP!

When the battery runs out, we MUST stop learning or patient privacy breaks!

For an interviewer:
Implements DP composition tracking with:
- Sequential composition: ε_total = Σ ε_i (worst case)
- Advanced composition: ε_total = √(2k ln(1/δ')) ε (with amplification)
- Alerts when budget depleted
- Prevents participation if budget exceeded

Why this matters:
- Each FL round consumes privacy budget
- Infinite rounds → zero privacy
- Must track cumulative epsilon across rounds
- Industry standard: ε_total ≤ 10 (strong privacy) or ε_total ≤ 100 (acceptable)

Reference: Dwork & Roth (2014) "The Algorithmic Foundations of Differential Privacy"
"""
import logging
from typing import Dict, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PrivacyBudgetStatus:
    """Current privacy budget status"""
    total_epsilon_spent: float
    total_epsilon_limit: float
    rounds_participated: int
    epsilon_per_round: float
    remaining_rounds: int
    budget_depleted: bool
    last_updated: datetime


class PrivacyBudgetTracker:
    """
    Track cumulative privacy budget across FL rounds.
    
    For a 15-year-old:
    This is the "battery meter" that warns you:
    "⚠️ Only 10% privacy budget left! Stop soon!"
    
    For an interviewer:
    Implements composition theorems for differential privacy:
    
    Basic Composition (conservative):
    If mechanism M_i is ε_i-DP, then:
    Composition M_1, M_2, ..., M_k is (Σ ε_i)-DP
    
    Advanced Composition (tighter bound):
    Composition is (ε', kδ + δ')-DP where:
    ε' = √(2k ln(1/δ')) ε + kε(e^ε - 1)
    
    We use basic composition for simplicity.
    """
    
    def __init__(
        self,
        epsilon_per_round: float = 1.0,
        total_epsilon_limit: float = 10.0,
        storage_path: str = "/var/securedx/privacy_budget.json",
    ):
        """
        Initialize privacy budget tracker.
        
        Args:
            epsilon_per_round: ε spent per FL round
            total_epsilon_limit: Maximum cumulative ε before stopping
            storage_path: Persistent storage for budget state
        
        Industry guidelines:
        - ε ≤ 1.0: Strong privacy (recommended)
        - ε ≤ 10: Acceptable privacy
        - ε > 10: Weak privacy (not recommended)
        
        Total budget examples:
        - Conservative clinic: ε_total = 10 (10 rounds at ε=1.0)
        - Standard clinic: ε_total = 50 (50 rounds at ε=1.0)
        - Research setting: ε_total = 100 (100 rounds at ε=1.0)
        """
        self.epsilon_per_round = epsilon_per_round
        self.total_epsilon_limit = total_epsilon_limit
        self.storage_path = storage_path
        
        # State
        self.total_epsilon_spent = 0.0
        self.rounds_participated = 0
        self.last_updated = datetime.utcnow()
        
        # Load from persistent storage
        self._load_state()
        
        logger.info(
            f"Privacy budget tracker initialized: "
            f"ε_per_round={epsilon_per_round}, "
            f"ε_limit={total_epsilon_limit}, "
            f"ε_spent={self.total_epsilon_spent:.2f}"
        )
    
    def can_participate(self) -> bool:
        """
        Check if clinic can participate in next FL round.
        
        Returns:
            True if budget allows, False if depleted
        
        For a 15-year-old:
        "Do we have enough battery to play another round?"
        
        For an interviewer:
        Conservative check: ε_spent + ε_per_round ≤ ε_limit
        """
        would_spend = self.total_epsilon_spent + self.epsilon_per_round
        can_afford = would_spend <= self.total_epsilon_limit
        
        if not can_afford:
            logger.warning(
                f"Privacy budget depleted! "
                f"ε_spent={self.total_epsilon_spent:.2f}, "
                f"ε_limit={self.total_epsilon_limit:.2f}"
            )
        
        return can_afford
    
    def record_round(self, epsilon_spent: Optional[float] = None) -> None:
        """
        Record completion of FL round.
        
        Args:
            epsilon_spent: Actual ε spent (defaults to epsilon_per_round)
        
        For a 15-year-old:
        "We just played a round. Subtract from battery: 100% → 90%"
        
        For an interviewer:
        Updates cumulative epsilon via basic composition:
        ε_total_new = ε_total_old + ε_i
        """
        if epsilon_spent is None:
            epsilon_spent = self.epsilon_per_round
        
        self.total_epsilon_spent += epsilon_spent
        self.rounds_participated += 1
        self.last_updated = datetime.utcnow()
        
        # Persist state
        self._save_state()
        
        # Log milestone warnings
        utilization = self.total_epsilon_spent / self.total_epsilon_limit
        
        if utilization >= 0.9:
            logger.error(
                f"🔴 CRITICAL: Privacy budget 90% depleted! "
                f"ε={self.total_epsilon_spent:.2f}/{self.total_epsilon_limit:.2f}"
            )
        elif utilization >= 0.75:
            logger.warning(
                f"🟠 WARNING: Privacy budget 75% depleted! "
                f"ε={self.total_epsilon_spent:.2f}/{self.total_epsilon_limit:.2f}"
            )
        elif utilization >= 0.5:
            logger.info(
                f"🟡 NOTICE: Privacy budget 50% depleted. "
                f"ε={self.total_epsilon_spent:.2f}/{self.total_epsilon_limit:.2f}"
            )
        
        logger.info(
            f"FL round {self.rounds_participated} completed. "
            f"ε_spent={epsilon_spent:.2f}, "
            f"ε_total={self.total_epsilon_spent:.2f}/{self.total_epsilon_limit:.2f}"
        )
    
    def get_status(self) -> PrivacyBudgetStatus:
        """
        Get current privacy budget status.
        
        Returns:
            PrivacyBudgetStatus with all metrics
        """
        remaining = self.total_epsilon_limit - self.total_epsilon_spent
        remaining_rounds = int(remaining / self.epsilon_per_round)
        budget_depleted = self.total_epsilon_spent >= self.total_epsilon_limit
        
        return PrivacyBudgetStatus(
            total_epsilon_spent=self.total_epsilon_spent,
            total_epsilon_limit=self.total_epsilon_limit,
            rounds_participated=self.rounds_participated,
            epsilon_per_round=self.epsilon_per_round,
            remaining_rounds=max(0, remaining_rounds),
            budget_depleted=budget_depleted,
            last_updated=self.last_updated,
        )
    
    def reset(self, confirm: bool = False) -> None:
        """
        Reset privacy budget (DANGEROUS - requires confirmation).
        
        For a 15-year-old:
        "Recharge battery to 100%"
        
        But WARNING: This is like time travel! Once privacy is spent,
        it's spent forever. Only reset if:
        - Deploying new model trained from scratch
        - Using completely different dataset
        - After re-identifying and re-consenting all patients
        
        For an interviewer:
        Privacy budget is NOT renewable in the mathematical sense.
        Resetting means:
        - Previous guarantees no longer hold
        - Must treat as new privacy regime
        - Requires governance approval
        """
        if not confirm:
            logger.error(
                "Privacy budget reset requires confirm=True. "
                "This is a security-critical operation."
            )
            return
        
        logger.warning(
            f"🔴 RESETTING PRIVACY BUDGET! "
            f"Previous: ε={self.total_epsilon_spent:.2f}, "
            f"rounds={self.rounds_participated}"
        )
        
        self.total_epsilon_spent = 0.0
        self.rounds_participated = 0
        self.last_updated = datetime.utcnow()
        
        self._save_state()
        
        logger.warning("Privacy budget reset complete. New regime starts now.")
    
    def _save_state(self) -> None:
        """Persist budget state to disk"""
        import json
        
        state = {
            'total_epsilon_spent': self.total_epsilon_spent,
            'rounds_participated': self.rounds_participated,
            'last_updated': self.last_updated.isoformat(),
        }
        
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            logger.error(f"Failed to save privacy budget state: {e}")
    
    def _load_state(self) -> None:
        """Load budget state from disk"""
        import json
        import os
        
        if not os.path.exists(self.storage_path):
            logger.info("No existing privacy budget state found. Starting fresh.")
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                state = json.load(f)
            
            self.total_epsilon_spent = state.get('total_epsilon_spent', 0.0)
            self.rounds_participated = state.get('rounds_participated', 0)
            self.last_updated = datetime.fromisoformat(state.get('last_updated'))
            
            logger.info(
                f"Loaded privacy budget state: "
                f"ε={self.total_epsilon_spent:.2f}, "
                f"rounds={self.rounds_participated}"
            )
        except Exception as e:
            logger.error(f"Failed to load privacy budget state: {e}")


# Global singleton
_tracker_instance: Optional[PrivacyBudgetTracker] = None


def get_privacy_budget_tracker() -> PrivacyBudgetTracker:
    """Get singleton privacy budget tracker"""
    global _tracker_instance
    if _tracker_instance is None:
        import os
        _tracker_instance = PrivacyBudgetTracker(
            epsilon_per_round=float(os.getenv("DP_EPSILON", "1.0")),
            total_epsilon_limit=float(os.getenv("DP_EPSILON_LIMIT", "10.0")),
        )
    return _tracker_instance
