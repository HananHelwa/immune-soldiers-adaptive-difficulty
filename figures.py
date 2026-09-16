"""Generates the manuscript's data figures directly from simulation output.
Not part of the main pipeline; run manually. Requires matplotlib.

Figure 1: final true mastery per KC per condition (visualizes Table 2 -- the
           difficulty-trap / equity finding).
Figure 2: condition-level metrics, mean +/- SD over 15 replications
          (visualizes Table 1).
Figure 3: true-skill trajectory over the session for one representative
          learner on the trapped KC (tolerance_autoimmunity), static vs
          full adaptive -- shows the difficulty trap emerging over time.

Colors are the dataviz skill's first three validated categorical slots
(blue/orange/aqua), assigned in a fixed order (static/adaptive/ablation)
across every figure, per the "color follows the entity" rule.
"""

import os
import random

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import KCS
from metrics import summarize_condition
from multi_seed_report import SEEDS
from run_simulation import CONDITIONS, run_condition
from simulate import run_single_learner

OUT_DIR = os.path.join(os.path.dirname(__file__), "figures")
os.makedirs(OUT_DIR, exist_ok=True)

COLOR_STATIC = "#2a78d6"   # categorical slot 1 (blue)
COLOR_ADAPTIVE = "#eb6834"  # categorical slot 2 (orange)
COLOR_ABLATION = "#1baf7a"  # categorical slot 3 (aqua)
INK = "#0b0b0b"
MUTED = "#898781"
GRIDLINE = "#e1e0d9"
LABELS = {"static_baseline": "Static baseline", "full_adaptive": "Full adaptive", "ablation_random_tier": "Ablation (random tier)"}
COLORS = {"static_baseline": COLOR_STATIC, "full_adaptive": COLOR_ADAPTIVE, "ablation_random_tier": COLOR_ABLATION}
KC_LABELS = {
    "innate_immunity": "Innate\nimmunity",
    "antigen_recognition": "Antigen\nrecognition",
    "cell_mediated_immunity": "Cell-mediated\nimmunity",
    "humoral_immunity": "Humoral\nimmunity",
    "tolerance_autoimmunity": "Tolerance &\nautoimmunity",
}

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "text.color": INK,
    "axes.edgecolor": GRIDLINE,
    "axes.labelcolor": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.grid": True,
    "grid.color": GRIDLINE,
    "grid.linewidth": 0.6,
    "axes.axisbelow": True,
})


def _style_axes(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.grid(axis="x", visible=False)
    ax.tick_params(axis="both", length=0)


def figure1_final_mastery():
    results_by_cond = {cond: run_condition(cond, factory, 200, 1) for cond, factory in CONDITIONS.items()}
    summaries = {cond: summarize_condition(res) for cond, res in results_by_cond.items()}

    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = range(len(KCS))
    width = 0.25
    for i, cond in enumerate(CONDITIONS):
        vals = [summaries[cond]["final_mastery"][kc]["mean_final_true_skill"] for kc in KCS]
        positions = [xi + (i - 1) * width for xi in x]
        ax.bar(positions, vals, width=width, color=COLORS[cond], label=LABELS[cond], zorder=3)

    ax.axhline(0.7, color=MUTED, linewidth=1, linestyle="--", zorder=2)
    ax.text(len(KCS) - 0.55, 0.715, "mastery threshold (θ=0.7)", color=MUTED, fontsize=8, ha="right")

    ax.set_xticks(list(x))
    ax.set_xticklabels([KC_LABELS[kc] for kc in KCS], fontsize=9)
    ax.set_ylabel("Final true skill")
    ax.set_ylim(0, 1.0)
    ax.set_title("Final true mastery per knowledge component", fontsize=11, loc="left", color=INK)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=9)
    _style_axes(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "figure1_final_mastery.png"), dpi=600)
    fig.savefig(os.path.join(OUT_DIR, "figure1_final_mastery.pdf"))
    plt.close(fig)
    print("Wrote figure1_final_mastery.{png,pdf}")


def figure2_condition_metrics():
    metric_keys = [
        ("challenge_skill_balance", "Challenge–skill balance"),
        ("estimator_calibration_r", "Estimator calibration (r)"),
        ("frustration", "Mean frustration"),
        ("boredom", "Mean boredom"),
    ]
    means = {cond: {k: [] for k, _ in metric_keys} for cond in CONDITIONS}
    for seed in SEEDS:
        for cond, factory in CONDITIONS.items():
            summary = summarize_condition(run_condition(cond, factory, 200, seed))
            means[cond]["challenge_skill_balance"].append(summary["challenge_skill_balance"])
            means[cond]["estimator_calibration_r"].append(summary["estimator_calibration_r"])
            means[cond]["frustration"].append(summary["engagement"]["mean_frustration"])
            means[cond]["boredom"].append(summary["engagement"]["mean_boredom"])

    def mean(xs):
        return sum(xs) / len(xs)

    def stdev(xs):
        m = mean(xs)
        return (sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) ** 0.5

    fig, axes = plt.subplots(1, 4, figsize=(11, 3.6))
    for ax, (key, title) in zip(axes, metric_keys):
        conds = list(CONDITIONS.keys())
        vals = [mean(means[c][key]) for c in conds]
        errs = [stdev(means[c][key]) for c in conds]
        colors = [COLORS[c] for c in conds]
        ax.bar(range(3), vals, yerr=errs, capsize=3, color=colors, zorder=3,
               error_kw={"ecolor": MUTED, "elinewidth": 1})
        ax.set_xticks(range(3))
        ax.set_xticklabels(["Static", "Adaptive", "Ablation"], fontsize=8, rotation=0)
        ax.set_title(title, fontsize=9.5, loc="left", color=INK)
        _style_axes(ax)
    fig.suptitle("Condition-level metrics, mean ± SD over 15 replications", fontsize=11, x=0.02, ha="left", color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(os.path.join(OUT_DIR, "figure2_condition_metrics.png"), dpi=600)
    fig.savefig(os.path.join(OUT_DIR, "figure2_condition_metrics.pdf"))
    plt.close(fig)
    print("Wrote figure2_condition_metrics.{png,pdf}")


def _mean_true_skill_over_session(cond, factory, kc, n_learners=200, seed=1, n_encounters=120):
    """Mean true_skill on `kc` across ALL learners at each point in the session
    (encounter index), forward-filling each learner's last known value between
    their own practices of this KC. This is the statistically correct way to
    show a population trajectory here: a first version of this figure averaged
    only over learners still being actively practiced at each attempt number,
    which silently drops learners once they are confirmed-mastered and stop
    being served this KC -- since confirmation correlates with being a strong
    learner, that dropped-out-early group is systematically the *strongest*
    performers, so the remaining "still being practiced" sample skews weaker
    over time. That produced a curve for full adaptive that appeared to peak
    and then decline, contradicting Table 2's final mean of 0.75 -- an
    artifact of changing sample composition, not of learners forgetting.
    Forward-filling keeps every learner in the average throughout, so the
    right-hand edge of this curve reproduces Table 2's final-mastery number
    exactly, by construction."""
    last_known = [None] * n_learners
    per_encounter_means = []
    for learner_id in range(n_learners):
        rng = random.Random(seed * 1000 + learner_id)
        controller = factory(rng)
        res = run_single_learner(learner_id, controller, rng)
        by_encounter = {r["encounter_idx"]: r["true_skill"] for r in res["trace"] if r.get("kc") == kc}
        last_known[learner_id] = by_encounter

    xs, means = [], []
    current = [None] * n_learners
    for t in range(n_encounters):
        for learner_id in range(n_learners):
            if t in last_known[learner_id]:
                current[learner_id] = last_known[learner_id][t]
        known = [v for v in current if v is not None]
        if known:
            xs.append(t)
            means.append(sum(known) / len(known))
    return xs, means


def figure3_difficulty_trap_trajectory():
    kc = "tolerance_autoimmunity"
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for cond in ("static_baseline", "full_adaptive"):
        xs, means = _mean_true_skill_over_session(cond, CONDITIONS[cond], kc)
        ax.plot(xs, means, color=COLORS[cond], label=LABELS[cond], linewidth=2)

    ax.axhline(0.7, color=MUTED, linewidth=1, linestyle="--", zorder=1)
    ax.text(2, 0.715, "mastery threshold (θ=0.7)", color=MUTED, fontsize=8)
    ax.set_xlabel("Encounter index (session)")
    ax.set_ylabel("Mean true skill across all 200 learners\n(tolerance & autoimmunity)")
    ax.set_ylim(0, 1.0)
    ax.set_title("The difficulty trap: population-mean learning curve", fontsize=11, loc="left", color=INK)
    ax.legend(frameon=False, loc="lower right", fontsize=9)
    _style_axes(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "figure3_difficulty_trap_trajectory.png"), dpi=600)
    fig.savefig(os.path.join(OUT_DIR, "figure3_difficulty_trap_trajectory.pdf"))
    plt.close(fig)
    print("Wrote figure3_difficulty_trap_trajectory.{png,pdf}")


if __name__ == "__main__":
    figure1_final_mastery()
    figure2_condition_metrics()
    figure3_difficulty_trap_trajectory()
