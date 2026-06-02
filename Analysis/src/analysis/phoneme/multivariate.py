"""Does a phoneme-class profile classify the phase of a held-out cycle?

A leave-one-cycle-out nearest-centroid classifier on within-cycle-normalized
day profiles, evaluated against a within-cycle label-shuffling null. Run on the
two phase-balanced cycles (Jan, Feb): a cycle that is almost one phase has no
phase-neutral baseline to normalize against. Comparing the full phoneme profile
to a "global means only" feature set tells us whether phoneme *structure* adds
predictive power over a single recording-wide shift.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .aggregation import BALANCED_CYCLES, within_cycle_z

H1H2_MANNERS = ["vowel", "diphthong", "nasal", "approximant"]  # voiced-only feature
MFCC2_MANNERS = ["vowel", "diphthong", "nasal", "approximant", "stop", "fricative"]


def build_day_profiles(df: pd.DataFrame) -> pd.DataFrame:
    """One row per day (balanced cycles) with per-class means + global means."""
    bal = df[df["cycle_start_date"].astype(str).str[:10].isin(BALANCED_CYCLES)].copy()
    bal = bal[bal["phase_label"].notna()]
    rows = []
    for date, g in bal.groupby("date"):
        row = {"date": date, "phase": g["phase_label"].iloc[0], "cyc": g["cycle_start_date"].iloc[0]}
        for m in H1H2_MANNERS:
            row[f"h1h2_{m}"] = g.loc[g["phonemeManner"] == m, "segment_h1h2_mean"].mean()
        for m in MFCC2_MANNERS:
            row[f"mfcc2_{m}"] = g.loc[g["phonemeManner"] == m, "segment_mfcc2_mean"].mean()
        row["h1h2_global"] = g["segment_h1h2_mean"].mean()
        row["mfcc2_global"] = g["segment_mfcc2_mean"].mean()
        rows.append(row)
    prof = pd.DataFrame(rows)
    feat_cols = [c for c in prof.columns if c.startswith(("h1h2_", "mfcc2_"))]
    for c in feat_cols:
        prof[c] = within_cycle_z(prof.rename(columns={"cyc": "cycle_start_date"}), c, "cycle_start_date")
    return prof


def _balanced_accuracy(profile: pd.DataFrame, cols: list[str], labels: np.ndarray) -> float:
    X = profile[cols].to_numpy(float)
    cyc = profile["cyc"].to_numpy()
    y = labels
    preds = np.empty(len(profile), bool)
    for held in np.unique(cyc):
        tr = cyc != held
        te = ~tr
        cf = X[tr & (~y)].mean(0)
        cl = X[tr & y].mean(0)
        d_l = np.linalg.norm(X[te] - cl, axis=1)
        d_f = np.linalg.norm(X[te] - cf, axis=1)
        preds[te] = d_l < d_f
    tp = ((preds) & y).sum() / max(y.sum(), 1)
    tn = ((~preds) & (~y)).sum() / max((~y).sum(), 1)
    return 0.5 * (tp + tn)


def classify(df: pd.DataFrame, n_perm: int = 5000, seed: int = 1) -> pd.DataFrame:
    prof = build_day_profiles(df)
    feat_cols = [c for c in prof.columns if c.startswith(("h1h2_", "mfcc2_")) and not c.endswith("_global")]
    prof = prof.dropna(subset=feat_cols).reset_index(drop=True)
    y = (prof["phase"] == "luteal").to_numpy()
    cyc = prof["cyc"].to_numpy()
    rng = np.random.default_rng(seed)

    sets = {
        "phoneme_profile": feat_cols,
        "global_means_only": ["h1h2_global", "mfcc2_global"],
        "h1h2_voiced_manner_profile": [c for c in feat_cols if c.startswith("h1h2_")],
        "mfcc2_manner_profile": [c for c in feat_cols if c.startswith("mfcc2_")],
    }
    rows = []
    for name, cols in sets.items():
        obs = _balanced_accuracy(prof, cols, y)
        null = np.empty(n_perm)
        for i in range(n_perm):
            lab = y.copy()
            for c in np.unique(cyc):
                idx = np.where(cyc == c)[0]
                lab[idx] = rng.permutation(lab[idx])
            null[i] = _balanced_accuracy(prof, cols, lab)
        rows.append(
            {
                "feature_set": name,
                "n_features": len(cols),
                "n_days": len(prof),
                "balanced_accuracy": round(float(obs), 3),
                "chance": round(float(null.mean()), 3),
                "p_value": round(float((np.sum(null >= obs) + 1) / (n_perm + 1)), 4),
            }
        )
    return pd.DataFrame(rows)
