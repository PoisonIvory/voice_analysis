"""Shared data access and within-cycle effect helpers for localization.

The analysis grain is one row per calendar day. Phase contrasts use within-cycle
normalization (z-score each feature inside its own cycle) so slow drift between
cycles cannot leak into a phase effect. Only cycles with enough days in both
phases anchor a contrast.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..analysis_dataset import build_analysis_table
from ..feature_taxonomy import with_task
from ..stats import cliffs_delta
from .config import BALANCED_CYCLE_STARTS


def load_daily() -> pd.DataFrame:
    """Fresh unified daily table with an integer day_index for drift control."""
    df = build_analysis_table()
    df = df.sort_values("date").reset_index(drop=True)
    df["day_index"] = (df["date"] - df["date"].min()).dt.days
    if "e3g" in df and "pdg" in df:
        ratio = df["e3g"] / df["pdg"].replace(0, np.nan)
        df["ep_ratio"] = ratio.where(np.isfinite(ratio))
    return df


def _balanced_mask(df: pd.DataFrame, cycles=BALANCED_CYCLE_STARTS) -> pd.Series:
    starts = {pd.Timestamp(c) for c in cycles}
    return df["cycle_start_date"].isin(starts)


def within_cycle_z(
    df: pd.DataFrame, col: str, cycles=BALANCED_CYCLE_STARTS, min_per_phase: int = 2
) -> pd.DataFrame:
    """Return rows (cycle, phase, z) for cycles with >= min_per_phase in both phases."""
    if col not in df.columns:
        return pd.DataFrame(columns=["cycle_start_date", "phase_label", "z"])
    sub = df.loc[_balanced_mask(df, cycles), ["cycle_start_date", "phase_label", col]]
    sub = sub.dropna(subset=[col, "phase_label"])
    frames = []
    for cstart, g in sub.groupby("cycle_start_date"):
        n_f = int((g["phase_label"] == "follicular").sum())
        n_l = int((g["phase_label"] == "luteal").sum())
        if n_f < min_per_phase or n_l < min_per_phase:
            continue
        sd = g[col].std(ddof=0)
        if not sd or np.isnan(sd):
            continue
        gg = g[["cycle_start_date", "phase_label"]].copy()
        gg["z"] = (g[col] - g[col].mean()) / sd
        frames.append(gg)
    if not frames:
        return pd.DataFrame(columns=["cycle_start_date", "phase_label", "z"])
    return pd.concat(frames, ignore_index=True)


def standardized_phase_effect(df: pd.DataFrame, base_feature: str, task: str) -> dict | None:
    """Luteal-minus-follicular effect for one feature, within-cycle normalized.

    Returns std_mean_diff (in within-cycle SD units) and Cliff's delta, or None
    if the feature has too few balanced-cycle days.
    """
    z = within_cycle_z(df, with_task(base_feature, task))
    foll = z.loc[z["phase_label"] == "follicular", "z"].to_numpy(dtype=float)
    lut = z.loc[z["phase_label"] == "luteal", "z"].to_numpy(dtype=float)
    if foll.size < 2 or lut.size < 2:
        return None
    return {
        "feature": base_feature,
        "task": task,
        "n_foll": int(foll.size),
        "n_lut": int(lut.size),
        "std_mean_diff": float(lut.mean() - foll.mean()),
        "cliffs_delta": float(cliffs_delta(lut, foll)),
    }


def family_effects(df: pd.DataFrame, members: dict[str, str], task: str) -> pd.DataFrame:
    """Per-feature standardized phase effects for a family (one task)."""
    rows = []
    for base in members:
        eff = standardized_phase_effect(df, base, task)
        if eff is not None:
            eff["label"] = members[base]
            rows.append(eff)
    return pd.DataFrame(rows)


def pooled_abs_effect(effects: pd.DataFrame) -> float:
    """Family summary: mean absolute standardized effect across member features."""
    if effects.empty:
        return float("nan")
    return float(effects["std_mean_diff"].abs().mean())
