"""Publication figures for the phoneme-prosody study.

Single responsibility: render the figures from the analyzable frame and the
result tables written by run.py. Matplotlib only (no seaborn dependency).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .aggregation import day_series, within_cycle_z
from .config import default_paths
from .load_phonemes import analyzable_segments, clean_recordings, load_phonemes
from .residual_segments import residualize_h1h2_on_f0

FOLL = "#2a9d8f"
LUT = "#e76f51"
SURFACE = "#264653"
TIMBRE = "#8a5a44"
GREY = "#9aa0a6"
WEEK_ORDER = ["week_1", "week_2", "week_3", "week_4", "week_5"]
plt.rcParams.update({"figure.dpi": 130, "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})


def _save(fig, path):
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print("wrote", path)


def fig_coverage(analyzable, clean, paths):
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))
    days = clean.drop_duplicates("date")[["date", "phase_label"]].dropna()
    rec_per_day = clean.groupby("date")["recordingId"].nunique()
    md = rec_per_day.reset_index().merge(clean.drop_duplicates("date")[["date", "phase_label"]], on="date")
    colors = md["phase_label"].map({"follicular": FOLL, "luteal": LUT}).fillna(GREY)
    ax[0].bar(md["date"], md["recordingId"], color=colors, width=3)
    ax[0].set_title("Recordings per day (phase-coloured)")
    ax[0].set_ylabel("recordings")
    ax[0].tick_params(axis="x", rotation=45, labelsize=7)

    manner = analyzable["phonemeManner"].value_counts()
    ax[1].barh(manner.index[::-1], manner.values[::-1], color=SURFACE)
    ax[1].set_title("Analyzable phonemes by manner")
    ax[1].set_xlabel("count")

    day_meta = clean.drop_duplicates("date")[["date", "phase_label", "cycle_start_date"]].dropna(subset=["phase_label"])
    day_meta["cyc"] = day_meta["cycle_start_date"].astype(str).str[:10]
    bal = day_meta.groupby(["cyc", "phase_label"]).size().unstack(fill_value=0)
    bal = bal.reindex(columns=["follicular", "luteal"], fill_value=0)
    idx = np.arange(len(bal))
    ax[2].bar(idx, bal["follicular"], color=FOLL, label="follicular")
    ax[2].bar(idx, bal["luteal"], bottom=bal["follicular"], color=LUT, label="luteal")
    ax[2].set_xticks(idx)
    ax[2].set_xticklabels([c[5:] for c in bal.index], rotation=45, fontsize=7)
    ax[2].set_title("Phase balance by cycle (days)")
    ax[2].set_ylabel("days")
    ax[2].legend(fontsize=8, frameon=False)
    _save(fig, paths.figures_dir / "fig01_coverage.png")


def fig_localization_forest(paths):
    loc = pd.read_csv(paths.tables_dir / "localization.csv")
    sub = loc[(loc.feature == "segment_h1h2_mean") & (loc.class_axis == "phonemeManner")].copy()
    sub = sub.sort_values("cliffs_delta_raw")
    y = np.arange(len(sub))
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.hlines(y, 0, sub["cliffs_delta_raw"], color=GREY, lw=1)
    ax.scatter(sub["cliffs_delta_raw"], y, s=90, color=SURFACE, label="raw (luteal-follicular)", zorder=3)
    ax.scatter(sub["cliffs_delta_demeaned"], y, s=90, facecolors="none", edgecolors=LUT,
               linewidths=2, label="after removing recording-wide offset", zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(sub["phoneme_class"])
    for thr in (0.147, 0.33, 0.474):
        ax.axvline(thr, color="#dddddd", lw=0.8, ls=":")
    ax.axvline(0, color="k", lw=0.8)
    ax.set_xlabel("Cliff's delta (H1-H2, luteal vs follicular)")
    ax.set_title("Where the open-quotient cycle signal lives\n(filled = raw; open = self-normalised). Only diphthongs survive de-meaning.")
    ax.legend(fontsize=8, frameon=False, loc="lower right")
    _save(fig, paths.figures_dir / "fig02_localization_forest.png")


def fig_diphthong_trajectory(analyzable, paths):
    av = residualize_h1h2_on_f0(analyzable)
    rec_mean = av.groupby("recordingId")["h1h2_resid_f0"].transform("mean")
    av["resid_demeaned"] = av["h1h2_resid_f0"] - rec_mean
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))

    # left: diphthong raw H1-H2 within-cycle z by cycle week, pooled over labelled cycles
    diph = day_series(av, "segment_h1h2_mean", subset=(av["phonemeManner"] == "diphthong"))
    diph = diph.dropna(subset=["cycle_week"])
    diph["z"] = within_cycle_z(diph, "segment_h1h2_mean")
    g = diph.groupby("cycle_week")["z"].mean().reindex(WEEK_ORDER).dropna()
    ax[0].plot(range(len(g)), g.values, "-o", color=SURFACE, lw=2)
    ax[0].axhline(0, color=GREY, lw=0.8)
    ax[0].set_xticks(range(len(g)))
    ax[0].set_xticklabels(g.index, rotation=30)
    ax[0].set_ylabel("within-cycle z (SD units)")
    ax[0].set_title("Diphthong H1-H2 rises across the cycle\n(pooled within-cycle z by cycle week)")

    # right: luteal vs follicular distribution of recording-demeaned residual diphthong
    dd = day_series(av, "resid_demeaned", subset=(av["phonemeManner"] == "diphthong"))
    dd = dd.dropna(subset=["phase_label"])
    data = [dd.loc[dd.phase_label == "follicular", "resid_demeaned"],
            dd.loc[dd.phase_label == "luteal", "resid_demeaned"]]
    parts = ax[1].violinplot(data, showmeans=True, showextrema=False)
    for pc, c in zip(parts["bodies"], [FOLL, LUT]):
        pc.set_facecolor(c)
        pc.set_alpha(0.6)
    ax[1].set_xticks([1, 2])
    ax[1].set_xticklabels(["follicular", "luteal"])
    ax[1].axhline(0, color=GREY, lw=0.8)
    ax[1].set_ylabel("F0-residualised, recording-demeaned H1-H2 (dB)")
    ax[1].set_title("Diphthong open-quotient excess vs the speaker's\nown other phonemes (F0-controlled)")
    _save(fig, paths.figures_dir / "fig03_diphthong.png")


def fig_global_vs_control(analyzable, paths):
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    specs = [("segment_mfcc2_mean", "MFCC2 (timbre)", TIMBRE),
             ("segment_h1h2_mean", "H1-H2 (open quotient)", SURFACE),
             ("segment_f1_bandwidth_mean", "F1 bandwidth (damping, control)", GREY)]
    for f, lab, c in specs:
        day = day_series(analyzable, f).dropna(subset=["cycle_week"])
        day["z"] = within_cycle_z(day, f)
        g = day.groupby("cycle_week")["z"].mean().reindex(WEEK_ORDER).dropna()
        ax[0].plot(range(len(g)), g.values, "-o", color=c, lw=2, label=lab)
    ax[0].axhline(0, color="k", lw=0.7)
    ax[0].set_xticks(range(len(WEEK_ORDER)))
    ax[0].set_xticklabels(WEEK_ORDER, rotation=30)
    ax[0].set_ylabel("within-cycle z (SD units)")
    ax[0].set_title("Global feature trajectories across the cycle")
    ax[0].legend(fontsize=8, frameon=False)

    # voiced vs voiceless within-cycle MFCC2 shift (globality of timbre shift)
    rows = []
    for sub_name, mask in [("voiced", analyzable.phonemeVoicing == "voiced"),
                           ("voiceless", analyzable.phonemeVoicing == "voiceless")]:
        day = day_series(analyzable, "segment_mfcc2_mean", subset=mask)
        day["z"] = within_cycle_z(day, "segment_mfcc2_mean")
        cyc = day["cycle_start_date"].astype(str).str[:10]
        for cs, lab in [("2026-01-14", "Jan"), ("2026-02-12", "Feb")]:
            g = day[cyc == cs]
            shift = g.loc[g.phase_label == "luteal", "z"].mean() - g.loc[g.phase_label == "follicular", "z"].mean()
            rows.append((sub_name, lab, shift))
    R = pd.DataFrame(rows, columns=["voicing", "cycle", "shift"])
    piv = R.pivot(index="voicing", columns="cycle", values="shift").reindex(["voiced", "voiceless"])
    x = np.arange(len(piv))
    ax[1].bar(x - 0.2, piv["Jan"], 0.4, color=TIMBRE, label="Jan cycle")
    ax[1].bar(x + 0.2, piv["Feb"], 0.4, color="#c98a6a", label="Feb cycle")
    ax[1].set_xticks(x)
    ax[1].set_xticklabels(piv.index)
    ax[1].axhline(0, color="k", lw=0.7)
    ax[1].set_ylabel("luteal-follicular shift (within-cycle SD)")
    ax[1].set_title("MFCC2 timbre shift is present even in\nvoiceless segments: a global, filter-level change")
    ax[1].legend(fontsize=8, frameon=False)
    _save(fig, paths.figures_dir / "fig04_global_vs_control.png")


def fig_contrasts(paths):
    con = pd.read_csv(paths.tables_dir / "within_recording_contrasts.csv")
    con = con.iloc[::-1]
    y = np.arange(len(con))
    fig, ax = plt.subplots(figsize=(9, 3.8))
    ax.barh(y - 0.2, con["cliffs_delta_phase"], 0.4, color=SURFACE, label="phase Cliff's delta")
    ax.barh(y + 0.2, con["pdg_partial_rho"], 0.4, color=LUT, label="progesterone partial rho")
    ax.set_yticks(y)
    ax.set_yticklabels(con["contrast"], fontsize=8)
    ax.axvline(0, color="k", lw=0.8)
    ax.set_xlabel("effect")
    ax.set_title("Within-recording contrasts are largely flat for phase\n(cycle signal is a global offset); one exploratory progesterone coupling remains")
    ax.legend(fontsize=8, frameon=False, loc="lower right")
    _save(fig, paths.figures_dir / "fig05_contrasts.png")


def fig_multivariate(paths):
    mv = pd.read_csv(paths.tables_dir / "multivariate_classifier.csv")
    order = ["global_means_only", "h1h2_voiced_manner_profile", "mfcc2_manner_profile", "phoneme_profile"]
    mv = mv.set_index("feature_set").reindex(order).reset_index()
    y = np.arange(len(mv))
    fig, ax = plt.subplots(figsize=(8.5, 3.6))
    ax.barh(y, mv["balanced_accuracy"], color=[GREY, SURFACE, TIMBRE, "#1d3557"])
    ax.axvline(0.5, color="k", lw=0.8, ls="--", label="chance")
    for i, r in mv.iterrows():
        ax.text(r["balanced_accuracy"] + 0.01, i, f"acc={r['balanced_accuracy']:.2f}, p={r['p_value']:.3f}",
                va="center", fontsize=8)
    ax.set_yticks(y)
    ax.set_yticklabels([s.replace("_", " ") for s in mv["feature_set"]], fontsize=8)
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("balanced accuracy (held-out cycle)")
    ax.set_title("Held-out-cycle phase classification from the phoneme profile")
    ax.legend(fontsize=8, frameon=False, loc="lower right")
    _save(fig, paths.figures_dir / "fig06_multivariate.png")


def fig_phoneme_heatmap(analyzable, paths):
    """Level 3: individual phoneme x cycle-week heatmap of within-cycle z (H1-H2)."""
    sub = analyzable[analyzable["phonemeVoicing"] == "voiced"].dropna(
        subset=["segment_h1h2_mean", "cycle_week"]
    ).copy()
    keep = sub["phonemeLabel"].value_counts()
    keep = keep[keep >= 120].index  # well-sampled, reliably-voiced phonemes only
    sub = sub[sub["phonemeLabel"].isin(keep)]
    rows = []
    for lab, g in sub.groupby("phonemeLabel"):
        day = day_series(g, "segment_h1h2_mean")
        day = day.dropna(subset=["cycle_week"])
        if day["cycle_start_date"].nunique() < 2:
            continue
        day["z"] = within_cycle_z(day, "segment_h1h2_mean")
        wk = day.groupby("cycle_week")["z"].mean().reindex(WEEK_ORDER)
        rows.append(pd.Series(wk.values, index=WEEK_ORDER, name=lab))
    M = pd.DataFrame(rows)
    M = M.loc[M.mean(axis=1).sort_values().index]
    fig, ax = plt.subplots(figsize=(7.5, max(4, 0.28 * len(M))))
    im = ax.imshow(M.values, aspect="auto", cmap="RdBu_r", vmin=-1.2, vmax=1.2)
    ax.set_xticks(range(len(WEEK_ORDER)))
    ax.set_xticklabels(WEEK_ORDER, rotation=30)
    ax.set_yticks(range(len(M)))
    ax.set_yticklabels(M.index, fontsize=7)
    ax.set_title("Per-phoneme H1-H2 across the cycle (within-cycle z)")
    fig.colorbar(im, ax=ax, label="z (SD units)", shrink=0.7)
    _save(fig, paths.figures_dir / "fig07_phoneme_heatmap.png")


def main():
    paths = default_paths()
    paths.figures_dir.mkdir(parents=True, exist_ok=True)
    raw = load_phonemes(paths)
    clean = clean_recordings(raw)
    analyzable = analyzable_segments(raw)
    fig_coverage(analyzable, clean, paths)
    fig_localization_forest(paths)
    fig_diphthong_trajectory(analyzable, paths)
    fig_global_vs_control(analyzable, paths)
    fig_contrasts(paths)
    fig_multivariate(paths)
    fig_phoneme_heatmap(analyzable, paths)


if __name__ == "__main__":
    main()
