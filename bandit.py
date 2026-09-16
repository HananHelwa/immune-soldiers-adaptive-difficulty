"""Contextual (mastery-biased) UCB1 bandit over difficulty tiers (Section 3.3).

One bandit instance per knowledge component. Value estimates are seeded from
current mastery rather than starting from a cold, uninformative prior -- low
mastery biases the initial preference toward Easy, high mastery toward Hard --
so the bandit already has a sensible default before it has pulled every arm.

Reward is shaped around the flow channel (Csikszentmihalyi, cited as [26] in
the manuscript): a tier is "good" when its rolling observed success rate sits
close to TARGET_BAND_CENTER, not when it is simply won or lost.
"""

import math
from collections import deque

from config import TIER_DIFFICULTY


class UCB1TierBandit:
    def __init__(self, tiers, target_band_center: float, c: float, window: int):
        self.tiers = tiers
        self.target_band_center = target_band_center
        self.c = c
        self.counts = {t: 1 for t in tiers}  # pseudo-count of 1 for the mastery-biased seed
        self.outcomes = {t: deque(maxlen=window) for t in tiers}  # raw success booleans
        self.total_pulls = len(tiers)  # matches the seeded pseudo-counts above

    def _seed_value(self, tier: str, mastery: float) -> float:
        # A tier is a good early guess when its difficulty roughly matches current
        # mastery (difficulty ~= mastery implies success probability near the flow band).
        return 1.0 - abs(TIER_DIFFICULTY[tier] - mastery)

    def _value_estimate(self, tier: str, mastery: float) -> float:
        history = self.outcomes[tier]
        if not history:
            return self._seed_value(tier, mastery)
        rolling_rate = sum(history) / len(history)
        return 1.0 - abs(rolling_rate - self.target_band_center)

    def select_tier(self, mastery: float) -> str:
        best_tier, best_score = None, -math.inf
        for tier in self.tiers:
            value = self._value_estimate(tier, mastery)
            bonus = self.c * math.sqrt(math.log(self.total_pulls) / self.counts[tier])
            score = value + bonus
            if score > best_score:
                best_tier, best_score = tier, score
        return best_tier

    def update(self, tier: str, observed_success: bool) -> None:
        self.counts[tier] += 1
        self.total_pulls += 1
        self.outcomes[tier].append(1.0 if observed_success else 0.0)
