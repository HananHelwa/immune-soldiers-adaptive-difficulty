"""Synthetic learner agents (Section 3.5).

Each agent has its own true (latent, model-invisible) skill per KC, a per-KC
learning rate, and a per-KC forgetting rate, so a simulated population is
heterogeneous rather than one archetype repeated N times. Response generation
follows a 2-parameter-logistic IRT curve [27]; engagement (frustration/boredom)
feeds back into the effective learning rate, which is what makes the
challenge-skill-balance metric consequential rather than cosmetic.
"""

import random
from collections import deque

from config import (
    ENGAGEMENT_DECAY,
    ENGAGEMENT_STEP,
    ENGAGEMENT_WINDOW,
    FORGETTING_RATE_BOUNDS,
    FORGETTING_RATE_MEAN,
    FORGETTING_RATE_SD,
    FRUSTRATION_TRIGGER_FAIL_RATE,
    BOREDOM_TRIGGER_SUCCESS_RATE,
    INITIAL_SKILL_BETA_PARAMS,
    IRT_SLOPE_BETA,
    IRT_SUCCESS_CEIL,
    IRT_SUCCESS_FLOOR,
    KCS,
    LEARNING_RATE_BOUNDS,
    LEARNING_RATE_MEAN,
    LEARNING_RATE_SD,
    MAX_ENGAGEMENT_PENALTY,
)
from utils import clip, sample_bounded_gauss, sigmoid


def _sample_beta(alpha: float, beta_param: float, rng: random.Random) -> float:
    return rng.betavariate(alpha, beta_param)


class SyntheticLearner:
    def __init__(self, rng: random.Random):
        a, b = INITIAL_SKILL_BETA_PARAMS
        self.true_skill = {kc: _sample_beta(a, b, rng) for kc in KCS}
        self.learning_rate = {
            kc: sample_bounded_gauss(LEARNING_RATE_MEAN, LEARNING_RATE_SD, LEARNING_RATE_BOUNDS, rng)
            for kc in KCS
        }
        self.forgetting_rate = {
            kc: sample_bounded_gauss(FORGETTING_RATE_MEAN, FORGETTING_RATE_SD, FORGETTING_RATE_BOUNDS, rng)
            for kc in KCS
        }
        self.recent_outcomes = {kc: deque(maxlen=ENGAGEMENT_WINDOW) for kc in KCS}
        self.frustration = {kc: 0.0 for kc in KCS}
        self.boredom = {kc: 0.0 for kc in KCS}

    def success_probability(self, kc: str, difficulty: float, rng: random.Random = None, mood_noise_sd: float = 0.0) -> float:
        raw = sigmoid(IRT_SLOPE_BETA * (self.true_skill[kc] - difficulty))
        if mood_noise_sd > 0.0 and rng is not None:
            # Cross-model robustness check only (off by default, main results unaffected):
            # a per-attempt "good/bad day" perturbation the AI's own assumptions know
            # nothing about, testing whether the system's benefit survives a world that
            # doesn't behave like the clean logistic curve it was tuned against.
            raw += rng.gauss(0.0, mood_noise_sd)
        return clip(raw, IRT_SUCCESS_FLOOR, IRT_SUCCESS_CEIL)

    def attempt(self, kc: str, difficulty: float, rng: random.Random, mood_noise_sd: float = 0.0) -> tuple:
        p = self.success_probability(kc, difficulty, rng, mood_noise_sd)
        success = rng.random() < p
        learning_opportunity = IRT_SUCCESS_FLOOR < p < IRT_SUCCESS_CEIL
        return success, learning_opportunity, p

    def _effective_learning_rate(self, kc: str) -> float:
        penalty = clip(self.frustration[kc] + self.boredom[kc], 0.0, MAX_ENGAGEMENT_PENALTY)
        return self.learning_rate[kc] * (1.0 - penalty)

    def _update_engagement(self, kc: str, success: bool) -> None:
        self.recent_outcomes[kc].append(1.0 if success else 0.0)
        window = self.recent_outcomes[kc]
        if len(window) == window.maxlen:
            rate = sum(window) / len(window)
            if rate <= 1 - FRUSTRATION_TRIGGER_FAIL_RATE:
                self.frustration[kc] = clip(self.frustration[kc] + ENGAGEMENT_STEP, 0.0, 1.0)
            else:
                self.frustration[kc] = clip(self.frustration[kc] - ENGAGEMENT_DECAY, 0.0, 1.0)
            if rate >= BOREDOM_TRIGGER_SUCCESS_RATE:
                self.boredom[kc] = clip(self.boredom[kc] + ENGAGEMENT_STEP, 0.0, 1.0)
            else:
                self.boredom[kc] = clip(self.boredom[kc] - ENGAGEMENT_DECAY, 0.0, 1.0)

    def record_attempt(self, kc: str, success: bool, learning_opportunity: bool) -> None:
        self._update_engagement(kc, success)
        if not learning_opportunity:
            return
        eff_lr = self._effective_learning_rate(kc)
        # Success reinforces skill gain more than a near-miss failure still does;
        # both move skill toward mastery since a genuine learning opportunity fired.
        gain_multiplier = 1.2 if success else 0.6
        skill = self.true_skill[kc]
        self.true_skill[kc] = clip(skill + eff_lr * gain_multiplier * (1.0 - skill), 0.0, 1.0)

    def apply_forgetting(self, practiced_this_session: set) -> None:
        for kc in KCS:
            if kc not in practiced_this_session:
                self.true_skill[kc] = clip(
                    self.true_skill[kc] * (1 - self.forgetting_rate[kc]), 0.0, 1.0
                )
