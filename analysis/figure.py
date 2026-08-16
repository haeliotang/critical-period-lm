"""The paper's figure: the decay curves that cross, and the per-seed exponents behind them.

Reads the registered records and recomputes everything from them. No number is typed in
here, so the figure cannot drift from `results/registered/`.

Two panels, because the claim needs both:

**(a)** is the finding as a reader will remember it. Gap to a seed-matched baseline against
budget, both axes logarithmic, so a power law is a straight line and the exponent is a slope.
The early arm starts above the late arm and ends below it; the lines cross. A level measured
at any single budget would have reported whichever side of that crossing it happened to land
on, which is the whole reason the endpoint is a rate.

**(b)** is the part that decides whether to believe (a). Eight seeds per condition, one fitted
exponent each. The late arm's eight sit in a band narrower than the gap to the other sixteen,
so the separation is not one seed's doing — and the control's spread, which is what the
registered margin is three times of, is visible at the same scale. That spread is why the v4
ladder returned `INCONCLUSIVE` on the same effect.

    python analysis/figure.py [v5]
"""

from __future__ import annotations

import json
import math
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from critical_period_lm.decision_rules import (  # noqa: E402
    BASELINE,
    PRIMARY_EARLY,
    PRIMARY_LATE,
    RunRecord,
    fit_exponent,
    paired_gaps,
)

# Validated for colour-vision deficiency and contrast before use: worst adjacent pair
# dE 8.6 (deuteranopia), 27.5 (normal vision), every slot >= 3:1 against the surface.
# All three sit in one lightness band, so print and greyscale are carried by the marker
# and dash, not by tone.
STYLE = {
    "fixed_early_N4": ("#4D8C57", "s", (0, (1, 1.6)), "fixed_early_N4 (control)"),
    PRIMARY_EARLY: ("#2166AC", "o", "solid", "shuffle_early_N4"),
    PRIMARY_LATE: ("#B2182B", "^", (0, (4, 1.8)), "shuffle_late_N4"),
}
ORDER = ["fixed_early_N4", PRIMARY_EARLY, PRIMARY_LATE]

INK, MUTED, GRID = "#1c1c1c", "#5b5b5b", "#d8d8d4"


def power_law(budgets, gaps) -> tuple[float, float]:
    """Exponent and amplitude of `gap = c / T^alpha`."""
    alpha = fit_exponent(budgets, gaps)
    log_c = st.fmean(math.log(g) + alpha * math.log(b) for g, b in zip(gaps, budgets))
    return alpha, math.exp(log_c)


def crossing(fit_a, fit_b) -> float | None:
    """Budget at which two fitted power laws meet, or None if they never do."""
    (alpha_a, c_a), (alpha_b, c_b) = fit_a, fit_b
    if math.isclose(alpha_a, alpha_b):
        return None
    return math.exp((math.log(c_a) - math.log(c_b)) / (alpha_a - alpha_b))


def _panel_curves(ax, budgets, means, fits):
    # The control is drawn as a large open square and the early arm as a filled circle on
    # top of it. They coincide to three decimals, and a circle nested inside a square shows
    # that faster than the legend does.
    sizes = {"fixed_early_N4": (9.5, "none", 1.3), PRIMARY_EARLY: (5.0, None, 0.8),
             PRIMARY_LATE: (5.8, None, 0.8)}
    for condition in ORDER:
        colour, marker, dash, label = STYLE[condition]
        alpha, c = fits[condition]
        size, face, edge_width = sizes[condition]
        smooth = [budgets[0] * (budgets[-1] / budgets[0]) ** (i / 100) for i in range(101)]
        ax.plot(smooth, [c / t**alpha for t in smooth], color=colour, linewidth=1.5,
                linestyle=dash, zorder=2)
        ax.plot(budgets, means[condition], marker=marker, markersize=size, linestyle="none",
                color=colour, markerfacecolor=face if face else colour,
                markeredgecolor=colour if face else "white", markeredgewidth=edge_width,
                zorder=3, label=f"{label}   $\\alpha$ = {alpha:.3f}")

    at = crossing(fits[PRIMARY_EARLY], fits[PRIMARY_LATE])
    if at and budgets[0] < at < budgets[-1] * 4:
        alpha, c = fits[PRIMARY_LATE]
        ax.plot([at], [c / at**alpha], marker="o", markersize=14, markerfacecolor="none",
                markeredgecolor=MUTED, markeredgewidth=1.0, zorder=4)
        ax.annotate(f"the curves cross\n$T \\approx$ {round(at, -2):,.0f}",
                    xy=(at, c / at**alpha), xytext=(0.74, 0.66), textcoords="axes fraction",
                    fontsize=7.5, color=MUTED, ha="center",
                    arrowprops=dict(arrowstyle="-", color=MUTED, linewidth=0.8, shrinkA=2,
                                    shrinkB=8))

    ax.set(xscale="log", yscale="log", xlabel="training budget (optimizer steps)",
           ylabel="gap to seed-matched baseline (nats/token)")
    ax.set_xticks(budgets)
    ax.set_xticklabels([f"{b:,}" for b in budgets])
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_title("(a) damage decays as a power law, at different rates", fontsize=8.5,
                 loc="left", color=INK, pad=8)
    ax.legend(frameon=False, fontsize=7.2, loc="lower left", handletextpad=0.5,
              labelcolor=INK, borderpad=0, borderaxespad=0.2)


def _panel_seeds(ax, per_seed, margin):
    # The registered rule reads a condition as different from the control when its mean
    # exponent differs by more than the margin, so the band is the control's mean plus and
    # minus the whole margin -- crossing its edge is the thing that changed the verdict.
    centre = st.fmean(per_seed["fixed_early_N4"])
    ax.axhspan(centre - margin, centre + margin, color=GRID, alpha=0.5, zorder=0, linewidth=0)
    ax.axhline(centre - margin, color=MUTED, linewidth=0.7, linestyle=(0, (3, 3)), zorder=1)

    for x, condition in enumerate(ORDER):
        colour, marker, _, _ = STYLE[condition]
        values = per_seed[condition]
        jitter = [x + (i - (len(values) - 1) / 2) * 0.052 for i in range(len(values))]
        ax.plot(jitter, values, marker=marker, markersize=5.2, linestyle="none", color=colour,
                markeredgecolor="white", markeredgewidth=0.7, zorder=3)
        ax.plot([x - 0.26, x + 0.26], [st.fmean(values)] * 2, color=colour, linewidth=2.0,
                solid_capstyle="butt", zorder=4)
        ax.annotate(f"{st.fmean(values):.3f}", xy=(x + 0.28, st.fmean(values)), xytext=(2, 0),
                    textcoords="offset points", fontsize=7.2, color=INK, ha="left",
                    va="center")

    top = max(max(v) for v in per_seed.values())
    ax.set_ylim(min(min(v) for v in per_seed.values()) - 0.09, max(top, centre + margin) + 0.13)
    ax.annotate("within the registered margin\nof the control", xy=(-0.40, centre + margin),
                xytext=(0, 5), textcoords="offset points", fontsize=6.9, color=MUTED, ha="left")
    ax.set_xticks(range(len(ORDER)))
    ax.set_xticklabels(["control", "early", "late"], color=INK)
    ax.set_xlim(-0.45, 2.72)
    ax.set_ylabel("fitted decay exponent $\\alpha$ (one per seed)")
    ax.set_title("(b) every seed, not one outlier", fontsize=8.5, loc="left", color=INK, pad=8)


def build(records: list[RunRecord], margin: float):
    gaps = paired_gaps(records)
    budgets = sorted({b for c in gaps for b in gaps[c]})
    means = {c: [st.fmean(gaps[c][b].values()) for b in budgets] for c in ORDER}
    fits = {c: power_law(budgets, means[c]) for c in ORDER}

    seeds = sorted(set.intersection(*(set(gaps[c][budgets[0]]) for c in ORDER)))
    per_seed = {
        c: [fit_exponent(budgets, [gaps[c][b][s] for b in budgets]) for s in seeds] for c in ORDER
    }

    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["STIXGeneral", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": 8,
        "axes.edgecolor": MUTED,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "axes.linewidth": 0.7,
        "figure.facecolor": "white",
    })
    figure, (left, right) = plt.subplots(
        1, 2, figsize=(7.0, 2.9), gridspec_kw={"width_ratios": [1.55, 1], "wspace": 0.30}
    )
    _panel_curves(left, budgets, means, fits)
    _panel_seeds(right, per_seed, margin)
    for ax in (left, right):
        ax.grid(True, which="major", color=GRID, linewidth=0.6, alpha=0.7, zorder=0)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    figure.tight_layout(pad=0.4)
    return figure, fits, per_seed


def main() -> int:
    version = sys.argv[1] if len(sys.argv) > 1 else "v5"
    records = [
        RunRecord(r["condition"], r["seed"], r["final_eval_loss"], r["total_steps"])
        for r in (
            json.loads(p.read_text()) for p in sorted((ROOT / "runs" / version).glob("*/run.json"))
        )
    ]
    if not records:
        print(f"no records under runs/{version}", file=sys.stderr)
        return 1
    report = json.loads((ROOT / "results" / "registered" / version / "report.json").read_text())

    figure, fits, per_seed = build(records, report["exponent_margin"])
    destination = ROOT / "paper" / "figures"
    destination.mkdir(parents=True, exist_ok=True)
    for suffix in ("pdf", "png"):
        figure.savefig(destination / f"decay-{version}.{suffix}", dpi=400,
                       bbox_inches="tight", facecolor="white")

    at = crossing(fits[PRIMARY_EARLY], fits[PRIMARY_LATE])
    print(f"{version}: crossing at T = {at:,.0f}" if at else f"{version}: curves never cross")
    for condition in ORDER:
        alpha, c = fits[condition]
        print(f"  {condition:<20} alpha {alpha:.3f}  amplitude {c:>7.1f}  "
              f"seeds {min(per_seed[condition]):.3f}-{max(per_seed[condition]):.3f}")
    print(f"written to {destination}/decay-{version}.{{pdf,png}}")
    assert BASELINE not in ORDER, "the baseline is the reference, never a plotted condition"
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
