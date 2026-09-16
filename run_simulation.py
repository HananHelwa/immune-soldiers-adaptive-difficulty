"""Entry point for the Section 3.5 / Section 4 simulation.

Usage:
    python run_simulation.py [--learners 200] [--seed 20260912] [--save-traces]

Population size and session length beyond --learners are set in config.py --
this script does not re-plumb every constant through argparse, since that
would add indirection a one-off research script does not need yet.
"""

import argparse
import csv
import json
import os
import random

from config import DEFAULT_SEED, KCS, N_LEARNERS
from controller import AblationController, AdaptiveController, StaticController
from metrics import summarize_condition
from simulate import run_single_learner

CONDITIONS = {
    "static_baseline": lambda rng: StaticController(),
    "full_adaptive": lambda rng: AdaptiveController(),
    "ablation_random_tier": lambda rng: AblationController(rng),
}


def run_condition(condition_name: str, controller_factory, n_learners: int, seed: int, mood_noise_sd: float = 0.0) -> list:
    results = []
    for learner_id in range(n_learners):
        rng = random.Random(seed * 1000 + learner_id)  # per-learner determinism, order-independent
        controller = controller_factory(rng)
        results.append(run_single_learner(learner_id, controller, rng, mood_noise_sd))
    return results


def flatten_summary_rows(condition_name: str, summary: dict) -> list:
    rows = []
    for kc in KCS:
        ttm = summary["time_to_mastery"][kc]
        fm = summary["final_mastery"][kc]
        rows.append(
            {
                "condition": condition_name,
                "kc": kc,
                "mean_encounters_to_mastery_model": ttm["mean_encounters_to_mastery_model"],
                "mean_encounters_to_mastery_true": ttm["mean_encounters_to_mastery_true"],
                "censored_model_frac": ttm["censored_model_frac"],
                "censored_true_frac": ttm["censored_true_frac"],
                "mean_final_model_mastery": fm["mean_final_model_mastery"],
                "mean_final_true_skill": fm["mean_final_true_skill"],
                "challenge_skill_balance": summary["challenge_skill_balance"],
                "mean_frustration": summary["engagement"]["mean_frustration"],
                "mean_boredom": summary["engagement"]["mean_boredom"],
                "estimator_calibration_r": summary["estimator_calibration_r"],
            }
        )
    return rows


def save_traces(condition_name: str, results: list, out_dir: str) -> None:
    path = os.path.join(out_dir, f"traces_{condition_name}.csv")
    fieldnames = [
        "learner_id", "encounter_idx", "kc", "tier", "difficulty", "quiz_outcome",
        "combat_outcome", "success_prob_true", "model_mastery", "true_skill",
        "frustration", "boredom", "retries", "latency_ms", "event",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for res in results:
            for r in res["trace"]:
                writer.writerow(r)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--learners", type=int, default=N_LEARNERS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--save-traces", action="store_true")
    parser.add_argument("--out-dir", type=str, default=os.path.join(os.path.dirname(__file__), "results"))
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    all_rows, full_summary = [], {}
    for condition_name, factory in CONDITIONS.items():
        results = run_condition(condition_name, factory, args.learners, args.seed)
        summary = summarize_condition(results)
        full_summary[condition_name] = summary
        all_rows.extend(flatten_summary_rows(condition_name, summary))
        if args.save_traces:
            save_traces(condition_name, results, args.out_dir)
        print(f"[{condition_name}] n={summary['n_learners']} "
              f"challenge_skill_balance={summary['challenge_skill_balance']:.3f} "
              f"calibration_r={summary['estimator_calibration_r']:.3f} "
              f"mean_frustration={summary['engagement']['mean_frustration']:.3f} "
              f"mean_boredom={summary['engagement']['mean_boredom']:.3f}")

    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(full_summary, f, indent=2)

    csv_path = os.path.join(args.out_dir, "summary.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nWrote {csv_path} and summary.json to {args.out_dir}")


if __name__ == "__main__":
    main()
