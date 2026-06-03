"""Thread 1 - the mean dissociation: cover moves, geometry is spared.

Single-case dissociation logic (after Crawford & Garthwaite 2005), implemented
with a within-cycle phase-label permutation null suited to an N-of-1 repeated-
measures design, plus an equivalence test (TOST-style, after Lakens 2018) that
turns "geometry did not move" into evidence of absence rather than absence of
evidence. All effects are Cliff's delta on within-cycle-normalized day values.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..feature_taxonomy import with_task
from ..stats import cliffs_delta, cliffs_magnitude
from .config import FAMILIES, FAMILY_LABELS, MOVED_CHANNEL, SPARED_CHANNEL, BALANCED_CYCLE_STARTS
from .dataset import _balanced_mask

SESOI = 0.147  # Cliff's delta "negligible/small" boundary = smallest effect of interest


def _zmatrix(df: pd.DataFrame, features: list[str], task: str) -> pd.DataFrame:
    """Per-day frame for balanced cycles with each feature z-scored within cycle."""
    sub = df.loc[_balanced_mask(df, BALANCED_CYCLE_STARTS)].copy()
    sub = sub.dropna(subset=["phase_label"]).reset_index(drop=True)
    out = sub[["cycle_start_date", "phase_label"]].copy()
    for base in features:
        col = with_task(base, task)
        z = pd.Series(np.nan, index=sub.index, dtype=float)
        if col in sub.columns:
            for _, g in sub.groupby("cycle_start_date"):
                vals = g[col]
                present = vals.dropna()
                n_f = int((sub.loc[present.index, "phase_label"] == "follicular").sum())
                n_l = int((sub.loc[present.index, "phase_label"] == "luteal").sum())
                sd = vals.std(ddof=0)
                if n_f < 2 or n_l < 2 or not sd or np.isnan(sd):
                    continue
                z.loc[g.index] = (vals - vals.mean()) / sd
        out[base] = z
    return out


def _cliffs_by_feature(matrix: pd.DataFrame, features: list[str], labels: np.ndarray) -> dict[str, float]:
    foll = labels == "follicular"
    lut = labels == "luteal"
    out: dict[str, float] = {}
    for f in features:
        if f not in matrix.columns:
            out[f] = np.nan
            continue
        col = matrix[f].to_numpy(dtype=float)
        a = col[lut]
        a = a[~np.isnan(a)]
        b = col[foll]
        b = b[~np.isnan(b)]
        out[f] = cliffs_delta(a, b) if (a.size and b.size) else np.nan
    return out


def _channel_abs_mean(cliffs: dict[str, float], features: list[str]) -> float:
    vals = np.array([cliffs[f] for f in features if f in cliffs and not np.isnan(cliffs[f])])
    return float(np.nanmean(np.abs(vals))) if vals.size else np.nan


def feature_effect_table(df: pd.DataFrame, task: str) -> pd.DataFrame:
    """Tidy per-feature Cliff's delta (luteal vs follicular) for every family."""
    rows = []
    for fam, members in FAMILIES.items():
        matrix = _zmatrix(df, list(members), task)
        labels = matrix["phase_label"].to_numpy()
        cliffs = _cliffs_by_feature(matrix, list(members), labels)
        for base, label in members.items():
            d = cliffs.get(base, np.nan)
            n_ok = int(matrix[base].notna().sum()) if base in matrix else 0
            rows.append(
                {
                    "family": fam,
                    "family_label": FAMILY_LABELS[fam],
                    "feature": base,
                    "label": label,
                    "task": task,
                    "cliffs_delta": d,
                    "magnitude": cliffs_magnitude(d) if not np.isnan(d) else "n/a",
                    "n_days": n_ok,
                }
            )
    return pd.DataFrame(rows)


def dissociation_test(
    df: pd.DataFrame,
    task: str,
    moved: list[str] | None = None,
    spared: list[str] | None = None,
    label: str = "broad",
    n_perm: int = 5000,
    seed: int = 7,
) -> dict:
    """Test that the moved channel separates from the spared channel beyond chance.

    Statistic D = mean|Cliff's delta| over MOVED features - mean|Cliff's delta|
    over SPARED features. Null: shuffle phase labels within each cycle.
    """
    moved = list(MOVED_CHANNEL) if moved is None else moved
    spared = list(SPARED_CHANNEL) if spared is None else spared
    matrix = _zmatrix(df, moved + spared, task)
    labels = matrix["phase_label"].to_numpy()
    cyc = matrix["cycle_start_date"].to_numpy()

    obs_cliffs = _cliffs_by_feature(matrix, moved + spared, labels)
    moved_obs = _channel_abs_mean(obs_cliffs, moved)
    spared_obs = _channel_abs_mean(obs_cliffs, spared)
    d_obs = moved_obs - spared_obs

    rng = np.random.default_rng(seed)
    cycles = np.unique(cyc)
    ge = 0
    for _ in range(n_perm):
        lab = labels.copy()
        for c in cycles:
            idx = np.where(cyc == c)[0]
            lab[idx] = rng.permutation(labels[idx])
        c_perm = _cliffs_by_feature(matrix, moved + spared, lab)
        d_perm = _channel_abs_mean(c_perm, moved) - _channel_abs_mean(c_perm, spared)
        if d_perm >= d_obs:
            ge += 1
    p = (1 + ge) / (1 + n_perm)
    return {
        "task": task,
        "moved_set": label,
        "moved_abs_cliffs": moved_obs,
        "spared_abs_cliffs": spared_obs,
        "dissociation_D": d_obs,
        "perm_p": p,
        "n_perm": n_perm,
    }


def equivalence_test(df: pd.DataFrame, task: str, n_boot: int = 4000, seed: int = 11) -> dict:
    """Equivalence (TOST-style) on the spared geometry channel.

    Geometry is declared statistically negligible if the 90% bootstrap CI of its
    mean |Cliff's delta| lies entirely below the SESOI (0.147). Bootstrap resamples
    days within each (cycle, phase) stratum.
    """
    spared = list(SPARED_CHANNEL)
    moved = list(MOVED_CHANNEL)
    matrix = _zmatrix(df, spared + moved, task)
    labels = matrix["phase_label"].to_numpy()
    cyc = matrix["cycle_start_date"].to_numpy()

    spared_obs = _channel_abs_mean(_cliffs_by_feature(matrix, spared, labels), spared)
    moved_obs = _channel_abs_mean(_cliffs_by_feature(matrix, moved, labels), moved)

    strata = [np.where((cyc == c) & (labels == ph))[0] for c in np.unique(cyc) for ph in ("follicular", "luteal")]
    strata = [s for s in strata if s.size > 0]
    rng = np.random.default_rng(seed)
    boots = np.empty(n_boot)
    for i in range(n_boot):
        idx = np.concatenate([rng.choice(s, size=s.size, replace=True) for s in strata])
        mb = matrix.iloc[idx]
        boots[i] = _channel_abs_mean(_cliffs_by_feature(mb, spared, mb["phase_label"].to_numpy()), spared)
    lo, hi = np.nanpercentile(boots, [5, 95])  # 90% CI for one-sided TOST at alpha=0.05
    return {
        "task": task,
        "sesoi": SESOI,
        "geometry_abs_cliffs": spared_obs,
        "geometry_ci90_lo": float(lo),
        "geometry_ci90_hi": float(hi),
        "moved_abs_cliffs": moved_obs,
        "equivalent_to_negligible": bool(hi < SESOI),
    }
