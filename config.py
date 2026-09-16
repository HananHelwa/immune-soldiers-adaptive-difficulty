"""Default parameters for the Section 3.5 simulation. Stdlib-only by design (no numpy/pandas)
so the code is trivially runnable from a bare Python 3 install for the eventual Data
Availability repo.
"""

KCS = [
    "innate_immunity",
    "antigen_recognition",
    "cell_mediated_immunity",
    "humoral_immunity",
    "tolerance_autoimmunity",
]

TIERS = ["Easy", "Medium", "Hard"]
TIER_DIFFICULTY = {"Easy": 0.2, "Medium": 0.5, "Hard": 0.8}

# The static baseline mirrors the original game's fixed level order and a fixed
# per-stage difficulty (Section 3.5, condition 1) -- bosses (KC5) are hardest.
STATIC_TIER_BY_KC = {
    "innate_immunity": "Easy",
    "antigen_recognition": "Easy",
    "cell_mediated_immunity": "Medium",
    "humoral_immunity": "Medium",
    "tolerance_autoimmunity": "Hard",
}

# --- Knowledge tracing (Section 3.2) ---
# P_T was lowered (0.15 -> 0.06) and P_S raised (0.1 -> 0.15) after the first
# simulation run showed the estimator racing far ahead of true skill: P_T is
# BKT's "spontaneous learning" term applied on every attempt regardless of
# correctness, so a value this high made the estimate climb toward mastery
# almost independently of actual evidence. See estimator_calibration_r.
BKT_P_L0 = 0.1
BKT_P_T = 0.06
BKT_P_G = {"quiz": 0.2, "combat": 0.2}
BKT_P_S = {"quiz": 0.15, "combat": 0.15}
BKT_P_F = 0.05  # applied once per session boundary a KC was not practiced

MASTERY_THRESHOLD = 0.7  # theta: both for KC-selection eligibility and time-to-mastery.
# Was 0.8: with a ~0.08 true learning rate and IRT saturation removing some attempts
# from counting as genuine opportunities, 0.8 was structurally almost unreachable for
# true skill within a realistic session length regardless of BKT tuning -- see
# N_ENCOUNTERS below, raised alongside this for the same reason.

CONFIRMATION_STREAK = 10  # consecutive above-threshold practices required before a KC
# counts as mastered, for both KC-selection and the time-to-mastery metric. Added
# after simulation results showed the adaptive controller abandoning KCs the moment
# the (still slightly optimistic) estimator first crossed threshold, before true
# skill had caught up -- mirrors how mastery-learning ITS require sustained mastery
# rather than trusting a single observation [17]. Raised from an initial value of 3
# to 10 after a sweep (premature_mastery_check.py) showed 3 still left 72.3% of
# confirmations premature; 10 cuts that to ~16.7%, improves estimator calibration
# (0.575->0.694 in the single-seed sweep), and reduces frustration, at the cost of
# a modest rise in boredom (learners waiting out a longer confirmation window on
# concepts they've effectively already learned) -- reported as a real trade-off,
# not hidden. Diminishing returns and a shrinking confirmation sample set in
# beyond ~10-15.

# --- Adaptive difficulty controller (Section 3.3) ---
TARGET_BAND_CENTER = 0.7
FLOW_BAND_HALF_WIDTH = 0.15  # used for the challenge-skill-balance metric, Section 4
UCB_EXPLORATION_C = 2.0
BANDIT_ROLLING_WINDOW = 5

# --- Synthetic learner population (Section 3.5) ---
N_LEARNERS = 200
N_ENCOUNTERS = 120  # was 60 -- too few genuine per-KC learning opportunities to reach mastery
SESSION_LENGTH = 10  # encounters per sitting; forgetting applied at each boundary

INITIAL_SKILL_BETA_PARAMS = (2.0, 5.0)  # skew toward low pre-instruction skill
LEARNING_RATE_MEAN, LEARNING_RATE_SD = 0.08, 0.03
LEARNING_RATE_BOUNDS = (0.01, 0.30)
FORGETTING_RATE_MEAN, FORGETTING_RATE_SD = 0.03, 0.02
FORGETTING_RATE_BOUNDS = (0.0, 0.15)

IRT_SLOPE_BETA = 6.0
IRT_SUCCESS_FLOOR = 0.05
IRT_SUCCESS_CEIL = 0.95

QUIZ_CHANNEL_PRESENT_PROB = 0.7  # not every encounter includes a quiz/dialogue check

# Engagement dynamics (Section 3.5): rolling window of recent outcomes per learner
ENGAGEMENT_WINDOW = 4
FRUSTRATION_TRIGGER_FAIL_RATE = 0.75  # frustration builds if >=75% of last window failed
BOREDOM_TRIGGER_SUCCESS_RATE = 0.9    # boredom builds if >=90% of last window succeeded
ENGAGEMENT_STEP = 0.15
ENGAGEMENT_DECAY = 0.2
MAX_ENGAGEMENT_PENALTY = 0.8  # effective learning rate never drops below 20% of base

DEFAULT_SEED = 20260912
