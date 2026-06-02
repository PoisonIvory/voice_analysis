"""Generic F0/loudness-residualized cycle test for any voice feature.

Some acoustic features (H1-H2, HNR) plausibly co-vary with pitch (F0) and vocal
intensity (loudness). If a cycle-phase difference in such a feature were really a
re-description of an F0 or loudness difference between phases, it would be a
mechanical artifact rather than a vocal-fold tissue property. This module factors
out that confound: it regresses a target feature on F0 and loudness, then re-runs
the phase-contrast and hormone-coupling lenses on the residual.

It is the engine behind `h1h2_residual` and `hnr_residual`; the only thing that
changes between features is the `ResidualSpec`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .analysis_dataset import build_analysis_table
from .residualize import residualize
from . import stats as st

F0 = "egemaps_F0semitoneFrom27.5Hz_sma3nz_amean"
LOUDNESS = "egemaps_loudness_sma3_amean"
TASKS = ("vowel", "prosody")

FOLLICULAR = "#2BA3E8"
LUTEAL = "#5E4DB3"
RAW = "#C7CEDA"
RESID = "#30A37A"
INK = "#1A1E2E"
GRID = "#D8DCE6"


@dataclass(frozen=True)
class ResidualSpec:
    target_base: str          # eGeMAPS base name (no task prefix)
    label: str                # short display label, e.g. "H1-H2" or "HNR"
    resid_key: str            # column-safe id, e.g. "H1H2" or "HNR"
    unit: str = ""            # y-axis unit text for the figure
    covariate_bases: tuple[str, ...] = (F0, LOUDNESS)
    fig_task: str = "prosody"  # task shown in the phase-gap panel


def _col(base: str, task: str) -> str:
    return f"{task}_{base}"


def resid_col(spec: ResidualSpec, task: str) -> str:
    return f"{task}_{spec.resid_key}_resid_f0_loud"


def build_residual_table(spec: ResidualSpec) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (analysis_table_with_residuals, coupling_compare, context_table)."""
    df = build_analysis_table()
    df["date_ord"] = df["date"].map(lambda d: d.toordinal() if pd.notna(d) else np.nan)
    voice = df[df["has_voice"]].copy()

    context_rows: list[dict] = []
    coupling_rows: list[dict] = []

    for task in TASKS:
        target = _col(spec.target_base, task)
        covs = [_col(b, task) for b in spec.covariate_bases]
        if target not in df.columns or not all(c in df.columns for c in covs):
            continue

        per_cov = {b: residualize(voice, target, [_col(b, task)]) for b in spec.covariate_bases}
        both = residualize(voice, target, covs)

        sub = voice[[target, *covs]].apply(pd.to_numeric, errors="coerce").dropna()
        row = dict(task=task, n_voice_days=len(sub), target_sd=float(sub[target].std()),
                   r2_all_covariates=both.r_squared)
        for b in spec.covariate_bases:
            short = "f0" if b == F0 else "loudness" if b == LOUDNESS else b
            row[f"r2_{short}_only"] = per_cov[b].r_squared
        context_rows.append(row)

        df[resid_col(spec, task)] = both.residual

        for variant, col in [("raw", target), ("residual", resid_col(spec, task))]:
            labeled = df[df["phase_label"].notna() & df["has_voice"]]
            pc = st.phase_contrast(labeled, col)
            hv = df[df["has_voice"] & df["has_hormones"]]
            for horm, horm_label in [("pdg", "Progesterone (PdG)"), ("e3g", "Estrogen (E3G)")]:
                hc = st.hormone_coupling(hv, col, horm, n_boot=2000)
                partial, _ = st.partial_spearman(hv, col, horm, "date_ord")
                coupling_rows.append(dict(
                    feature=spec.label, task=task, variant=variant, hormone=horm_label,
                    cliffs_delta=pc.cliffs_delta, cliffs_magnitude=pc.magnitude,
                    luteal_minus_follicular=pc.delta_luteal_minus_follicular,
                    phase_p=pc.mann_whitney_p,
                    cycles_consistent=pc.cycles_consistent, cycles_total=pc.cycles_total,
                    n_hormone=hc.n, raw_rho=hc.spearman_rho,
                    boot_lo=hc.boot_lo, boot_hi=hc.boot_hi, partial_rho_date=partial,
                ))

    return df, pd.DataFrame(coupling_rows), pd.DataFrame(context_rows)


def _style() -> None:
    plt.rcParams.update({
        "figure.dpi": 150, "savefig.dpi": 150, "font.size": 11,
        "axes.titlesize": 12, "axes.titleweight": "bold", "axes.labelsize": 10,
        "axes.edgecolor": "#9AA3B2", "axes.linewidth": 0.8, "axes.grid": True,
        "grid.color": GRID, "grid.linewidth": 0.7, "axes.axisbelow": True,
        "text.color": INK, "axes.labelcolor": INK, "xtick.color": INK,
        "ytick.color": INK, "figure.facecolor": "white", "axes.facecolor": "white",
    })


def render_figure(df: pd.DataFrame, context: pd.DataFrame, coupling: pd.DataFrame,
                  spec: ResidualSpec, out: Path) -> Path:
    _style()
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.6))

    # Panel A: how much target variance F0 / loudness / both explain, per task.
    ax = axes[0]
    y = np.arange(len(context))
    h = 0.26
    ax.barh(y + h, context["r2_f0_only"], height=h, color="#E8913B", label="F0 only")
    ax.barh(y, context["r2_loudness_only"], height=h, color="#8895A7", label="Loudness only")
    ax.barh(y - h, context["r2_all_covariates"], height=h, color=INK, label="F0 + loudness")
    ax.set_yticks(y)
    ax.set_yticklabels([t.capitalize() for t in context["task"]])
    ax.set_xlabel(f"Share of daily {spec.label} variance explained (R\u00b2)")
    ax.set_title(f"How much of {spec.label} is pitch/intensity?")
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(axis="y", visible=False)

    # Panel B: phase separation, raw vs residual, for the chosen task.
    ax = axes[1]
    task = spec.fig_task
    raw_c, res_c = _col(spec.target_base, task), resid_col(spec, task)
    labeled = df[df["phase_label"].notna() & df["has_voice"]]
    positions, data, colors, ticks = [], [], [], []
    for i, (col, name) in enumerate([(raw_c, f"Raw {spec.label}"),
                                     (res_c, "Residual\n(F0+loud removed)")]):
        for j, ph in enumerate(["follicular", "luteal"]):
            vals = pd.to_numeric(labeled.loc[labeled["phase_label"] == ph, col], errors="coerce").dropna()
            pos = i * 2.4 + j
            positions.append(pos); data.append(vals.to_numpy())
            colors.append(FOLLICULAR if ph == "follicular" else LUTEAL)
        ticks.append((i * 2.4 + 0.5, name))
    bp = ax.boxplot(data, positions=positions, widths=0.7, patch_artist=True,
                    showfliers=False, medianprops=dict(color=INK, lw=1.5))
    for patch, c in zip(bp["boxes"], colors):
        patch.set_facecolor(c); patch.set_alpha(0.45)
    for pos, vals, c in zip(positions, data, colors):
        ax.scatter(np.random.normal(pos, 0.05, len(vals)), vals, s=12, color=INK, alpha=0.35, zorder=3)
    ax.set_xticks([t[0] for t in ticks])
    ax.set_xticklabels([t[1] for t in ticks], fontsize=9)
    ax.set_ylabel(f"{spec.label}{(' (' + spec.unit + ')') if spec.unit else ''} - {task}")
    ax.set_title("Phase gap survives residualization")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor=FOLLICULAR, alpha=0.45, label="Follicular"),
                       Patch(facecolor=LUTEAL, alpha=0.45, label="Luteal")],
              fontsize=8, loc="best")
    ax.grid(axis="x", visible=False)

    # Panel C: Cliff's delta (luteal vs follicular) raw vs residual, both tasks.
    ax = axes[2]
    cd = coupling[coupling["hormone"] == "Progesterone (PdG)"].drop_duplicates(["task", "variant"])
    tasks = list(TASKS)
    raw_vals = [cd[(cd.task == t) & (cd.variant == "raw")]["cliffs_delta"].iloc[0] for t in tasks]
    res_vals = [cd[(cd.task == t) & (cd.variant == "residual")]["cliffs_delta"].iloc[0] for t in tasks]
    y = np.arange(len(tasks))
    ax.barh(y + 0.2, raw_vals, height=0.38, color=RAW, label=f"Raw {spec.label}")
    ax.barh(y - 0.2, res_vals, height=0.38, color=RESID, label=f"Residual {spec.label}")
    ax.axvline(0, color=INK, lw=0.8)
    ax.set_yticks(y); ax.set_yticklabels([t.capitalize() for t in tasks])
    ax.set_xlabel("Cliff's delta (luteal vs follicular)")
    ax.set_title("Effect size: raw vs residual")
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(axis="y", visible=False)

    fig.suptitle(f"F0/loudness-residualized {spec.label}: the cycle signal is not a pitch or intensity artifact",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def run(spec: ResidualSpec, table_prefix: str, fig_name: str) -> dict:
    """Compute, save tables + figure, print a summary. Returns the result frames."""
    from .config import default_paths

    paths = default_paths()
    df, coupling, context = build_residual_table(spec)

    tables_dir = paths.outputs_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    context.to_csv(tables_dir / f"{table_prefix}_context.csv", index=False)
    coupling.to_csv(tables_dir / f"{table_prefix}_coupling.csv", index=False)
    fig_path = render_figure(df, context, coupling, spec, paths.figures_dir / fig_name)

    pd.set_option("display.width", 170)
    pd.set_option("display.max_columns", 30)
    print(f"=== CONTEXT: F0/loudness explained variance for {spec.label} ===")
    print(context.to_string(index=False))
    print(f"\n=== CYCLE SIGNAL: raw {spec.label} vs F0/loudness-residual ===")
    print(coupling.to_string(index=False))
    print(f"\nfigure: {fig_path}")
    return {"df": df, "coupling": coupling, "context": context}
