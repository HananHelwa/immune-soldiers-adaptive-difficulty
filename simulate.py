"""Per-learner simulation loop (Section 3.5): plays one synthetic learner through
one experimental condition and returns a flat trace of per-encounter records
plus the final knowledge-tracer and learner state.
"""

import random

from bkt import TwoChannelBKT
from config import (
    BKT_P_F,
    BKT_P_G,
    BKT_P_L0,
    BKT_P_S,
    BKT_P_T,
    CONFIRMATION_STREAK,
    KCS,
    MASTERY_THRESHOLD,
    N_ENCOUNTERS,
    QUIZ_CHANNEL_PRESENT_PROB,
    SESSION_LENGTH,
    TIER_DIFFICULTY,
)
from learner import SyntheticLearner


def run_single_learner(learner_id: int, controller, rng: random.Random, mood_noise_sd: float = 0.0) -> dict:
    learner = SyntheticLearner(rng)
    tracer = TwoChannelBKT(KCS, BKT_P_L0, BKT_P_T, BKT_P_G, BKT_P_S, BKT_P_F)
    last_practiced = {kc: -1 for kc in KCS}
    practiced_this_session = set()
    streak = {kc: 0 for kc in KCS}  # consecutive above-threshold practices, see CONFIRMATION_STREAK
    trace = []

    t = 0
    while t < N_ENCOUNTERS:
        if t > 0 and t % SESSION_LENGTH == 0:
            tracer.end_session()
            learner.apply_forgetting(practiced_this_session)
            for kc in KCS:
                if kc not in practiced_this_session and tracer.mastery[kc] < MASTERY_THRESHOLD:
                    streak[kc] = 0  # forgetting revoked an earlier confirmation
            practiced_this_session = set()

        kc, tier = controller.choose_encounter(tracer.mastery, last_practiced, streak, t)
        if kc is None:
            trace.append({"learner_id": learner_id, "encounter_idx": t, "event": "all_kcs_mastered"})
            break

        difficulty = TIER_DIFFICULTY[tier]
        success, learning_opportunity, p_true = learner.attempt(kc, difficulty, rng, mood_noise_sd)
        quiz_present = rng.random() < QUIZ_CHANNEL_PRESENT_PROB
        # Quiz and combat are two independent Bernoulli draws from the same underlying
        # success probability p_true, not the same draw reused -- treating them as
        # perfectly correlated would double-count one observation as two.
        quiz_outcome = (rng.random() < p_true) if quiz_present else None

        tracer.observe(kc, "combat", success)
        if quiz_present:
            tracer.observe(kc, "quiz", quiz_outcome)
        tracer.apply_transit(kc)

        learner.record_attempt(kc, success, learning_opportunity)
        if hasattr(controller, "record_outcome"):
            controller.record_outcome(kc, tier, success)

        last_practiced[kc] = t
        practiced_this_session.add(kc)
        streak[kc] = streak[kc] + 1 if tracer.mastery[kc] >= MASTERY_THRESHOLD else 0

        trace.append(
            {
                "learner_id": learner_id,
                "encounter_idx": t,
                "kc": kc,
                "tier": tier,
                "difficulty": difficulty,
                "quiz_outcome": quiz_outcome,
                "combat_outcome": success,
                "success_prob_true": p_true,
                "model_mastery": tracer.mastery[kc],
                "true_skill": learner.true_skill[kc],
                "frustration": learner.frustration[kc],
                "boredom": learner.boredom[kc],
                "retries": 0 if success else rng.randint(1, 3),
                "latency_ms": max(500, round(rng.gauss(4000, 1000))),
            }
        )
        t += 1

    return {
        "trace": trace,
        "final_mastery": dict(tracer.mastery),
        "final_true_skill": dict(learner.true_skill),
    }
