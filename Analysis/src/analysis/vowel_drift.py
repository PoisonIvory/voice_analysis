"""Diagnostic: did a change in the sustained-vowel articulation drive the F0 drift?

Concern (from the participant): partway through the study the sustained vowel was
produced differently (a deliberate "ah" vs "uh" change after reading about cardinal
vowels). A vowel change is an articulatory change and would show up in the formant
frequencies (F1/F2/F3). The worry is that this technique drift is what produced the
slow F0 drift that inflated the raw pitch-estrogen correlation in the main report.

This module tests that hypothesis three ways and renders one figure:
  1. Timing - when did the formants (vowel identity) actually shift, relative to the
     cycle-tracking window and the hormone window?
  2. Independence - inside the hormone window, do the formants move while F0 moves?
  3. Control - does residualizing F0 on the formants remove the F0 drift / the
     F0-estrogen correlation? (If the vowel were the cause, it should.)

It reuses `residualize` for the partial-correlation controls and the shared daily table.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from .config import default_paths
from .residualize import residualize
from .study_figures import ESTROGEN, FOLLICULAR, INK, LUTEAL, _style

F0 = "vowel_egemaps_F0semitoneFrom27.5Hz_sma3nz_amean"
F1 = "vowel_egemaps_F1frequency_sma3nz_amean"
F2 = "vowel_egemaps_F2frequency_sma3nz_amean"
F3 = "vowel_egemaps_F3frequency_sma3nz_amean"
LOUD = "vowel_egemaps_loudness_sma3_amean"

HORMONE_LO = pd.Timestamp("2026-01-22")
HORMONE_HI = pd.Timestamp("2026-03-25")


def vowel_days(df: pd.DataFrame) -> pd.DataFrame:
    v = df[df["has_vowel"] == True].copy().sort_values("date")  # noqa: E712
    v["date_ord"] = v["date"].map(lambda d: d.toordinal())
    return v


def changepoint(series: pd.Series, dates: pd.Series, margin: int = 4) -> tuple[pd.Timestamp, float]:
    """Single best mean-shift split (max |Welch-style t|). Returns (date, t-stat)."""
    s = series.dropna()
    vals = s.to_numpy(float)
    n = len(vals)
    best_i, best_t = None, 0.0
    for i in range(margin, n - margin):
        a, b = vals[:i], vals[i:]
        sp = np.sqrt(((a.var(ddof=1) * (len(a) - 1)) + (b.var(ddof=1) * (len(b) - 1))) / (n - 2))
        t = (b.mean() - a.mean()) / (sp * np.sqrt(1 / len(a) + 1 / len(b))) if sp > 0 else 0.0
        if abs(t) > abs(best_t):
            best_i, best_t = i, t
    return dates.loc[s.index[best_i]], float(best_t)


def _spearman(frame: pd.DataFrame, a: str, b: str) -> tuple[float, int]:
    s = frame[[a, b]].apply(pd.to_numeric, errors="coerce").dropna()
    return (float(stats.spearmanr(s[a], s[b]).statistic), len(s)) if len(s) > 2 else (np.nan, len(s))


def partial_spearman(frame: pd.DataFrame, a: str, b: str, controls: list[str]) -> tuple[float, int]:
    """Spearman of a,b after linearly removing `controls` from both."""
    ra = residualize(frame, a, controls).residual
    rb = residualize(frame, b, controls).residual
    s = pd.DataFrame({"ra": ra, "rb": rb}).dropna()
    return (float(stats.spearmanr(s["ra"], s["rb"]).statistic), len(s)) if len(s) > 2 else (np.nan, len(s))


@dataclass(frozen=True)
class VowelDriftSummary:
    formant_changepoints: dict[str, str]
    settle_date: str                  # when the vowel articulation stabilised (F2 changepoint)
    labeled_days_before_settle: int   # phase-labeled voice days in the unstable-vowel era
    hormone_days_before_settle: int   # voice+hormone days in the unstable era (should be 0)
    window_trends: dict[str, float]   # feature -> rho with date inside hormone window
    f0_date_raw: float
    f0_date_ctrl_formants: float
    f0_estrogen_raw: float
    f0_estrogen_ctrl_formants: float
    f0_estrogen_ctrl_date: float


def summarize(df: pd.DataFrame) -> VowelDriftSummary:
    v = vowel_days(df)
    cps = {name: str(changepoint(v[col], v["date"])[0].date())
           for name, col in [("F1", F1), ("F2", F2), ("F3", F3), ("F0", F0)]}
    win = v[(v["date"] >= HORMONE_LO) & (v["date"] <= HORMONE_HI)]
    trends = {name: _spearman(win, col, "date_ord")[0]
              for name, col in [("F0", F0), ("F1", F1), ("F2", F2), ("F3", F3), ("loudness", LOUD)]}
    settle = pd.Timestamp(cps["F2"])
    before = v["date"] < settle
    return VowelDriftSummary(
        formant_changepoints=cps,
        settle_date=str(settle.date()),
        labeled_days_before_settle=int((before & v["phase_label"].notna()).sum()),
        hormone_days_before_settle=int((before & (v["has_hormones"] == True)).sum()),  # noqa: E712
        window_trends=trends,
        f0_date_raw=_spearman(v, F0, "date_ord")[0],
        f0_date_ctrl_formants=partial_spearman(v, F0, "date_ord", [F1, F2, F3])[0],
        f0_estrogen_raw=_spearman(v, F0, "e3g")[0],
        f0_estrogen_ctrl_formants=partial_spearman(v, F0, "e3g", [F1, F2, F3])[0],
        f0_estrogen_ctrl_date=partial_spearman(v, F0, "e3g", ["date_ord"])[0],
    )


def _zscore(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std(ddof=0)


def fig_vowel_drift(df: pd.DataFrame, summ: VowelDriftSummary, out: Path) -> Path:
    _style()
    v = vowel_days(df)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))

    # Panel A: vowel space (F1 vs F2), split at the settle/changepoint date
    ax = axes[0]
    settle = pd.Timestamp(summ.settle_date)
    early = v[v["date"] < settle]
    late = v[v["date"] >= settle]
    ax.scatter(late[F2], late[F1], c="#8895A7", s=34, alpha=0.7, label="post-shift (settled)")
    ax.scatter(early[F2], early[F1], c=ESTROGEN, s=60, alpha=0.9, edgecolors=INK,
               lw=0.5, label="pre-shift (Sep-Nov)")
    ax.invert_xaxis(); ax.invert_yaxis()  # vowel-chart convention: F1 down, F2 left
    ax.set_xlabel("F2 (Hz)  <- backer | fronter ->")
    ax.set_ylabel("F1 (Hz)  <- closer | opener ->")
    ax.set_title("The vowel moved, then settled")
    ax.legend(fontsize=8, loc="lower left")

    # Panel B: timeline of F0 vs formants (z), changepoint + hormone window shaded
    ax = axes[1]
    ax.axvspan(HORMONE_LO, HORMONE_HI, color=LUTEAL, alpha=0.10, lw=0, label="hormone window")
    ax.plot(v["date"], _zscore(v[F0]), "-o", ms=3.5, lw=1.6, color=INK, label="F0 (pitch)")
    ax.plot(v["date"], _zscore(v[F1]), "-o", ms=3, lw=1.2, color=FOLLICULAR, alpha=0.85, label="F1")
    ax.plot(v["date"], _zscore(v[F2]), "-o", ms=3, lw=1.2, color=ESTROGEN, alpha=0.85, label="F2")
    cp = pd.Timestamp(summ.formant_changepoints["F2"])
    ax.axvline(cp, color="#B23B3B", ls="--", lw=1.4)
    ax.annotate("vowel changepoint", (cp, 2.0), color="#B23B3B", fontsize=8,
                rotation=90, va="top", ha="right")
    ax.axhline(0, color=INK, lw=0.6)
    ax.set_ylabel("within-feature z")
    ax.set_title("Formants step early; F0 drifts later")
    ax.legend(fontsize=7.5, loc="lower left", ncol=2, framealpha=0.9)
    for lab in ax.get_xticklabels():
        lab.set_rotation(30); lab.set_ha("right")

    # Panel C: what actually controls the F0 drift / F0-estrogen link
    ax = axes[2]
    groups = [
        ("F0 ~ date\n(all vowel days)", summ.f0_date_raw, summ.f0_date_ctrl_formants, None),
        ("F0 ~ estrogen\n(hormone window)", summ.f0_estrogen_raw, summ.f0_estrogen_ctrl_formants,
         summ.f0_estrogen_ctrl_date),
    ]
    x = np.arange(len(groups))
    w = 0.26
    ax.bar(x - w, [g[1] for g in groups], w, color="#C7CEDA", label="raw")
    ax.bar(x, [g[2] for g in groups], w, color=ESTROGEN, label="control formants (vowel)")
    ax.bar(x + w, [g[3] if g[3] is not None else np.nan for g in groups], w, color=FOLLICULAR,
           label="control date (time)")
    ax.axhline(0, color=INK, lw=0.8)
    ax.set_xticks(x); ax.set_xticklabels([g[0] for g in groups], fontsize=9)
    ax.set_ylabel("Spearman rho")
    ax.set_title("Time, not vowel, drives F0")
    ax.legend(fontsize=8, loc="lower left")
    ax.grid(axis="x", visible=False)

    fig.suptitle("Did the vowel change drive the F0 drift? No - it settled before the hormone window, and F0 drifts independently",
                 fontsize=12.5, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93), w_pad=2.5)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


if __name__ == "__main__":
    paths = default_paths()
    data = pd.read_parquet(paths.processed_dir / "analysis_daily.parquet")
    summary = summarize(data)
    print("formant changepoints:", summary.formant_changepoints)
    print("vowel settled (F2 changepoint):", summary.settle_date)
    print("phase-labeled days before settle:", summary.labeled_days_before_settle,
          "| hormone days before settle:", summary.hormone_days_before_settle)
    print("within-window trend with date:", {k: round(x, 2) for k, x in summary.window_trends.items()})
    print(f"F0~date:      raw {summary.f0_date_raw:+.2f}  | formants {summary.f0_date_ctrl_formants:+.2f}")
    print(f"F0~estrogen:  raw {summary.f0_estrogen_raw:+.2f}  | formants {summary.f0_estrogen_ctrl_formants:+.2f}"
          f"  | date {summary.f0_estrogen_ctrl_date:+.2f}")

    pd.DataFrame([summary.__dict__]).to_json(paths.outputs_dir / "tables" / "vowel_drift_summary.json",
                                             indent=2)
    p = fig_vowel_drift(data, summary, paths.figures_dir / "fig12_vowel_drift.png")
    print("figure:", p)
