"""Figures for the SupeRR Selector report.

Palettes are the ones validated with the dataviz validator:
  - sequential RR-pink ramp (monotonic L 0.94 -> 0.46) for ordered pressure bands
  - categorical slots 1-3 (#2a78d6/#eb6834/#1baf7a) for model variants
Charts are single-axis throughout; where a fill sits below 3:1 contrast on the
page the bar carries a visible direct label, which is the documented relief.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)
DATA = ROOT.parent / "dashboard" / "src" / "data"

SEQ = ["#fde4f0", "#f9b8d8", "#f286bb", "#e6499a", "#d11a76", "#9e0d56"]
CAT = ["#2a78d6", "#eb6834", "#1baf7a"]
RR = "#d11a76"
INK = "#14142b"
MUTED = "#6b6b86"
GRID = "#e4e4ed"
SURFACE = "#ffffff"

plt.rcParams.update({
    "font.family": "Helvetica Neue",
    "font.size": 9.5,
    "axes.edgecolor": GRID,
    "axes.labelcolor": MUTED,
    "text.color": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.facecolor": SURFACE,
    "figure.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
})

diag = json.load(open(DATA / "diagnostics.json"))
press = diag["pressure"]
models = diag["models"]
relb = diag["ratings"]["reliability_batting"]["metrics"]
rell = diag["ratings"]["reliability_bowling"]["metrics"]
pbat = json.load(open(DATA / "players_bat.json"))
pbowl = json.load(open(DATA / "players_bowl.json"))


def style(ax, ylabel=None, show_y=True):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=8.5, labelpad=8)
    if not show_y:
        ax.set_yticklabels([])


def save(fig, name):
    fig.savefig(FIG / name, dpi=220, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    print(f"  {name}")


# --- Fig 1: outcomes across pressure bands (three single-axis panels) --------
def fig_bands():
    b = press["batting_by_pi"]
    labels = [r["band"] for r in b]
    panels = [
        ("run_rate", "Run rate (runs per over)", "barely moves"),
        ("wkt_per_100", "Dismissals per 100 balls", "doubles"),
        ("runs_per_dismissal", "Runs per dismissal", "halves"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(11.2, 3.3))
    for ax, (key, title, note) in zip(axes, panels):
        vals = [r[key] for r in b]
        bars = ax.bar(labels, vals, color=SEQ, width=0.72,
                      edgecolor=SURFACE, linewidth=1.6)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, v, f"{v:.1f}",
                    ha="center", va="bottom", fontsize=8.5,
                    color=INK, fontweight="bold")
        ax.set_title(title, fontsize=9.5, color=INK, fontweight="bold",
                     loc="left", pad=26)
        ax.text(0, 1.035, note, transform=ax.transAxes, fontsize=8.5,
                color=RR, fontweight="bold")
        ax.set_ylim(0, max(vals) * 1.25)
        style(ax)
        ax.tick_params(axis="x", labelsize=8, rotation=35)
    fig.text(0.5, -0.06, "Pressure Index band  ·  light = calm, dark = extreme",
             ha="center", fontsize=8.5, color=MUTED)
    save(fig, "f1_bands.png")


# --- Fig 2: within-phase control -------------------------------------------
def fig_phase():
    order = ["1-6", "7-11", "12-15", "16-17", "18-20"]
    wb = press["batting_within_phase"]
    wl = press["bowling_within_phase"]

    def pick(rows, terc, key):
        return [next(r[key] for r in rows if r["ovb"] == p and r["terc"] == terc)
                for p in order]

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 3.5))
    specs = [
        (axes[0], pick(wb, "low", "runs_per_dismissal"),
         pick(wb, "high", "runs_per_dismissal"),
         "Batting — runs per dismissal", "{:.0f}"),
        (axes[1], pick(wl, "low", "run_rate"), pick(wl, "high", "run_rate"),
         "Bowling — runs conceded per over", "{:.1f}"),
    ]
    x = range(len(order))
    for ax, lo, hi, title, fm in specs:
        w = 0.37
        b1 = ax.bar([i - w / 2 - 0.01 for i in x], lo, w, label="Low pressure",
                    color=SEQ[1], edgecolor=SURFACE, linewidth=1.6)
        b2 = ax.bar([i + w / 2 + 0.01 for i in x], hi, w, label="High pressure",
                    color=SEQ[4], edgecolor=SURFACE, linewidth=1.6)
        for bars in (b1, b2):
            for bar in bars:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                        fm.format(bar.get_height()), ha="center", va="bottom",
                        fontsize=7.8, color=INK)
        ax.set_xticks(list(x))
        ax.set_xticklabels([f"Ov {p}" for p in order], fontsize=8.5)
        ax.set_title(title, fontsize=9.5, color=INK, fontweight="bold",
                     loc="left", pad=10)
        ax.set_ylim(0, max(max(lo), max(hi)) * 1.22)
        style(ax)
        ax.legend(frameon=False, fontsize=8.5, loc="upper right", ncol=2,
                  handlelength=1.1, columnspacing=1.0)
    save(fig, "f2_phase.png")


# --- Fig 3: robustness by index variant ------------------------------------
def fig_robust():
    order = ["1-6", "7-11", "12-15", "16-17", "18-20"]
    rob = press["robustness"]
    series = [("Full index", "full_index", CAT[0]),
              ("Without build-up", "without_buildup", CAT[1]),
              ("Leverage only", "leverage_only", CAT[2])]
    fig, ax = plt.subplots(figsize=(11.2, 3.5))
    x = range(len(order))
    w = 0.26
    for i, (label, key, color) in enumerate(series):
        vals = [rob[key][p] for p in order]
        off = (i - 1) * (w + 0.015)
        bars = ax.bar([j + off for j in x], vals, w, label=label, color=color,
                      edgecolor=SURFACE, linewidth=1.6)
        # Direct labels are the documented relief for the aqua slot's contrast.
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    v - 1.4 if v < 0 else v + 0.6,
                    f"{v:+.1f}" if abs(v) < 1 else f"{v:+.0f}",
                    ha="center", va="top" if v < 0 else "bottom",
                    fontsize=7.6, color=INK)
    ax.axhline(0, color=MUTED, lw=1)
    lo = min(rob[k][p] for _, k, _ in series for p in order)
    hi = max(rob[k][p] for _, k, _ in series for p in order)
    ax.set_ylim(lo - 7, hi + 4)
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"Overs {p}" for p in order], fontsize=8.5)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:+.0f}%"))
    ax.set_title("Change in runs per dismissal, top vs bottom pressure tercile, within phase",
                 fontsize=9.5, color=INK, fontweight="bold", loc="left", pad=26)
    ax.text(0, 1.035, "more negative = the index separates harder situations more sharply",
            transform=ax.transAxes, fontsize=8.5, color=MUTED)
    style(ax)
    ax.legend(frameon=False, fontsize=8.5, ncol=3, loc="lower right",
              bbox_to_anchor=(1.0, 1.0), handlelength=1.1)
    save(fig, "f3_robust.png")


# --- Fig 4: split-half reliability -----------------------------------------
def fig_reliability():
    rows = [("Overall impact", "overall"), ("Pressure impact", "press"),
            ("Clutch premium", "clutch"), ("Match consistency", "pos_rate")]
    bat = [relb[k]["full_length_r"] for _, k in rows]
    bowl = [rell[k]["full_length_r"] for _, k in rows]
    fig, ax = plt.subplots(figsize=(8.6, 3.0))
    y = range(len(rows))
    h = 0.36
    b1 = ax.barh([i + h / 2 + 0.01 for i in y], bat, h, label="Batting",
                 color=CAT[0], edgecolor=SURFACE, linewidth=1.6)
    b2 = ax.barh([i - h / 2 - 0.01 for i in y], bowl, h, label="Bowling",
                 color=CAT[1], edgecolor=SURFACE, linewidth=1.6)
    for bars in (b1, b2):
        for bar in bars:
            ax.text(bar.get_width() + 0.008, bar.get_y() + bar.get_height() / 2,
                    f"{bar.get_width():.2f}", va="center", fontsize=8,
                    color=INK)
    ax.axvline(0.3, color=MUTED, lw=1, ls=(0, (3, 3)))
    ax.text(0.305, len(rows) - 0.35, "durable skill", fontsize=8, color=MUTED)
    ax.set_yticks(list(y))
    ax.set_yticklabels([r[0] for r in rows], fontsize=9, color=INK)
    ax.set_xlim(0, 0.56)
    ax.set_xlabel("Split-half reliability (Spearman–Brown corrected)", fontsize=8.5)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.xaxis.grid(True, color=GRID, lw=0.8)
    ax.yaxis.grid(False)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8.5, loc="upper right", handlelength=1.1)
    save(fig, "f4_reliability.png")


# --- Fig 5/6: pressure vs calm dumbbells for the two shortlists -------------
def fig_dumbbell(profiles, name, title):
    top = sorted([p for p in profiles if p.get("consensus_rank")],
                 key=lambda p: p["consensus_rank"])[:10]
    top = top[::-1]
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    for i, p in enumerate(top):
        a, b = p["impact_calm"], p["impact_press"]
        up = b >= a
        ax.plot([a, b], [i, i], color=SEQ[2] if up else "#c9c9d6", lw=2.6,
                solid_capstyle="round", zorder=1)
        ax.scatter([a], [i], s=52, color="#ffffff", edgecolor=MUTED,
                   linewidth=1.6, zorder=2)
        ax.scatter([b], [i], s=72, color=RR if up else "#eda100",
                   edgecolor=SURFACE, linewidth=1.4, zorder=3)
        ax.text(max(a, b) + 0.022, i, f"{b:+.2f}", va="center", fontsize=8,
                color=INK, fontweight="bold")
    ax.axvline(0, color=MUTED, lw=1)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels([f"{p['consensus_rank']}. {p['name']}" for p in top],
                       fontsize=9, color=INK)
    ax.set_xlabel("Runs added per delivery vs what the situation normally yields",
                  fontsize=8.5)
    ax.set_title(title, fontsize=10, color=INK, fontweight="bold", loc="left",
                 pad=30)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.xaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    xs = [p["impact_calm"] for p in top] + [p["impact_press"] for p in top]
    ax.set_xlim(min(0, min(xs)) - 0.06, max(xs) + 0.12)
    handles = [
        plt.Line2D([], [], marker="o", ls="", markerfacecolor="#ffffff",
                   markeredgecolor=MUTED, markersize=7, label="Calm"),
        plt.Line2D([], [], marker="o", ls="", color=RR, markersize=8,
                   label="Under pressure (lifts)"),
        plt.Line2D([], [], marker="o", ls="", color="#eda100", markersize=8,
                   label="Under pressure (dips)"),
    ]
    ax.set_ylim(-0.7, len(top) - 0.3)
    ax.legend(handles=handles, frameon=False, fontsize=8.5, ncol=3,
              loc="lower right", bbox_to_anchor=(1.0, 1.005),
              handletextpad=0.3, columnspacing=1.2)
    save(fig, name)


# --- Fig 7: chase win-probability calibration -------------------------------
def fig_calibration():
    cal = models["inn2"]["calibration"]
    fig, ax = plt.subplots(figsize=(4.6, 4.2))
    ax.plot([0, 100], [0, 100], color=MUTED, lw=1, ls=(0, (4, 4)), zorder=1)
    xs = [c["pred"] * 100 for c in cal]
    ys = [c["obs"] * 100 for c in cal]
    ns = [c["n"] for c in cal]
    mx = max(ns)
    ax.scatter(xs, ys, s=[40 + 240 * (n / mx) for n in ns], color=RR,
               alpha=0.85, edgecolor=SURFACE, linewidth=1.4, zorder=2)
    ax.set_xlabel("Predicted win probability", fontsize=8.5)
    ax.set_ylabel("Observed win rate", fontsize=8.5)
    ax.set_xlim(-4, 104)
    ax.set_ylim(-4, 104)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_title("Chase model calibration", fontsize=9.5, color=INK,
                 fontweight="bold", loc="left", pad=26)
    ax.text(0, 1.035, f"{models['inn2']['n']:,} deliveries · Brier {models['inn2']['brier']:.3f}",
            transform=ax.transAxes, fontsize=8.5, color=MUTED)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    save(fig, "f7_calibration.png")


if __name__ == "__main__":
    print("figures:")
    fig_bands()
    fig_phase()
    fig_robust()
    fig_reliability()
    fig_dumbbell(pbat, "f5_bat.png", "Top 10 batters — calm standard vs pressure output")
    fig_dumbbell(pbowl, "f6_bowl.png", "Top 10 bowlers — calm standard vs pressure output")
    fig_calibration()
