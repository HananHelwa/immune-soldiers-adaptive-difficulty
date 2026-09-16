"""Two one-off robustness checks, not part of the main pipeline:

1. Cross-model check: does the pattern survive when the synthetic world adds
   per-attempt "good/bad day" noise that the AI's own assumptions (BKT, the
   bandit's reward shaping) know nothing about -- i.e., is the benefit real
   under a world that doesn't behave exactly like the clean curve the system
   was built and tuned against.
2. Sensitivity sweep: does the pattern survive varying two hand-picked
   settings (IRT response slope, BKT learning-transit rate) instead of
   trusting only the one combination reported in Section 4.
"""

import learner as learner_module
import simulate as simulate_module
from config import KCS
from metrics import summarize_condition
from run_simulation import CONDITIONS, run_condition


def headline(results):
    summary = summarize_condition(results)
    finals = [summary["final_mastery"][kc]["mean_final_true_skill"] for kc in KCS]
    return summary["challenge_skill_balance"], max(finals) - min(finals)


def cross_model_check(seeds=(1, 2, 3, 4, 5), mood_noise_sd=0.15):
    print(f"\n=== Cross-model check: mood_noise_sd={mood_noise_sd} (n={len(seeds)} seeds) ===")
    for cond, factory in CONDITIONS.items():
        csbs, ranges = [], []
        for seed in seeds:
            results = run_condition(cond, factory, 200, seed, mood_noise_sd)
            csb, rng_ = headline(results)
            csbs.append(csb)
            ranges.append(rng_)
        print(f"  {cond}: challenge_skill_balance={sum(csbs)/len(csbs):.3f}  mastery_range={sum(ranges)/len(ranges):.3f}")


def sensitivity_sweep():
    print("\n=== Sensitivity sweep: IRT_SLOPE_BETA (single seed=1 per setting) ===")
    original_beta = learner_module.IRT_SLOPE_BETA
    for beta in (4.0, 6.0, 8.0):
        learner_module.IRT_SLOPE_BETA = beta
        print(f" beta={beta}")
        for cond, factory in CONDITIONS.items():
            results = run_condition(cond, factory, 200, 1)
            csb, rng_ = headline(results)
            print(f"   {cond}: challenge_skill_balance={csb:.3f}  mastery_range={rng_:.3f}")
    learner_module.IRT_SLOPE_BETA = original_beta

    print("\n=== Sensitivity sweep: BKT_P_T learning-transit rate (single seed=1 per setting) ===")
    original_pt = simulate_module.BKT_P_T
    for pt in (0.04, 0.06, 0.10):
        simulate_module.BKT_P_T = pt
        print(f" P_T={pt}")
        for cond, factory in CONDITIONS.items():
            results = run_condition(cond, factory, 200, 1)
            csb, rng_ = headline(results)
            print(f"   {cond}: challenge_skill_balance={csb:.3f}  mastery_range={rng_:.3f}")
    simulate_module.BKT_P_T = original_pt


if __name__ == "__main__":
    cross_model_check()
    sensitivity_sweep()
