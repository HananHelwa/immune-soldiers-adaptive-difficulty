"""One-off robustness check: re-run the full N=200 experiment across many seeds
and report mean +/- SD per condition, instead of trusting a single run plus a
3-seed spot check. Not part of the main pipeline -- run manually when asked.
"""

import statistics

from config import KCS
from metrics import summarize_condition
from run_simulation import CONDITIONS, run_condition

SEEDS = list(range(1, 16))  # 15 independent replications of the N=200 population
N_LEARNERS = 200


def collect() -> dict:
    per_condition = {
        cond: {"challenge_skill_balance": [], "calibration_r": [], "frustration": [], "boredom": [], "mastery_range": []}
        for cond in CONDITIONS
    }
    for seed in SEEDS:
        for cond, factory in CONDITIONS.items():
            results = run_condition(cond, factory, N_LEARNERS, seed)
            summary = summarize_condition(results)
            per_condition[cond]["challenge_skill_balance"].append(summary["challenge_skill_balance"])
            per_condition[cond]["calibration_r"].append(summary["estimator_calibration_r"])
            per_condition[cond]["frustration"].append(summary["engagement"]["mean_frustration"])
            per_condition[cond]["boredom"].append(summary["engagement"]["mean_boredom"])
            finals = [summary["final_mastery"][kc]["mean_final_true_skill"] for kc in KCS]
            per_condition[cond]["mastery_range"].append(max(finals) - min(finals))
    return per_condition


def report(per_condition: dict) -> None:
    for cond, metrics in per_condition.items():
        print(f"=== {cond} (n={len(SEEDS)} seeds) ===")
        for name, vals in metrics.items():
            m = statistics.mean(vals)
            s = statistics.stdev(vals) if len(vals) > 1 else 0.0
            print(f"  {name}: {m:.3f} +/- {s:.3f}  (min {min(vals):.3f}, max {max(vals):.3f})")


if __name__ == "__main__":
    report(collect())
