"""Publication figures for the HuBERT phonological-subspace cycle study.

Single responsibility: render four figures from the loaded d-prime frame and the
result tables written by run.py. Matplotlib only, matching the phoneme study's
visual style.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ..phoneme.aggregation import day_series, within_cycle_z
from .config import PRIMARY_BACKBONE, default_paths
from .load_dprime import load_dprime, primary
from .taxonomy import COMPOSITE_CONSONANT, USABLE_CONTRASTS, dprime_col, label

FOLL = "#2a9d8f"
LUT = "#e76f51"
SURFACE = "#264653"
GREY = "#9aa0a6"
BACKBONE_COLORS = {"hubert-base": "#264653", "wavlm-base": "#2a9d8f", "wav2vec2-base": "#e9c46a"}
WEEK_ORDER = ["week_1", "week_2", "week_3", "week_4", "week_5"]
plt.rcParams.update(
    {"figure.dpi": 130, "font.size": 10, "axes.spines.top": False, "axes.spines.right": False}
)


def _save(fig, path):
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print("wrote", path)


def fig_coverage(prim: pd.DataFrame, paths):
    fig, ax = plt.subplots(1, 2, figsize=(11.5, 3.8))

    # left: per-contrast token counts (pos+neg), median with min-max range.
    keys = USABLE_CONTRASTS
    med, lo, hi = [], [], []
    for k in keys:
        total = prim[f"n_{k}_pos"] + prim[f"n_{k}_neg"]
        med.append(total.median())
        lo.append(total.median() - total.min())
        hi.append(total.max() - total.median())
    y = np.arange(len(keys))
    ax[0].barh(y, med, xerr=[lo, hi], color=SURFACE, alpha=0.85, error_kw={"ecolor": GREY, "lw": 1})
    ax[0].axvline(5, color=LUT, lw=1, ls="--", label="5-token minimum")
    ax[0].set_yticks(y)
    ax[0].set_yticklabels([label(k) for k in keys], fontsize=8)
    ax[0].set_xlabel("tokens per recording (pos + neg)")
    ax[0].set_title("Fixed passage keeps tokens near-constant\n(token-count confound removed at source)")
    ax[0].legend(fontsize=8, frameon=False, loc="lower right")

    # right: phase balance by cycle (days).
    days = prim.drop_duplicates("date")[["date", "phase_label", "cycle_start_date"]].dropna(
        subset=["phase_label"]
    )
    days["cyc"] = days["cycle_start_date"].astype(str).str[:10]
    bal = days.groupby(["cyc", "phase_label"]).size().unstack(fill_value=0)
    bal = bal.reindex(columns=["follicular", "luteal"], fill_value=0)
    idx = np.arange(len(bal))
    ax[1].bar(idx, bal["follicular"], color=FOLL, label="follicular")
    ax[1].bar(idx, bal["luteal"], bottom=bal["follicular"], color=LUT, label="luteal")
    ax[1].set_xticks(idx)
    ax[1].set_xticklabels([c[5:] for c in bal.index], rotation=45, fontsize=7)
    ax[1].set_title("Phase balance by cycle (days)")
    ax[1].set_ylabel("days")
    ax[1].legend(fontsize=8, frameon=False)
    _save(fig, paths.figures_dir / "fig01_coverage.png")


def fig_phase_forest(paths):
    phase = pd.read_csv(paths.tables_dir / "phase_contrasts.csv")
    order = [COMPOSITE_CONSONANT] + [dprime_col(k) for k in USABLE_CONTRASTS]
    labels = ["Consonant composite"] + [label(k) for k in USABLE_CONTRASTS]
    y = np.arange(len(order))[::-1]
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    for backbone, g in phase.groupby("backbone"):
        g = g.set_index("feature").reindex(order)
        ax.scatter(
            g["cliffs_delta"], y, s=70 if backbone == PRIMARY_BACKBONE else 40,
            color=BACKBONE_COLORS.get(backbone, GREY),
            edgecolors="k" if backbone == PRIMARY_BACKBONE else "none",
            linewidths=0.6, alpha=0.9, label=backbone, zorder=3,
        )
    for thr in (0.147, 0.33, 0.474):
        for s in (-1, 1):
            ax.axvline(s * thr, color="#dddddd", lw=0.8, ls=":")
    ax.axvline(0, color="k", lw=0.9)
    ax.axhline(len(order) - 1.5, color="#cccccc", lw=0.8)  # separate composite
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlim(-0.7, 0.7)
    ax.set_xlabel("Cliff's delta (luteal - follicular), day grain")
    ax.set_title(
        "Phonological separability is stable across the cycle\n"
        "No contrast survives BH-FDR in any backbone (dotted = small/medium/large bands)"
    )
    ax.legend(fontsize=8, frameon=False, loc="lower right", title="backbone")
    _save(fig, paths.figures_dir / "fig02_phase_forest.png")


def fig_privileged_spotlight(prim: pd.DataFrame, paths):
    fig, ax = plt.subplots(1, 2, figsize=(11.5, 3.9))

    # left: within-cycle-week trajectory for the two cycle-privileged contrasts.
    specs = [(dprime_col("nasality"), "Nasality", SURFACE), (dprime_col("voicing"), "Voicing", LUT)]
    for feature, lab, c in specs:
        day = day_series(prim, feature).dropna(subset=["cycle_week"])
        day["z"] = within_cycle_z(day, feature)
        g = day.groupby("cycle_week")["z"].mean().reindex(WEEK_ORDER).dropna()
        ax[0].plot(range(len(g)), g.values, "-o", color=c, lw=2, label=lab)
    ax[0].axhline(0, color="k", lw=0.7)
    ax[0].set_xticks(range(len(WEEK_ORDER)))
    ax[0].set_xticklabels(WEEK_ORDER, rotation=30)
    ax[0].set_ylabel("within-cycle z (SD units)")
    ax[0].set_title("Cycle-privileged contrasts across the cycle\n(no systematic luteal shift)")
    ax[0].legend(fontsize=8, frameon=False)

    # right: date-partial hormone coupling for composite + privileged contrasts.
    horm = pd.read_csv(paths.tables_dir / "hormone_coupling.csv")
    feats = [COMPOSITE_CONSONANT, dprime_col("nasality"), dprime_col("voicing")]
    flabels = ["composite", "nasality", "voicing"]
    x = np.arange(len(feats))
    pdg = [horm[(horm.feature == f) & (horm.hormone == "pdg")]["date_partial_rho"].iloc[0] for f in feats]
    e3g = [horm[(horm.feature == f) & (horm.hormone == "e3g")]["date_partial_rho"].iloc[0] for f in feats]
    ax[1].bar(x - 0.2, pdg, 0.4, color=LUT, label="progesterone (PdG)")
    ax[1].bar(x + 0.2, e3g, 0.4, color=FOLL, label="estrogen (E3G)")
    ax[1].axhline(0, color="k", lw=0.7)
    ax[1].set_xticks(x)
    ax[1].set_xticklabels(flabels)
    ax[1].set_ylabel("date-partial Spearman rho")
    ax[1].set_ylim(-0.5, 0.5)
    ax[1].set_title("Drift-controlled hormone coupling\n(nasality leans negative with PdG; all n.s.)")
    ax[1].legend(fontsize=8, frameon=False)
    _save(fig, paths.figures_dir / "fig03_privileged_spotlight.png")


def fig_robustness(df: pd.DataFrame, paths):
    fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.0))

    # left: per-recording composite agreement, HuBERT-base vs the other two.
    wide = df.pivot_table(index="recordingId", columns="backbone", values=COMPOSITE_CONSONANT)
    rho = pd.read_csv(paths.tables_dir / "inter_backbone_rho.csv")
    for other, c in [("wavlm-base", FOLL), ("wav2vec2-base", "#e9c46a")]:
        sub = wide[[PRIMARY_BACKBONE, other]].dropna()
        r = rho[(rho.backbone_a.isin([PRIMARY_BACKBONE, other])) & (rho.backbone_b.isin([PRIMARY_BACKBONE, other]))]
        rval = float(r["spearman_rho"].iloc[0]) if len(r) else float("nan")
        ax[0].scatter(sub[PRIMARY_BACKBONE], sub[other], s=28, color=c, alpha=0.8,
                      label=f"{other} (rho={rval:.2f})")
    ax[0].set_xlabel("HuBERT-base composite d-prime")
    ax[0].set_ylabel("other backbone composite d-prime")
    ax[0].set_title("Per-recording composite agreement\n(little to rank: one speaker, fixed passage)")
    ax[0].legend(fontsize=8, frameon=False, loc="upper left")

    # right: consonant-profile cosine across backbone pairs (shape agreement).
    cos = pd.read_csv(paths.tables_dir / "profile_cosine.csv")
    pair = cos["backbone_a"].str.replace("-base", "") + " / " + cos["backbone_b"].str.replace("-base", "")
    yy = np.arange(len(cos))[::-1]
    ax[1].barh(yy, cos["profile_cosine"], color=SURFACE, alpha=0.85)
    for i, v in zip(yy, cos["profile_cosine"]):
        ax[1].text(v - 0.01, i, f"{v:.3f}", va="center", ha="right", color="white", fontsize=9)
    ax[1].set_yticks(yy)
    ax[1].set_yticklabels(pair, fontsize=8)
    ax[1].set_xlim(0.9, 1.0)
    ax[1].set_xlabel("cosine similarity of mean consonant d-prime profile")
    ax[1].set_title("Profile shape is architecture-independent\n(cosine > 0.95 across all pairs)")
    _save(fig, paths.figures_dir / "fig04_robustness.png")


def main():
    paths = default_paths()
    paths.figures_dir.mkdir(parents=True, exist_ok=True)
    df = load_dprime(paths)
    prim = primary(df)
    fig_coverage(prim, paths)
    fig_phase_forest(paths)
    fig_privileged_spotlight(prim, paths)
    fig_robustness(df, paths)


if __name__ == "__main__":
    main()
