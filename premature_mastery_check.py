"""Quantifies how often the controller declares a KC 'mastered' while true
skill is still below threshold, comparing the old single-crossing rule
(CONFIRMATION_STREAK=1) against the current sustained-evidence rule
(CONFIRMATION_STREAK=3). Backs Section 4.7 / Contribution 5 / Section 5.3's
premature-mastery-declaration finding. Not part of the main pipeline; run
manually.
"""

import controller as controller_module
from config import KCS, MASTERY_THRESHOLD
from run_simulation import CONDITIONS, run_condition


def premature_rate(streak_value: int, seeds=(1, 2, 3, 4, 5), n_learners: int = 200) -> tuple:
    controller_module.CONFIRMATION_STREAK = streak_value
    total, premature = 0, 0
    for seed in seeds:
        results = run_condition("full_adaptive", CONDITIONS["full_adaptive"], n_learners, seed)
        for res in results:
            declared = {}
            streaks = {kc: 0 for kc in KCS}
            for r in res["trace"]:
                if "kc" not in r:
                    continue
                kc = r["kc"]
                if kc in declared:
                    continue
                if r["model_mastery"] >= MASTERY_THRESHOLD:
                    streaks[kc] += 1
                else:
                    streaks[kc] = 0
                if streaks[kc] >= streak_value:
                    declared[kc] = r["true_skill"]
            for kc, true_at_declare in declared.items():
                total += 1
                if true_at_declare < MASTERY_THRESHOLD:
                    premature += 1
    return premature / total, total


if __name__ == "__main__":
    for streak in (1, 3, 10):
        rate, n = premature_rate(streak)
        print(f"CONFIRMATION_STREAK={streak}: premature-declaration rate = {rate:.1%} (n={n} KC-confirmations observed)")
