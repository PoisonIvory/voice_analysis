"""Thread 2 - two-hormone attribution and the peripheral-vs-central split.

You measured both metabolites daily (E3G, PdG), so each moved feature can be
attributed to estrogen vs progesterone vs their ratio, with slow drift removed
(the raw estrogen->pitch link was mostly shared drift). The peripheral cover
features and the central pitch-control features are then compared: progesterone
acts on both the larynx (peripheral) and, via allopregnanolone/GABA-A, on
auditory-motor pitch control (central); estrogen acts mainly peripherally.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from ..feature_taxonomy import with_task
from ..stats import partial_spearman
from .config import CENTRAL_SET, PERIPHERAL_SET

HORMONES = {"e3g": "Estrogen (E3G)", "pdg": "Progesterone (PdG)", "ep_ratio": "E3G/PdG ratio"}


def _feature_sets() -> list[tuple[str, str, str]]:
    items = []
    for base, label in PERIPHERAL_SET.items():
        items.append(("peripheral", base, label))
    for base, label in CENTRAL_SET.items():
        items.append(("central", base, label))
    return items


def coupling_table(df: pd.DataFrame, task: str) -> pd.DataFrame:
    """Drift-controlled partial Spearman of each feature vs each hormone."""
    rows = []
    for arm, base, label in _feature_sets():
        col = with_task(base, task)
        if col not in df.columns:
            continue
        for hormone in HORMONES:
            if hormone not in df.columns:
                continue
            sub = df[[col, hormone, "day_index"]].dropna()
            n = len(sub)
            if n < 6:
                rows.append({"arm": arm, "feature": base, "label": label, "task": task,
                             "hormone": hormone, "n": n, "raw_rho": np.nan, "partial_rho": np.nan})
                continue
            raw = stats.spearmanr(sub[col], sub[hormone]).statistic
            partial, _ = partial_spearman(sub, col, hormone, "day_index")
            rows.append({"arm": arm, "feature": base, "label": label, "task": task,
                         "hormone": hormone, "n": n, "raw_rho": float(raw), "partial_rho": partial})
    return pd.DataFrame(rows)


def peripheral_vs_central(coupling: pd.DataFrame) -> pd.DataFrame:
    """Mean absolute drift-controlled coupling by arm and hormone."""
    out = (
        coupling.dropna(subset=["partial_rho"])
        .assign(abs_partial=lambda d: d["partial_rho"].abs())
        .groupby(["task", "arm", "hormone"], as_index=False)["abs_partial"]
        .mean()
        .rename(columns={"abs_partial": "mean_abs_partial_rho"})
    )
    return out


def estrogen_periovulatory(df: pd.DataFrame, task: str) -> dict:
    """Estrogen 'best-voice / most-stable' check around the E3G peak.

    Periovulatory = days at/above the within-cycle E3G 75th percentile while PdG
    is still low (pre-luteal). Compares clarity (HNR) and cover stability there
    vs the luteal phase. Directional; hormone window is short.
    """
    hnr = with_task("egemaps_HNRdBACF_sma3nz_amean", task)
    h1h2 = with_task("egemaps_logRelF0-H1-H2_sma3nz_amean", task)
    work = df[df["e3g"].notna() & df["pdg"].notna()].copy()
    if work.empty or hnr not in work.columns:
        return {"task": task, "n_periovulatory": 0, "n_luteal": 0}

    peri_mask = pd.Series(False, index=work.index)
    for _, g in work.groupby("cycle_start_date"):
        if g["e3g"].notna().sum() < 4:
            continue
        thr = g["e3g"].quantile(0.75)
        pdg_lo = g["pdg"].median()
        peri_mask.loc[g.index] = (g["e3g"] >= thr) & (g["pdg"] <= pdg_lo)
    peri = work[peri_mask]
    luteal = work[work["phase_label"] == "luteal"]

    def med(frame, col):
        return float(frame[col].dropna().median()) if col in frame and frame[col].notna().any() else np.nan

    return {
        "task": task,
        "n_periovulatory": int(len(peri)),
        "n_luteal": int(len(luteal)),
        "hnr_periovulatory": med(peri, hnr),
        "hnr_luteal": med(luteal, hnr),
        "h1h2_periovulatory": med(peri, h1h2),
        "h1h2_luteal": med(luteal, h1h2),
    }


def hormone_rates(df: pd.DataFrame) -> pd.DataFrame:
    """Gap-aware daily rate of change of E3G and PdG on measured days."""
    h = df.loc[df["e3g"].notna() | df["pdg"].notna(), ["date", "e3g", "pdg"]].copy()
    h = h.sort_values("date").reset_index(drop=True)
    gap = h["date"].diff().dt.days
    h["e3g_rate"] = h["e3g"].diff() / gap
    h["pdg_rate"] = h["pdg"].diff() / gap
    h["e3g_abs_rate"] = h["e3g_rate"].abs()
    h["pdg_abs_rate"] = h["pdg_rate"].abs()
    return h
