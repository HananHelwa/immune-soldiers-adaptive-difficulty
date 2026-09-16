"""Generates the MDPI Graphical Abstract: a schematic (not data-plot) diagram
distinct from Figures 1-3, per MDPI's requirement that a GA not duplicate a
body figure or simply combine the text abstract with a picture. Not part of
the main simulation pipeline; run manually. Requires matplotlib.

Layout: "before" (fixed difficulty, one concept stuck below threshold) ->
AI-layer feedback loop (knowledge tracing -> adaptive controller -> game
encounter) -> "after" (adaptive difficulty, every concept reaches threshold).
Colors reuse the same fixed categorical assignment as every other figure in
the paper (blue = static/fixed, orange = full adaptive) for consistency.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

OUT_DIR = os.path.join(os.path.dirname(__file__), "figures")
os.makedirs(OUT_DIR, exist_ok=True)

COLOR_STATIC = "#2a78d6"
COLOR_ADAPTIVE = "#eb6834"
INK = "#0b0b0b"
MUTED = "#898781"
GOOD = "#0ca30c"
CRITICAL = "#d03b3b"
BOX_FACE = "#fcfcfb"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],  # MDPI's GA font list; DejaVu Sans is a last-resort fallback only
    "font.size": 12,
    "text.color": INK,
})


def bar_group(ax, x_lo, x_hi, values, color, threshold=0.7, flag=None):
    """Five vertical bars evenly filling [x_lo, x_hi], each `values[i]` tall (0-1 scale)."""
    n = len(values)
    gap = (x_hi - x_lo) * 0.06
    width = ((x_hi - x_lo) - (n - 1) * gap) / n
    for i, v in enumerate(values):
        x = x_lo + i * (width + gap)
        ax.add_patch(Rectangle((x, 0), width, v, facecolor=color, edgecolor="none", zorder=3))
        marker_y = v + 0.05
        cx_m = x + width / 2
        if flag == "below" and v < threshold:
            # Plain "X" text (safe ASCII, renders in any font) rather than a
            # dingbat glyph -- a Unicode checkmark/cross previously fell back
            # to a broken symbol font on this system and rendered as tofu.
            ax.text(cx_m, marker_y, "X", color=CRITICAL, fontsize=13, weight="bold", ha="center", va="bottom", zorder=4)
        elif flag == "above":
            # Hand-drawn checkmark (vector lines), same reasoning: never
            # depends on a font having the right glyph.
            s = 0.018
            ax.plot([cx_m - s, cx_m - s * 0.2, cx_m + s * 1.2],
                    [marker_y + s * 0.6, marker_y, marker_y + s * 1.4],
                    color=GOOD, linewidth=2.2, solid_capstyle="round", zorder=4)
    ax.plot([x_lo - gap * 0.5, x_hi + gap * 0.5], [threshold, threshold],
            color=MUTED, linewidth=1.3, linestyle="--", zorder=2)


def flow_box(ax, cx, cy, w, h, text):
    box = FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle="round,pad=0.01,rounding_size=0.02",
                          facecolor=BOX_FACE, edgecolor=INK, linewidth=1.4, zorder=3)
    ax.add_patch(box)
    ax.text(cx, cy, text, ha="center", va="center", fontsize=11, color=INK, zorder=4, wrap=True)


def arrow(ax, p0, p1, curve=0.0):
    a = FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=16, color=INK,
                         linewidth=1.4, connectionstyle=f"arc3,rad={curve}", zorder=2)
    ax.add_patch(a)


def build():
    fig, ax = plt.subplots(figsize=(13.75, 7.0))
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.14, 1.05)
    ax.axis("off")

    BEFORE_LO, BEFORE_HI = 0.02, 0.24
    CENTER_LO, CENTER_HI = 0.32, 0.68
    AFTER_LO, AFTER_HI = 0.76, 0.98
    before_cx = (BEFORE_LO + BEFORE_HI) / 2
    center_cx = (CENTER_LO + CENTER_HI) / 2
    after_cx = (AFTER_LO + AFTER_HI) / 2

    # --- "Before": fixed difficulty ---
    ax.text(before_cx, 0.98, "Fixed difficulty\n(original design)", ha="center", fontsize=13, weight="bold", color=INK)
    before_vals = [0.68, 0.68, 0.76, 0.79, 0.40]
    bar_group(ax, BEFORE_LO, BEFORE_HI, before_vals, COLOR_STATIC, flag="below")
    ax.text(before_cx, -0.10, "One concept left behind, no matter\nhow many attempts a learner makes",
            ha="center", fontsize=10, color=MUTED)

    # --- Center: AI layer feedback loop (top-to-bottom pipeline + return arrow) ---
    ax.text(center_cx, 0.98, "AI layer\n(evaluated by simulation)", ha="center", fontsize=13, weight="bold", color=INK)
    box_hw, box_hh = 0.15, 0.065
    ys = [0.84, 0.61, 0.38, 0.15]
    labels = ["Learner plays\nan encounter", "Knowledge tracing:\nper-concept mastery estimate",
              "Adaptive difficulty controller\n(bandit)", "Next encounter:\nconcept + difficulty"]
    for y, label in zip(ys, labels):
        flow_box(ax, center_cx, y, 2 * box_hw, 2 * box_hh, label)
    for y0, y1 in zip(ys[:-1], ys[1:]):
        arrow(ax, (center_cx, y0 - box_hh), (center_cx, y1 + box_hh))
    return_x = CENTER_HI + 0.05
    arrow(ax, (center_cx + box_hw, ys[-1]), (return_x, ys[-1]), curve=0.0)
    arrow(ax, (return_x, ys[-1]), (return_x, ys[0]), curve=0.0)
    arrow(ax, (return_x, ys[0]), (center_cx + box_hw, ys[0]), curve=0.0)

    # --- "After": adaptive difficulty ---
    ax.text(after_cx, 0.98, "Adaptive difficulty\n(this paper)", ha="center", fontsize=13, weight="bold", color=INK)
    after_vals = [0.75, 0.74, 0.75, 0.75, 0.75]
    bar_group(ax, AFTER_LO, AFTER_HI, after_vals, COLOR_ADAPTIVE, flag="above")
    ax.text(after_cx, -0.10, "Every concept reaches mastery,\nincluding the one left behind before",
            ha="center", fontsize=10, color=MUTED)

    fig.tight_layout()
    out_png = os.path.join(OUT_DIR, "graphical_abstract.png")
    out_pdf = os.path.join(OUT_DIR, "graphical_abstract.pdf")
    fig.savefig(out_png, dpi=220, facecolor="white")
    fig.savefig(out_pdf, facecolor="white")
    plt.close(fig)
    print(f"Wrote {out_png} and {out_pdf}")


if __name__ == "__main__":
    build()
