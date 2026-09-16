"""Aggregate metrics reported in Section 4 (Results), computed from the raw
per-learner traces produced by simulate.run_single_learner.
"""

from config import (
    CONFIRMATION_STREAK,
    FLOW_BAND_HALF_WIDTH,
    KCS,
    MASTERY_THRESHOLD,
    N_ENCOUNTERS,
    TARGET_BAND_CENTER,
)
from utils import mean, pearson_r, stdev


def _first_sustained_crossing(records: list, key: str, threshold: float, streak_required: int):
    """First encounter_idx after `streak_required` consecutive practices of this KC
    at or above `threshold` -- matches the controller's own confirmation rule
    (Section 4), rather than trusting a single crossing."""
    streak = 0
    for r in records:
        value = r.get(key)
        if value is not None and value >= threshold:
            streak += 1
            if streak >= streak_required:
                return r["encounter_idx"]
        else:
            streak = 0
    return None  # censored: never sustained mastery within N_ENCOUNTERS


def time_to_mastery(results: list, threshold: float = MASTERY_THRESHOLD) -> dict:
    out = {}
    for kc in KCS:
        model_times, true_times = [], []
        censored_model = censored_true = 0
        for res in results:
            kc_records = [r for r in res["trace"] if r.get("kc") == kc]
            t_model = _first_sustained_crossing(kc_records, "model_mastery", threshold, CONFIRMATION_STREAK)
            t_true = _first_sustained_crossing(kc_records, "true_skill", threshold, CONFIRMATION_STREAK)
            if t_model is None:
                censored_model += 1
            else:
                model_times.append(t_model)
            if t_true is None:
                censored_true += 1
            else:
                true_times.append(t_true)
        out[kc] = {
            "mean_encounters_to_mastery_model": mean(model_times) if model_times else float("nan"),
            "mean_encounters_to_mastery_true": mean(true_times) if true_times else float("nan"),
            "censored_model_frac": censored_model / len(results),
            "censored_true_frac": censored_true / len(results),
        }
    return out


def final_mastery_summary(results: list) -> dict:
    out = {}
    for kc in KCS:
        model_vals = [res["final_mastery"][kc] for res in results]
        true_vals = [res["final_true_skill"][kc] for res in results]
        out[kc] = {
            "mean_final_model_mastery": mean(model_vals),
            "mean_final_true_skill": mean(true_vals),
        }
    return out


def challenge_skill_balance(
    results: list, band_center: float = TARGET_BAND_CENTER, half_width: float = FLOW_BAND_HALF_WIDTH
) -> float:
    in_band, total = 0, 0
    lo, hi = band_center - half_width, band_center + half_width
    for res in results:
        for r in res["trace"]:
            if "success_prob_true" not in r:
                continue
            total += 1
            if lo <= r["success_prob_true"] <= hi:
                in_band += 1
    return in_band / total if total else float("nan")


def engagement_summary(results: list) -> dict:
    frustrations, boredoms = [], []
    for res in results:
        for r in res["trace"]:
            if "frustration" in r:
                frustrations.append(r["frustration"])
                boredoms.append(r["boredom"])
    return {
        "mean_frustration": mean(frustrations),
        "mean_boredom": mean(boredoms),
        "sd_frustration": stdev(frustrations),
        "sd_boredom": stdev(boredoms),
    }


def estimator_calibration(results: list) -> float:
    model_vals, true_vals = [], []
    for res in results:
        for r in res["trace"]:
            if "model_mastery" in r:
                model_vals.append(r["model_mastery"])
                true_vals.append(r["true_skill"])
    return pearson_r(model_vals, true_vals)


def summarize_condition(results: list) -> dict:
    return {
        "n_learners": len(results),
        "time_to_mastery": time_to_mastery(results),
        "final_mastery": final_mastery_summary(results),
        "challenge_skill_balance": challenge_skill_balance(results),
        "engagement": engagement_summary(results),
        "estimator_calibration_r": estimator_calibration(results),
    }
