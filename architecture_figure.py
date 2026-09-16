"""Renders Section 3.4's architecture diagram (originally Mermaid-only text)
as an actual figure, needed for the LaTeX/Overleaf version since LaTeX has
no native Mermaid support. Not part of the main pipeline; run manually.
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT_DIR = os.path.join(os.path.dirname(__file__), "figures")
os.makedirs(OUT_DIR, exist_ok=True)

INK = "#0b0b0b"
MUTED = "#898781"
BOX_FACE = "#fcfcfb"
CLIENT_FACE = "#eaf1fb"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 11,
    "text.color": INK,
})


def flow_box(ax, cx, cy, w, h, text, face=BOX_FACE):
    box = FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle="round,pad=0.01,rounding_size=0.015",
                          facecolor=face, edgecolor=INK, linewidth=1.3, zorder=3)
    ax.add_patch(box)
    ax.text(cx, cy, text, ha="center", va="center", fontsize=10.5, color=INK, zorder=4)


def arrow(ax, p0, p1, curve=0.0, label=None, label_pos=0.5):
    a = FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=14, color=INK,
                         linewidth=1.3, connectionstyle=f"arc3,rad={curve}", zorder=2)
    ax.add_patch(a)
    if label:
        lx = p0[0] + (p1[0] - p0[0]) * label_pos
        ly = p0[1] + (p1[1] - p0[1]) * label_pos
        ax.text(lx, ly + 0.035, label, ha="center", va="bottom", fontsize=8.3, color=MUTED)


def build():
    fig, ax = plt.subplots(figsize=(12.5, 4.6))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Client subgraph background
    client_box = FancyBboxPatch((0.03, 0.55), 0.30, 0.35, boxstyle="round,pad=0.01,rounding_size=0.015",
                                 facecolor=CLIENT_FACE, edgecolor=MUTED, linewidth=1.0, linestyle="--", zorder=1)
    ax.add_patch(client_box)
    ax.text(0.18, 0.93, "Game client (Unity) -- or simulated (Sec. 3.5)", ha="center", fontsize=9.5,
            color=MUTED, style="italic")

    flow_box(ax, 0.10, 0.72, 0.11, 0.14, "Encounter\nruntime")
    flow_box(ax, 0.24, 0.72, 0.11, 0.14, "Telemetry\nemitter")
    arrow(ax, (0.155, 0.72), (0.185, 0.72))

    flow_box(ax, 0.46, 0.72, 0.17, 0.16, "Learner Model\nService\n(per-KC BKT,\nSec. 3.2)")
    arrow(ax, (0.295, 0.72), (0.375, 0.72), label="encounter\noutcome event")

    flow_box(ax, 0.68, 0.72, 0.17, 0.16, "Difficulty\nController\n(KC priority +\nbandit, Sec. 3.3)")
    arrow(ax, (0.545, 0.72), (0.595, 0.72), label="mastery vector,\nengagement")

    flow_box(ax, 0.90, 0.72, 0.15, 0.16, "Encounter\nConfiguration\n(maps to Unity\nparams)")
    arrow(ax, (0.765, 0.72), (0.825, 0.72), label="next encounter\nspec: (KC, tier)")

    # return arrow to encounter runtime
    arrow(ax, (0.90, 0.64), (0.90, 0.20), curve=0.0)
    arrow(ax, (0.90, 0.20), (0.10, 0.20), curve=0.0, label="enemy stats, spawn rate, hint flag, quiz-bank level", label_pos=0.5)
    arrow(ax, (0.10, 0.20), (0.10, 0.65), curve=0.0)

    fig.tight_layout()
    out_png = os.path.join(OUT_DIR, "figure4_architecture.png")
    out_pdf = os.path.join(OUT_DIR, "figure4_architecture.pdf")
    fig.savefig(out_png, dpi=220, facecolor="white")
    fig.savefig(out_pdf, facecolor="white")
    plt.close(fig)
    print(f"Wrote {out_png} and {out_pdf}")


if __name__ == "__main__":
    build()
