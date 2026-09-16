# Simulation code (Section 3.5 / Section 4)

Stdlib-only Python 3 (no numpy/pandas), so it runs from a bare install — matches
the eventual GitHub Data Availability link.

## Run

```
python run_simulation.py                       # N=200 learners, default seed
python run_simulation.py --learners 50          # smaller/faster run
python run_simulation.py --save-traces          # also writes per-encounter CSVs
```

Outputs land in `results/`: `summary.json` (full nested metrics per condition),
`summary.csv` (flattened, one row per condition x KC), and, with `--save-traces`,
`traces_<condition>.csv` (every encounter, every learner).

## Files

- `config.py` — every tunable parameter, with inline notes on *why* each default
  was set the way it was (several were revised after the first couple of runs
  surfaced real issues — see below).
- `bkt.py` — two-channel Bayesian Knowledge Tracing (Section 3.2).
- `bandit.py` — mastery-biased UCB1 bandit over difficulty tiers (Section 3.3).
- `controller.py` — the three experimental conditions' encounter-selection logic.
- `learner.py` — synthetic learner agents: true skill, IRT-based response
  generation, engagement dynamics (Section 3.5).
- `simulate.py` — per-learner simulation loop tying the above together.
- `metrics.py` — the five metrics reported in Section 4.
- `run_simulation.py` — CLI entry point.

## What changed during development (worth keeping in the paper's methods/limitations)

1. **Double learning-transit bug** (fixed): the original code applied BKT's
   learning-transit step once per *observation channel* rather than once per
   *encounter*, so an encounter with both a quiz and a combat observation
   inflated mastery twice. Fixed by splitting `observe()` (per channel) from
   `apply_transit()` (once per encounter).
2. **Perfectly-correlated channels bug** (fixed): quiz and combat outcomes were
   generated from the same random draw, violating the conditional-independence
   assumption behind treating them as two separate Bayesian observations. Fixed
   by drawing two independent Bernoulli outcomes from the same success
   probability.
3. **Estimator overconfidence** (mitigated, not eliminated): even after (1)-(2),
   the BKT estimate reliably crossed the mastery threshold while true skill
   almost never did within a short session. Retuning `P_T` down and `P_S` up
   helped a little; the deeper cause was structural (see 4).
4. **Session length / threshold too tight** (fixed): 60 encounters split five
   ways left too little room for genuine learning opportunities, given the IRT
   response function saturates (no learning credit) once skill and difficulty
   are far apart. Raised to 120 encounters and lowered the mastery threshold
   0.8 -> 0.7.
5. **Premature abandonment** (fixed, and the most substantive finding): with a
   single-crossing mastery rule, the adaptive controller moved on from a KC the
   moment the (still slightly optimistic) estimate crossed threshold, before
   true skill had caught up -- a real failure mode in knowledge-tracing-driven
   adaptive systems, not specific to this simulation. Fixed by requiring
   `CONFIRMATION_STREAK` (3) consecutive above-threshold practices before a KC
   counts as mastered, mirroring how mastery-learning ITS are built in
   practice [17]. Applied identically to the `time_to_mastery` metric so all
   three conditions are compared on equal footing.

## Robustness checks (`multi_seed_report.py`, `robustness_checks.py`)

Not part of the main pipeline; run manually when asked.

- `multi_seed_report.py` — re-runs the full experiment across 15 seeds and reports mean ± SD per condition, instead of trusting one run.
- `robustness_checks.py` — two checks addressing specific validity concerns:
  1. **Cross-model check**: adds a "good/bad day" noise term to the synthetic learner's response generation (`mood_noise_sd`, off by default everywhere else) that the AI's own assumptions (BKT, the bandit) know nothing about — tests whether results depend on the AI being well-matched to its own test world.
  2. **Sensitivity sweep**: varies the IRT response-curve slope and the BKT learning-transit rate across a small range each, one at a time, to test whether the story depends on the exact hand-picked settings reported in Section 4.

Both checks: the cross-concept equity finding (Section 4.4) held up essentially unchanged. The challenge-skill-balance ranking held under the parameter sweep but was less stable under the noisy-world check specifically (the ablation condition became worst rather than middle) — reported as found, not smoothed over.

- `premature_mastery_check.py` — a scientific-review pass on the manuscript caught that Contribution 5 ("requiring sustained evidence mitigates premature mastery declaration") was never actually backed by a quantified result — only by a qualitative development anecdote (the bullet above about item 5). This script quantifies it directly across `m` in {1, 3, 10}: 92.8% -> 72.3% -> 15.4% of KC-confirmations happen while true skill is still below threshold. `CONFIRMATION_STREAK` was raised to 10 as the final default after this sweep (`config.py`), since it also improved calibration and frustration with negligible cost to the equity finding (`multi_seed_report.py`). Now reported in the manuscript's Section 4.7, not left as an unverified claim.

## Figures (`figures.py`)

Generates the three figures embedded in the manuscript, directly from simulation output, at 600 dpi PNG (MDPI's preferred minimum) plus vector PDF. Not part of the main pipeline; run manually; requires matplotlib.

- Figure 1: final true mastery per KC per condition (visualizes Table 2).
- Figure 2: condition-level metrics, mean ± SD over 15 replications (visualizes Table 1).
- Figure 3: population-mean true-skill trajectory over the session for the trapped KC (tolerance & autoimmunity), static vs. full adaptive.

Colors are the first three slots of the dataviz skill's validated categorical palette (blue/orange/aqua), assigned in the fixed order static/adaptive/ablation across every figure — never reassigned by rank or by which condition "wins" a given metric.

Figure 3 went through one real correction worth knowing about if extending this script: the first version averaged true_skill only over learners still being actively practiced at each attempt number. Since a learner stops being served a KC once it's confirmed-mastered, and confirmation correlates with being a stronger learner, the surviving "still being practiced" sample skews toward strugglers over time — producing a curve for full adaptive that appeared to peak around 0.60 and then decline, flatly contradicting Table 2's actual final mean of 0.75. The fix was to forward-fill each learner's last known value and average over all 200 learners at every point in the session, so the curve's right-hand edge reproduces Table 2 by construction rather than by coincidence.

## Graphical Abstract (`graphical_abstract.py`)

Generates MDPI's required Graphical Abstract: a schematic before/after diagram (fixed vs. adaptive difficulty, plus the AI-layer feedback loop), deliberately distinct in style from Figures 1-3 so it doesn't duplicate a body figure. The "before" bar heights are the real Table 2 static-condition values, not illustrative numbers. Two real bugs fixed during development, in case the script is extended: (1) the bar-group column width was computed incorrectly, causing bars to overlap the center diagram; (2) Unicode checkmark/X glyphs fell back to a broken symbol font once Arial was set (Arial lacks those glyphs) -- fixed by using plain ASCII "X" and a hand-drawn vector checkmark instead of any font-dependent glyph.

## Headline pattern after all of the above (N=200, seed 20260912)

- **Static baseline** creates a "difficulty trap": KCs whose fixed tier happens
  to match typical learner skill converge fine (final true skill ~0.68-0.79),
  but the one fixed to "Hard" by design (tolerance/autoimmunity, the final
  boss) gets stuck around 0.40 -- it is never given content it can actually
  learn from.
- **Full adaptive** equalizes final true skill across all five KCs (~0.61-0.63
  each) -- no concept is left behind, directly fixing the static baseline's
  worst-case failure -- though it doesn't push the "easy" KCs as high as static
  did, an equity-vs-peak-performance trade-off worth discussing explicitly.
- **Ablation (random tier)** shares the equalization property with full
  adaptive (same KC-selection rule) but takes ~30% longer to converge, has
  double the frustration, and a meaningfully worse challenge-skill balance --
  isolating that the *bandit's* contribution is efficiency and engagement, not
  the equity gain (which comes from mastery-based KC selection alone).
- **Estimator calibration** (`estimator_calibration_r`) sits around 0.56-0.76
  -- positive and meaningful, but far from perfect, which is itself worth
  reporting: hand-set BKT priors should not be trusted as well-calibrated
  without fitting to real pilot data before any classroom deployment.

None of the numeric constants above are final -- see the inline notes in
`config.py` for what's still a placeholder pending a deliberate sensitivity
analysis.
