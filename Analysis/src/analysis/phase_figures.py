"""Renders figures for the within-cycle phase lens (the second analysis).

Consumes `phase_lens` outputs so the figures and the companion report stay
consistent. Reuses the first study's brand palette and light theme.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import feature_taxonomy as tax
from . import phase_lens as pl
from .study_figures import FAMILY_COLORS, FOLLICULAR, GRID, INK, LUTEAL, _style

WEEK_ORDER = ["week_1", "week_2", "week_3", "week_4"]
WEEK_LABELS = ["Wk 1\n(menses)", "Wk 2\n(late foll.)", "Wk 3\n(early luteal)", "Wk 4\n(late luteal)"]

# Pre-specified trajectory features (chosen by mechanism, not by the data).
# Each gets a distinct colour so overlapping same-family lines stay readable.
TRAJECTORY = [
    ("egemaps_HNRdBACF_sma3nz_amean", "prosody", "HNR / clarity (speech)", "#2BA3E8", "-"),
    ("egemaps_alphaRatioV_sma3nz_amean", "vowel", "Alpha ratio / tilt (vowel)", "#E8913B", "-"),
    ("egemaps_mfcc2V_sma3nz_amean", "prosody", "MFCC2 / timbre (speech)", "#5E4DB3", "-"),
    ("egemaps_F2frequency_sma3nz_amean", "vowel", "F2 frequency / geometry (vowel)", "#8895A7", ":"),
]


def fig_shift_forest(shift_table: pd.DataFrame, out: Path, top: int = 14) -> Path:
    _style()
    block = shift_table.head(top).iloc[::-1].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(11, 6.2))
    y = np.arange(len(block))
    for i, row in block.iterrows():
        color = FAMILY_COLORS.get(row["family"], "#888")
        ax.plot([0, row["pooled_shift_z"]], [i, i], color=color, lw=2.2, alpha=0.5, zorder=1)
        ax.scatter(row["pooled_shift_z"], i, color=color, s=70, zorder=3)
        ax.annotate(f"{row['cycles_concordant']}/{row['cycles_total']}",
                    (row["pooled_shift_z"], i), fontsize=7.5, color=INK,
                    ha="left" if row["pooled_shift_z"] < 0 else "right",
                    va="center", xytext=(6 if row["pooled_shift_z"] < 0 else -6, 0),
                    textcoords="offset points")
    ax.axvline(0, color=INK, lw=0.9)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{r.feature} ({r.task})" for r in block.itertuples()], fontsize=8.5)
    ax.set_xlabel("Within-cycle shift, luteal - follicular  (SD units)   ·   point labels = cycles agreeing on direction")
    ax.set_title("Once cross-cycle drift is removed, the phase signal sharpens")
    ax.grid(axis="y", visible=False)
    from matplotlib.lines import Line2D
    handles = [Line2D([0], [0], marker="o", color="w", markerfacecolor=c, markersize=9,
                      label=tax.FAMILY_LABELS[k]) for k, c in FAMILY_COLORS.items()]
    ax.legend(handles=handles, loc="lower right", fontsize=8, frameon=True, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def fig_family_magnitude(family_summary: pd.DataFrame, out: Path) -> Path:
    _style()
    order = ["Surface / damping (mucosa & closure)", "Spectral envelope / timbre (MFCC)",
             "Source pitch (fold mass/tension)", "Geometric (vocal-tract shape)"]
    fam_key = {v: k for k, v in tax.FAMILY_LABELS.items()}
    s = family_summary.set_index("family_label").reindex(order)
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    colors = [FAMILY_COLORS[fam_key[lbl]] for lbl in order]
    ax.barh(np.arange(len(order))[::-1], s["mean_abs"], color=colors, alpha=0.9, height=0.6)
    for i, lbl in enumerate(order[::-1]):
        ax.text(s.loc[lbl, "mean_abs"] + 0.01, i, f"{s.loc[lbl, 'mean_abs']:.2f}",
                va="center", fontsize=9, color=INK)
    ax.set_yticks(np.arange(len(order))[::-1])
    ax.set_yticklabels([lbl.split(" (")[0] for lbl in order], fontsize=9)
    ax.set_xlabel("Mean |within-cycle phase shift|  (SD units)")
    ax.set_title("Where the cycle lives in the voice: surface & timbre move, geometry holds")
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def fig_week_trajectory(df: pd.DataFrame, out: Path) -> Path:
    _style()
    traj = pd.concat([pl.week_trajectory(df, [b for b, t, _, _, _ in TRAJECTORY if t == task], task)
                      for task in ("vowel", "prosody")], ignore_index=True)
    fig, ax = plt.subplots(figsize=(9.5, 5))
    xs = np.arange(len(WEEK_ORDER))
    for base, task, label, color, ls in TRAJECTORY:
        sub = traj[(traj["base"] == base) & (traj["task"] == task)].set_index("cycle_week").reindex(WEEK_ORDER)
        ax.errorbar(xs, sub["mean"], yerr=sub["sem"], marker="o", ms=6, lw=2, ls=ls,
                    color=color, capsize=3, label=label, alpha=0.95)
    ax.axhline(0, color=INK, lw=0.8)
    ax.axvspan(1.5, 3.5, color=LUTEAL, alpha=0.07, lw=0)
    ax.axvspan(-0.5, 1.5, color=FOLLICULAR, alpha=0.07, lw=0)
    ax.set_xticks(xs)
    ax.set_xticklabels(WEEK_LABELS, fontsize=9)
    ax.set_ylabel("Within-cycle z  (pooled across 4 cycles)")
    ax.set_title("The voice traces a repeatable arc across the cycle")
    ax.legend(fontsize=8.5, loc="upper left", framealpha=0.9)
    ax.text(0.985, 0.03, "blue = follicular weeks   purple = luteal weeks", transform=ax.transAxes,
            fontsize=8, color="#6B7280", ha="right")
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def fig_separability(results: dict, out: Path) -> Path:
    _style()
    signal = results["Surface + timbre (mechanism signal)"]
    control = results["Geometry only (negative control)"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))

    ax = axes[0]
    ax.axvspan(0, signal.null_p95, color="#C7CEDA", alpha=0.5, label="null 95% (chance)")
    ax.axvline(signal.null_mean, color="#6B7280", lw=1.4, ls="--", label=f"null mean {signal.null_mean:.2f}")
    ax.axvline(signal.balanced_accuracy, color=LUTEAL, lw=2.6,
               label=f"observed {signal.balanced_accuracy:.2f}")
    ax.axvline(0.5, color=INK, lw=0.8)
    ax.set_xlim(0.2, 0.95)
    ax.set_yticks([])
    ax.set_xlabel("Leave-one-cycle-out balanced accuracy")
    ax.set_title(f"Phase is readable from the voice\n(p = {signal.p_value:.3f})", fontsize=11)
    ax.legend(fontsize=8.5, loc="upper left")

    ax = axes[1]
    names = ["Surface +\ntimbre", "Geometry\n(control)"]
    accs = [signal.balanced_accuracy, control.balanced_accuracy]
    ax.bar(names, accs, color=[LUTEAL, "#8895A7"], alpha=0.9, width=0.55)
    ax.axhline(0.5, color=INK, lw=0.9, ls="--")
    ax.text(1.5, 0.515, "chance", fontsize=8, color=INK, ha="right")
    for i, a in enumerate(accs):
        ax.text(i, a + 0.02, f"{a:.2f}", ha="center", fontsize=10, color=INK)
    ax.set_ylim(0, 0.9)
    ax.set_ylabel("Balanced accuracy")
    ax.set_title("Signal vs negative control", fontsize=11)
    ax.grid(axis="x", visible=False)

    fig.suptitle("A multivariate phase signature that generalises to a held-out cycle",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def render_all(df: pd.DataFrame, figures_dir: Path, n_perm: int = 2000) -> dict[str, Path]:
    figures_dir.mkdir(parents=True, exist_ok=True)
    shift_table = pl.phase_shift_table(df)
    family_summary = pl.family_shift_summary(shift_table)
    _, sep_results = pl.separability_table(df, n_perm=n_perm)
    return {
        "shift_forest": fig_shift_forest(shift_table, figures_dir / "phase_fig01_shift_forest.png"),
        "family_magnitude": fig_family_magnitude(family_summary, figures_dir / "phase_fig02_family_magnitude.png"),
        "week_trajectory": fig_week_trajectory(df, figures_dir / "phase_fig03_week_trajectory.png"),
        "separability": fig_separability(sep_results, figures_dir / "phase_fig04_separability.png"),
    }


if __name__ == "__main__":
    from .config import default_paths

    paths = default_paths()
    data = pd.read_parquet(paths.processed_dir / "analysis_daily.parquet")

    tables_dir = paths.outputs_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    shift = pl.phase_shift_table(data)
    shift.to_csv(tables_dir / "phase_within_cycle_shift.csv", index=False)
    pl.family_shift_summary(shift).to_csv(tables_dir / "phase_family_magnitude.csv", index=False)
    sep_tbl, _ = pl.separability_table(data, n_perm=2000)
    sep_tbl.to_csv(tables_dir / "phase_separability.csv", index=False)

    rendered = render_all(data, paths.figures_dir)
    for name, p in rendered.items():
        print(f"{name}: {p}")
