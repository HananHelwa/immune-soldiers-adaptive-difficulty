"""Adds a fourth condition -- a "well-tuned" static baseline (same fixed
rotation, but every KC at the single best uniform tier, "Medium", rather
than the original game's per-KC assignment) -- and compares it against the
other three conditions with the same 15-replication rigor as Table 1.

Addresses the limitation named in Section 5.3: how much of the original
static baseline's poor equity is an avoidable design choice (mismatched
per-KC tiers) versus inherent to any fixed-difficulty design. Not part of
the main pipeline; run manually.
"""

import statistics

from config import KCS
from controller import StaticMatchedController
from metrics import summarize_condition
from run_simulation import run_condition

SEEDS = list(range(1, 16))
N_LEARNERS = 200


def collect():
    metrics = {"challenge_skill_balance": [], "calibration_r": [], "frustration": [], "boredom": [], "mastery_range": [], "mean_final_true": []}
    for seed in SEEDS:
        results = run_condition("static_matched", lambda rng: StaticMatchedController("Medium"), N_LEARNERS, seed)
        summary = summarize_condition(results)
        finals = [summary["final_mastery"][kc]["mean_final_true_skill"] for kc in KCS]
        metrics["challenge_skill_balance"].append(summary["challenge_skill_balance"])
        metrics["calibration_r"].append(summary["estimator_calibration_r"])
        metrics["frustration"].append(summary["engagement"]["mean_frustration"])
        metrics["boredom"].append(summary["engagement"]["mean_boredom"])
        metrics["mastery_range"].append(max(finals) - min(finals))
        metrics["mean_final_true"].append(sum(finals) / len(finals))
    return metrics


def report(metrics):
    print("=== static_matched (Medium, uniform), n=15 seeds ===")
    for name, vals in metrics.items():
        m = statistics.mean(vals)
        s = statistics.stdev(vals)
        print(f"  {name}: {m:.3f} +/- {s:.3f} (min {min(vals):.3f}, max {max(vals):.3f})")


if __name__ == "__main__":
    report(collect())
