"""Statistics helpers tuned for an N-of-1 repeated-measures design.

With one participant and a handful of cycles, we prioritize effect sizes and
cross-cycle consistency over p-values. Functions here are deliberately small.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


def cliffs_delta(a: np.ndarray, b: np.ndarray) -> float:
    """Nonparametric effect size in [-1, 1]: P(a>b) - P(a<b)."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    a = a[~np.isnan(a)]
    b = b[~np.isnan(b)]
    if a.size == 0 or b.size == 0:
        return np.nan
    diff = a[:, None] - b[None, :]
    return float((np.sign(diff).sum()) / (a.size * b.size))


def cliffs_magnitude(delta: float) -> str:
    """Romano et al. thresholds for |Cliff's delta|."""
    d = abs(delta)
    if np.isnan(d):
        return "n/a"
    if d < 0.147:
        return "negligible"
    if d < 0.33:
        return "small"
    if d < 0.474:
        return "medium"
    return "large"


@dataclass(frozen=True)
class PhaseContrast:
    feature: str
    n_follicular: int
    n_luteal: int
    median_follicular: float
    median_luteal: float
    delta_luteal_minus_follicular: float
    cliffs_delta: float
    magnitude: str
    mann_whitney_p: float
    cycles_consistent: int
    cycles_total: int


def phase_contrast(
    df: pd.DataFrame, feature: str, group_col: str = "phase_label", cycle_col: str = "cycle_start_date"
) -> PhaseContrast:
    """Compare luteal vs follicular for one feature, with cross-cycle consistency.

    Cliff's delta is computed as luteal-vs-follicular (positive = higher in luteal).
    `cycles_consistent` counts cycles whose luteal-minus-follicular median shares
    the sign of the pooled difference.

    `mann_whitney_p` treats each day as independent; serial dependence within cycles
    makes it anti-conservative. Prefer effect sizes and cross-cycle consistency.
    """
    sub = df[[feature, group_col, cycle_col]].dropna(subset=[feature, group_col])
    foll = sub.loc[sub[group_col] == "follicular", feature].to_numpy(dtype=float)
    lut = sub.loc[sub[group_col] == "luteal", feature].to_numpy(dtype=float)

    median_f = float(np.median(foll)) if foll.size else np.nan
    median_l = float(np.median(lut)) if lut.size else np.nan
    delta_raw = median_l - median_f
    cd = cliffs_delta(lut, foll)

    if foll.size and lut.size:
        try:
            _, p = stats.mannwhitneyu(lut, foll, alternative="two-sided")
        except ValueError:
            p = np.nan
    else:
        p = np.nan

    pooled_sign = np.sign(delta_raw) if not np.isnan(delta_raw) else 0.0
    consistent = 0
    total = 0
    for _, g in sub.groupby(cycle_col):
        gf = g.loc[g[group_col] == "follicular", feature]
        gl = g.loc[g[group_col] == "luteal", feature]
        if len(gf) and len(gl):
            total += 1
            if np.sign(gl.median() - gf.median()) == pooled_sign and pooled_sign != 0:
                consistent += 1

    return PhaseContrast(
        feature=feature,
        n_follicular=int(foll.size),
        n_luteal=int(lut.size),
        median_follicular=median_f,
        median_luteal=median_l,
        delta_luteal_minus_follicular=float(delta_raw),
        cliffs_delta=float(cd),
        magnitude=cliffs_magnitude(cd),
        mann_whitney_p=float(p),
        cycles_consistent=consistent,
        cycles_total=total,
    )


def partial_spearman(df: pd.DataFrame, x: str, y: str, z: str) -> tuple[float, int]:
    """First-order partial Spearman of x,y controlling for nuisance z (e.g. date).

    Returns (partial_rho, n). Used to separate true coupling from shared drift.
    Descriptive only: no p-value and no adjustment for serial dependence.
    """
    sub = df[[x, y, z]].dropna()
    n = len(sub)
    if n < 6:
        return np.nan, n
    rxy = stats.spearmanr(sub[x], sub[y]).statistic
    rxz = stats.spearmanr(sub[x], sub[z]).statistic
    ryz = stats.spearmanr(sub[y], sub[z]).statistic
    denom = np.sqrt((1 - rxz**2) * (1 - ryz**2))
    if denom == 0 or np.isnan(denom):
        return np.nan, n
    return float((rxy - rxz * ryz) / denom), n


def benjamini_hochberg(pvals: np.ndarray) -> np.ndarray:
    """Return BH-FDR adjusted q-values for an array of p-values.

    Assumes independent (or positively dependent) tests; serially correlated day
    p-values are anti-conservative. Use for screening, not as sole confirmatory evidence.
    """
    p = np.asarray(pvals, dtype=float)
    mask = ~np.isnan(p)
    q = np.full_like(p, np.nan)
    if mask.sum() == 0:
        return q
    pv = p[mask]
    m = pv.size
    order = np.argsort(pv)
    ranked = pv[order]
    adj = ranked * m / (np.arange(1, m + 1))
    adj = np.minimum.accumulate(adj[::-1])[::-1]
    adj = np.clip(adj, 0, 1)
    out = np.empty(m)
    out[order] = adj
    q[mask] = out
    return q
