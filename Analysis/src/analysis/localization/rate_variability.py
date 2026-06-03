"""Thread 3 - rate, not level: does the cover destabilize when hormones move fast?

Kervin 2025 found voice was most variable during the rapidly-changing menses and
luteal phases and most stable in the hormonally-flat fertile window, but could
only infer rate from phase. We test the cover-specific version: within-cycle
voice variability of the cover vs geometry, in rapid-change vs stable windows,
and against measured progesterone rate of change. Directional; voice is sparse.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..feature_taxonomy import with_task
from .config import GEOMETRY, MOVED_CHANNEL
from .hormones import hormone_rates


def _z_within_cycle_all(df: pd.DataFrame, col: str, min_days: int = 4) -> pd.Series:
    """Z-score a feature within each cycle using all that cycle's voice days."""
    z = pd.Series(np.nan, index=df.index, dtype=float)
    if col not in df.columns:
        return z
    for _, g in df.groupby("cycle_start_date"):
        vals = g[col].dropna()
        if vals.size < min_days:
            continue
        sd = vals.std(ddof=0)
        if not sd or np.isnan(sd):
            continue
        z.loc[vals.index] = (vals - vals.mean()) / sd
    return z


def _window(row) -> str:
    cd = row.get("cycle_day")
    dn = row.get("days_to_next_start")
    cd = None if pd.isna(cd) else int(cd)
    dn = None if pd.isna(dn) else int(dn)
    if (cd is not None and cd <= 4) or (dn is not None and dn <= 3):
        return "rapid"  # menses + premenstrual
    if cd is not None and 6 <= cd <= 12 and (dn is None or dn > 3):
        return "stable"  # mid-follicular plateau
    return "other"


def _channel_dispersion(df: pd.DataFrame, members: dict[str, str], task: str, group_col: str) -> pd.DataFrame:
    """IQR of within-cycle-z values per group, averaged across a feature set."""
    work = df.copy()
    feats = []
    for base in members:
        col = with_task(base, task)
        zc = f"_z_{base}"
        work[zc] = _z_within_cycle_all(work, col)
        feats.append(zc)
    rows = []
    for grp, g in work.groupby(group_col):
        per_feat = []
        for zc in feats:
            vals = g[zc].dropna()
            if vals.size >= 3:
                per_feat.append(float(vals.quantile(0.75) - vals.quantile(0.25)))
        if per_feat:
            rows.append({group_col: grp, "dispersion_iqr_z": float(np.mean(per_feat)),
                         "n_days_median": int(np.median([g[zc].notna().sum() for zc in feats]))})
    return pd.DataFrame(rows)


def variability_by_window(df: pd.DataFrame, task: str) -> pd.DataFrame:
    """Cover vs geometry voice variability in rapid-change vs stable windows."""
    work = df[df["phase_label"].notna()].copy()
    work["window"] = work.apply(_window, axis=1)
    work = work[work["window"].isin(["rapid", "stable"])]
    cover = _channel_dispersion(work, MOVED_CHANNEL, task, "window").assign(channel="cover")
    geom = _channel_dispersion(work, GEOMETRY, task, "window").assign(channel="geometry")
    return pd.concat([cover, geom], ignore_index=True)


def variability_by_pdg_rate(df: pd.DataFrame, task: str) -> pd.DataFrame:
    """Cover vs geometry variability on high vs low |progesterone rate| days."""
    rates = hormone_rates(df)[["date", "pdg_abs_rate"]]
    work = df.merge(rates, on="date", how="left")
    work = work[work["pdg_abs_rate"].notna() & work["has_voice"]].copy()
    if work.empty:
        return pd.DataFrame()
    med = work["pdg_abs_rate"].median()
    work["pdg_rate_group"] = np.where(work["pdg_abs_rate"] > med, "fast", "slow")
    cover = _channel_dispersion(work, MOVED_CHANNEL, task, "pdg_rate_group").assign(channel="cover")
    geom = _channel_dispersion(work, GEOMETRY, task, "pdg_rate_group").assign(channel="geometry")
    return pd.concat([cover, geom], ignore_index=True)
