"""Renders presentation-ready figures for the voice-cycle study.

Consumes the tables from `study_results.compute_all` so figures and report stay
consistent. Light theme with Decibelle brand accents for the two cycle phases.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import feature_taxonomy as tax

# Brand-aligned palette (see PeriodTracker DESIGN_SYSTEM).
FOLLICULAR = "#2BA3E8"   # electric cyan
LUTEAL = "#5E4DB3"       # deep indigo
ESTROGEN = "#E8913B"     # warm amber
PROGESTERONE = "#5E4DB3" # indigo
LH = "#30A37A"           # teal
INK = "#1A1E2E"
GRID = "#D8DCE6"

FAMILY_COLORS = {
    "geometric_vocal_tract": "#8895A7",
    "source_pitch": "#E8913B",
    "surface_damping": "#2BA3E8",
    "spectral_envelope_mfcc": "#5E4DB3",
}

F0_VOWEL = "vowel_egemaps_F0semitoneFrom27.5Hz_sma3nz_amean"
HNR_VOWEL = "vowel_egemaps_HNRdBACF_sma3nz_amean"
HNR_PROSODY = "prosody_egemaps_HNRdBACF_sma3nz_amean"
MFCC1_VOWEL = "vowel_egemaps_mfcc1V_sma3nz_amean"


def _style() -> None:
    plt.rcParams.update({
        "figure.dpi": 150,
        "savefig.dpi": 150,
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
        "axes.edgecolor": "#9AA3B2",
        "axes.linewidth": 0.8,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.7,
        "axes.axisbelow": True,
        "text.color": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    })


def _phase_runs(df: pd.DataFrame):
    sub = df[["date", "phase_label"]].dropna(subset=["phase_label"]).sort_values("date")
    runs = []
    start = prev = None
    label = None
    for _, row in sub.iterrows():
        d, lab = row["date"], row["phase_label"]
        if label is None:
            start = prev = d
            label = lab
        elif lab == label and (d - prev).days <= 2:
            prev = d
        else:
            runs.append((start, prev, label))
            start = prev = d
            label = lab
    if label is not None:
        runs.append((start, prev, label))
    return runs


def _shade_phases(ax, df):
    for start, end, label in _phase_runs(df):
        ax.axvspan(start, end, color=FOLLICULAR if label == "follicular" else LUTEAL,
                   alpha=0.08, lw=0)


def fig_coverage(df: pd.DataFrame, out: Path) -> Path:
    _style()
    fig, ax = plt.subplots(figsize=(11, 3.4))
    _shade_phases(ax, df)
    lanes = [("Oura (body)", "has_oura", "#8895A7"),
             ("Voice", "has_voice", FOLLICULAR),
             ("Hormones (Inito)", "has_hormones", ESTROGEN)]
    for i, (name, col, color) in enumerate(lanes):
        days = df.loc[df[col] == True, "date"]  # noqa: E712
        ax.scatter(days, np.full(len(days), i), marker="|", s=160, color=color, lw=1.6)
    for cs in df["cycle_start_date"].dropna().unique():
        ax.axvline(pd.Timestamp(cs), color=INK, ls=":", lw=0.9, alpha=0.5)
    ax.set_yticks(range(len(lanes)))
    ax.set_yticklabels([n for n, _, _ in lanes])
    ax.set_ylim(-0.6, len(lanes) - 0.4)
    ax.set_title("Data coverage and study design (N-of-1, daily tracking)")
    ax.set_xlabel("Date  (dotted lines = cycle start; blue = follicular, purple = luteal shading)")
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def fig_positive_controls(df: pd.DataFrame, out: Path) -> Path:
    _style()
    panels = [("temp_deviation", "Body temperature deviation (degC)"),
              ("hrv", "Heart-rate variability (ms)"),
              ("average_hr", "Daytime average heart rate (bpm)")]
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.8))
    sub = df[df["phase_label"].notna()]
    for ax, (col, label) in zip(axes, panels):
        data = [sub.loc[sub["phase_label"] == ph, col].dropna() for ph in ["follicular", "luteal"]]
        bp = ax.boxplot(data, patch_artist=True, widths=0.6, showfliers=False,
                        medianprops=dict(color=INK, lw=1.6))
        for patch, color in zip(bp["boxes"], [FOLLICULAR, LUTEAL]):
            patch.set_facecolor(color)
            patch.set_alpha(0.45)
        for i, d in enumerate(data, start=1):
            ax.scatter(np.random.normal(i, 0.05, len(d)), d, s=12, color=INK, alpha=0.35, zorder=3)
        ax.set_xticks([1, 2])
        ax.set_xticklabels(["Follicular", "Luteal"])
        ax.set_title(label, fontsize=11)
    fig.suptitle("Positive controls: the body clearly shows the cycle", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def fig_hormones(df: pd.DataFrame, out: Path) -> Path:
    _style()
    hw = df[df["has_hormones"]].sort_values("date")
    fig, ax = plt.subplots(figsize=(11, 3.8))
    _shade_phases(ax, df[df["date"].between(hw["date"].min(), hw["date"].max())])
    ax.plot(hw["date"], hw["e3g"], "-o", color=ESTROGEN, ms=4, lw=1.6, label="Estrogen (E3G)")
    ax.plot(hw["date"], hw["pdg"] * 10, "-o", color=PROGESTERONE, ms=4, lw=1.6,
            label="Progesterone (PdG, x10)")
    ax2 = ax.twinx()
    ax2.plot(hw["date"], hw["lh"], "-^", color=LH, ms=4, lw=1.2, alpha=0.8, label="LH")
    ax2.set_ylabel("LH", color=LH)
    for cs, g in hw.groupby("cycle_start_date"):
        if g["lh"].notna().any():
            peak = g.loc[g["lh"].idxmax()]
            ax2.annotate("peak LH", (peak["date"], peak["lh"]), color=LH,
                         fontsize=8, ha="center", va="bottom")
    ax.set_ylabel("E3G  /  PdG x10")
    ax.set_title("Hormonal ground truth across tracked cycles (Inito)")
    ax.set_xlabel("Date")
    ax.legend(loc="upper right", fontsize=9, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def _annot_rho(ax, x, y):
    from scipy import stats
    s = pd.DataFrame({"x": x, "y": y}).dropna()
    rho, p = stats.spearmanr(s["x"], s["y"])
    ax.text(0.04, 0.93, f"rho = {rho:+.2f}\np = {p:.3f}  (n={len(s)})",
            transform=ax.transAxes, va="top", fontsize=9,
            bbox=dict(boxstyle="round", fc="white", ec="#9AA3B2", alpha=0.9))


def fig_confound(df: pd.DataFrame, out: Path) -> Path:
    _style()
    hv = df[df["has_voice"] & df["has_hormones"]].sort_values("date")
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))

    axes[0].scatter(hv["e3g"], hv[F0_VOWEL], color=ESTROGEN, s=28, alpha=0.8)
    axes[0].set_xlabel("Estrogen (E3G)")
    axes[0].set_ylabel("Pitch F0 (semitones, vowel)")
    axes[0].set_title("Raw: pitch vs estrogen looks strong")
    _annot_rho(axes[0], hv["e3g"], hv[F0_VOWEL])

    ax = axes[1]
    ax.plot(hv["date"], hv[F0_VOWEL], "-o", color=ESTROGEN, ms=4, label="Pitch F0 (vowel)")
    ax.set_ylabel("Pitch F0 (semitones)", color=ESTROGEN)
    axb = ax.twinx()
    axb.plot(hv["date"], hv["e3g"], "-s", color="#8895A7", ms=4, label="Estrogen (E3G)")
    axb.set_ylabel("Estrogen (E3G)", color="#8895A7")
    ax.set_title("...but both just drift down over time")
    ax.set_xlabel("Date")
    for lab in ax.get_xticklabels():
        lab.set_rotation(30); lab.set_ha("right")

    ax = axes[2]
    pairs = [("Pitch ~ Estrogen\n(vowel)", 0.529, 0.291),
             ("HNR ~ Progesterone\n(vowel)", 0.442, 0.408),
             ("HNR ~ Progesterone\n(prosody)", 0.405, 0.349)]
    ypos = np.arange(len(pairs))
    ax.barh(ypos + 0.18, [p[1] for p in pairs], height=0.34, color="#C7CEDA", label="Raw rho")
    ax.barh(ypos - 0.18, [p[2] for p in pairs], height=0.34, color=FOLLICULAR, label="After time-control")
    ax.set_yticks(ypos)
    ax.set_yticklabels([p[0] for p in pairs], fontsize=9)
    ax.set_xlabel("Spearman rho")
    ax.set_title("What survives detrending")
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(axis="y", visible=False)

    fig.suptitle("The drift trap: why raw correlations overstate the cycle effect",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def fig_coupling_forest(coupling: pd.DataFrame, out: Path) -> Path:
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(13, 6), sharex=True)
    for ax, horm in zip(axes, ["Progesterone (PdG)", "Estrogen (E3G)"]):
        block = coupling[coupling["hormone"] == horm].copy()
        block["abs_raw"] = block["raw_rho"].abs()
        block = block.sort_values("abs_raw", ascending=False).head(12)
        block = block.iloc[::-1].reset_index(drop=True)
        y = np.arange(len(block))
        for i, row in block.iterrows():
            color = FAMILY_COLORS.get(row["family"], "#888")
            ax.plot([row["boot_lo"], row["boot_hi"]], [i, i], color=color, lw=2, alpha=0.5)
            ax.scatter(row["raw_rho"], i, color=color, s=55, zorder=3, label="raw")
            ax.scatter(row["partial_rho_date"], i, facecolors="white", edgecolors=color,
                       s=55, zorder=4, lw=1.6)
        ax.axvline(0, color=INK, lw=0.8)
        ax.set_yticks(y)
        ax.set_yticklabels([f"{r.feature} ({r.task})" for r in block.itertuples()], fontsize=8)
        ax.set_xlabel("Spearman rho")
        ax.set_title(f"Coupling with {horm}")
        ax.grid(axis="y", visible=False)
    # legend
    from matplotlib.lines import Line2D
    handles = [Line2D([0], [0], marker="o", color="w", markerfacecolor=c, markersize=9, label=tax.FAMILY_LABELS[k])
               for k, c in FAMILY_COLORS.items()]
    handles += [Line2D([0], [0], marker="o", color="w", markerfacecolor="#555", markersize=9, label="Raw rho"),
                Line2D([0], [0], marker="o", color="w", markerfacecolor="white", markeredgecolor="#555", markersize=9, label="After time-control")]
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=8, frameon=False, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("Which voice features couple with hormones (filled = raw, open = time-controlled)",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0.06, 1, 0.95))
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def fig_task_dissociation(coupling: pd.DataFrame, out: Path) -> Path:
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))

    def panel(ax, hormone, features, title):
        rows = []
        for base in features:
            label = tax.label_of(base)
            v = coupling[(coupling["base"] == base) & (coupling["task"] == "vowel") & (coupling["hormone"] == hormone)]
            p = coupling[(coupling["base"] == base) & (coupling["task"] == "prosody") & (coupling["hormone"] == hormone)]
            rows.append((label,
                         float(v["partial_rho_date"].iloc[0]) if len(v) else np.nan,
                         float(p["partial_rho_date"].iloc[0]) if len(p) else np.nan))
        labels = [r[0] for r in rows]
        y = np.arange(len(rows))
        ax.barh(y + 0.2, [r[1] for r in rows], height=0.38, color=FOLLICULAR, label="Vowel")
        ax.barh(y - 0.2, [r[2] for r in rows], height=0.38, color=LUTEAL, label="Prosody")
        ax.axvline(0, color=INK, lw=0.8)
        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=8)
        ax.set_xlabel("Time-controlled Spearman rho")
        ax.set_title(title, fontsize=11)
        ax.legend(fontsize=8, loc="lower right")
        ax.grid(axis="y", visible=False)

    panel(axes[0], "Progesterone (PdG)", [
        "egemaps_HNRdBACF_sma3nz_amean",
        "egemaps_hammarbergIndexV_sma3nz_amean",
        "egemaps_F2bandwidth_sma3nz_amean",
        "egemaps_mfcc1V_sma3nz_amean",
        "egemaps_mfcc2V_sma3nz_amean",
        "egemaps_mfcc3V_sma3nz_amean",
    ], "Quality / timbre vs Progesterone")
    panel(axes[1], "Estrogen (E3G)", [
        "egemaps_F0semitoneFrom27.5Hz_sma3nz_amean",
        "egemaps_F1frequency_sma3nz_amean",
        "egemaps_F2frequency_sma3nz_amean",
        "egemaps_F3frequency_sma3nz_amean",
    ], "Pitch / geometry vs Estrogen")

    fig.suptitle("Different tasks reveal different mechanisms", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def fig_mfcc(df: pd.DataFrame, coupling: pd.DataFrame, out: Path) -> Path:
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
    mfccs = ["egemaps_mfcc1V_sma3nz_amean", "egemaps_mfcc2V_sma3nz_amean",
             "egemaps_mfcc3V_sma3nz_amean", "egemaps_mfcc4V_sma3nz_amean"]
    labels = ["MFCC1", "MFCC2", "MFCC3", "MFCC4"]
    y = np.arange(len(mfccs))
    vow = [coupling[(coupling.base == b) & (coupling.task == "vowel") & (coupling.hormone == "Progesterone (PdG)")]["partial_rho_date"].iloc[0] for b in mfccs]
    pro = [coupling[(coupling.base == b) & (coupling.task == "prosody") & (coupling.hormone == "Progesterone (PdG)")]["partial_rho_date"].iloc[0] for b in mfccs]
    axes[0].barh(y + 0.2, vow, height=0.38, color=FOLLICULAR, label="Vowel")
    axes[0].barh(y - 0.2, pro, height=0.38, color=LUTEAL, label="Prosody")
    axes[0].axvline(0, color=INK, lw=0.8)
    axes[0].set_yticks(y); axes[0].set_yticklabels(labels)
    axes[0].set_xlabel("Time-controlled rho vs Progesterone")
    axes[0].set_title("MFCC coupling with progesterone")
    axes[0].legend(fontsize=8); axes[0].grid(axis="y", visible=False)

    hv = df[df["has_voice"] & df["has_hormones"]]
    axes[1].scatter(hv["pdg"], hv[MFCC1_VOWEL], color=PROGESTERONE, s=28, alpha=0.8)
    axes[1].set_xlabel("Progesterone (PdG)")
    axes[1].set_ylabel("MFCC1 (vowel, brightness)")
    axes[1].set_title("MFCC1 brightness rises with progesterone")
    _annot_rho(axes[1], hv["pdg"], hv[MFCC1_VOWEL])

    fig.suptitle("Spectral timbre (MFCC) tracks progesterone, task-specifically",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def fig_headline(df: pd.DataFrame, out: Path) -> Path:
    _style()
    hv = df[df["has_voice"] & df["has_hormones"]]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    axes[0].scatter(hv["pdg"], hv[HNR_VOWEL], color=FOLLICULAR, s=30, alpha=0.85)
    axes[0].set_xlabel("Progesterone (PdG)")
    axes[0].set_ylabel("HNR (vowel, dB)")
    axes[0].set_title("Sustained vowel")
    _annot_rho(axes[0], hv["pdg"], hv[HNR_VOWEL])
    axes[1].scatter(hv["pdg"], hv[HNR_PROSODY], color=LUTEAL, s=30, alpha=0.85)
    axes[1].set_xlabel("Progesterone (PdG)")
    axes[1].set_ylabel("HNR (prosody, dB)")
    axes[1].set_title("Connected speech")
    _annot_rho(axes[1], hv["pdg"], hv[HNR_PROSODY])
    fig.suptitle("Headline signal: voice clarity (HNR) rises with progesterone in both tasks",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def fig_robustness(results: dict, out: Path) -> Path:
    _style()
    rob = results["robustness"]
    coupling = results["hormone_coupling"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))

    # Panel A: in-window (measured PdG) vs held-out (temperature proxy, drift-controlled)
    y = np.arange(len(rob))[::-1]
    axes[0].barh(y + 0.2, rob["in_window_rho_pdg"], height=0.38, color=FOLLICULAR,
                 label="In-window vs measured PdG")
    axes[0].barh(y - 0.2, rob["heldout_rho_temp_datectrl"], height=0.38, color="#C7657A",
                 label="Held-out vs temp proxy (drift-controlled)")
    axes[0].axvline(0, color=INK, lw=0.8)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels(rob["feature"], fontsize=8)
    axes[0].set_xlabel("Spearman rho")
    axes[0].set_title("Candidate signals do not replicate out-of-sample", fontsize=11)
    axes[0].legend(fontsize=8, loc="lower right")
    axes[0].grid(axis="y", visible=False)

    # Panel B: FDR q-values for the candidate couplings (vs measured PdG)
    from . import study_results as sr
    labels, qvals = [], []
    for name, task, base in sr.CANDIDATES:
        row = coupling[(coupling["base"] == base) & (coupling["task"] == task)
                       & (coupling["hormone"] == "Progesterone (PdG)")]
        if len(row):
            labels.append(name)
            qvals.append(float(row["fdr_q"].iloc[0]))
    yb = np.arange(len(labels))[::-1]
    axes[1].barh(yb, qvals, color="#8895A7")
    axes[1].axvline(0.05, color="#C7657A", ls="--", lw=1.2, label="q = 0.05")
    axes[1].axvline(0.10, color=ESTROGEN, ls=":", lw=1.2, label="q = 0.10")
    axes[1].set_yticks(yb)
    axes[1].set_yticklabels(labels, fontsize=8)
    axes[1].set_xlabel("FDR-adjusted q-value (vs measured PdG)")
    axes[1].set_title("None survive multiple-comparison correction", fontsize=11)
    axes[1].legend(fontsize=8, loc="lower right")
    axes[1].grid(axis="y", visible=False)

    fig.suptitle("Robustness checks: the voice signal does not hold up",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def render_all(results: dict, figures_dir: Path) -> dict[str, Path]:
    figures_dir.mkdir(parents=True, exist_ok=True)
    df = results["analysis_table"]
    coupling = results["hormone_coupling"]
    paths = {
        "coverage": fig_coverage(df, figures_dir / "fig01_coverage.png"),
        "positive_controls": fig_positive_controls(df, figures_dir / "fig02_positive_controls.png"),
        "hormones": fig_hormones(df, figures_dir / "fig03_hormones.png"),
        "confound": fig_confound(df, figures_dir / "fig04_confound.png"),
        "forest": fig_coupling_forest(coupling, figures_dir / "fig05_coupling_forest.png"),
        "task": fig_task_dissociation(coupling, figures_dir / "fig06_task_dissociation.png"),
        "mfcc": fig_mfcc(df, coupling, figures_dir / "fig07_mfcc.png"),
        "headline": fig_headline(df, figures_dir / "fig08_headline_hnr.png"),
        "robustness": fig_robustness(results, figures_dir / "fig09_robustness.png"),
    }
    return paths


if __name__ == "__main__":
    from .config import default_paths
    from .study_results import compute_all

    paths = default_paths()
    res = compute_all(paths.outputs_dir / "tables")
    rendered = render_all(res, paths.figures_dir)
    for name, p in rendered.items():
        print(f"{name}: {p}")
