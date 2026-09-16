"""Encounter selection for the three experimental conditions (Section 3.5).

- StaticController: the original fixed level/stage/boss progression, condition 1.
- AdaptiveController: mastery-priority KC selection + UCB1 tier bandit, condition 2.
- AblationController: mastery-priority KC selection + random tier, condition 3
  (isolates how much of the adaptive effect comes from targeting the right
  concept versus from tuning difficulty within it).
"""

import random

from bandit import UCB1TierBandit
from config import (
    BANDIT_ROLLING_WINDOW,
    CONFIRMATION_STREAK,
    KCS,
    MASTERY_THRESHOLD,
    STATIC_TIER_BY_KC,
    TARGET_BAND_CENTER,
    TIERS,
    UCB_EXPLORATION_C,
)


def select_kc_by_mastery(mastery: dict, last_practiced: dict, streak: dict, threshold: float):
    """Lowest-mastery KC not yet *confirmed* mastered, ties broken by
    least-recently-practiced. A KC counts as confirmed (and drops out of
    selection) only after `streak` consecutive practiced encounters at or
    above `threshold` -- a single crossing is not trusted, since the BKT
    estimate is known (Section 4) to sometimes race ahead of true skill.
    Returns None once every KC is confirmed (session mastered)."""
    eligible = [kc for kc in KCS if streak[kc] < CONFIRMATION_STREAK]
    if not eligible:
        return None
    eligible.sort(key=lambda kc: (mastery[kc], last_practiced[kc]))
    return eligible[0]


class StaticController:
    """No mastery model involved by design -- this is the non-adaptive baseline."""

    def __init__(self):
        self._cycle = list(KCS)
        self._i = 0

    def choose_encounter(self, mastery: dict, last_practiced: dict, streak: dict, encounter_idx: int):
        kc = self._cycle[self._i % len(self._cycle)]
        self._i += 1
        return kc, STATIC_TIER_BY_KC[kc]


class StaticMatchedController:
    """A "well-tuned" non-adaptive baseline: same fixed rotation as StaticController,
    but every KC gets the same, population-appropriate tier, rather than the
    original game's per-KC assignment (which happens to mismatch one KC badly).
    All KCs draw initial skill from the same distribution (Section 3.5), so
    there is no principled reason for a fixed baseline to treat KCs differently
    here -- this isolates how much of StaticController's poor equity was an
    avoidable, arbitrary design choice versus inherent to non-adaptive difficulty."""

    def __init__(self, tier: str):
        self._cycle = list(KCS)
        self._i = 0
        self.tier = tier

    def choose_encounter(self, mastery: dict, last_practiced: dict, streak: dict, encounter_idx: int):
        kc = self._cycle[self._i % len(self._cycle)]
        self._i += 1
        return kc, self.tier


class AdaptiveController:
    def __init__(self):
        self.bandits = {
            kc: UCB1TierBandit(TIERS, TARGET_BAND_CENTER, UCB_EXPLORATION_C, BANDIT_ROLLING_WINDOW)
            for kc in KCS
        }

    def choose_encounter(self, mastery: dict, last_practiced: dict, streak: dict, encounter_idx: int):
        kc = select_kc_by_mastery(mastery, last_practiced, streak, MASTERY_THRESHOLD)
        if kc is None:
            return None, None
        tier = self.bandits[kc].select_tier(mastery[kc])
        return kc, tier

    def record_outcome(self, kc: str, tier: str, observed_success: bool) -> None:
        self.bandits[kc].update(tier, observed_success)


class AblationController:
    """Same KC-selection rule as AdaptiveController; tier chosen uniformly at random
    instead of via the bandit, to isolate the bandit's contribution."""

    def __init__(self, rng: random.Random):
        self.rng = rng

    def choose_encounter(self, mastery: dict, last_practiced: dict, streak: dict, encounter_idx: int):
        kc = select_kc_by_mastery(mastery, last_practiced, streak, MASTERY_THRESHOLD)
        if kc is None:
            return None, None
        tier = self.rng.choice(TIERS)
        return kc, tier

    def record_outcome(self, kc: str, tier: str, observed_success: bool) -> None:
        pass  # nothing to learn -- tier choice is random by design
