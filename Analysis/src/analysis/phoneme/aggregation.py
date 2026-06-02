"""Aggregation helpers shared across the phoneme analyses.

Single responsibility: turn the phoneme-grain frame into the day- and
recording-grain series the statistics operate on, and provide the within-cycle
normalization used as the primary drift control (consistent with the
whole-recording study's Lens 2).

Grain policy
------------
- One prosody recording is the natural self-normalizing unit (within-recording
  contrasts live here). Multiple recordings can share a date.
- Phase contrasts and hormone coupling are computed at the DAY grain (recordings
  averaged within a day) to avoid pseudo-replication, matching the house style.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

BALANCED_CYCLES = ("2026-01-14", "2026-02-12")


def recording_class_mean(df: pd.DataFrame, feature: str, class_col: str, class_val: str) -> pd.DataFrame:
    """Mean of `feature` over phonemes of one class, per recording (+ context)."""
    sub = df[df[class_col] == class_val].dropna(subset=[feature])
    keep = ["date", "recordingId", "phase_label", "cycle_start_date", "day_index", "pdg", "e3g"]
    keep = [c for c in keep if c in df.columns]
    rec = sub.groupby(["recordingId"], as_index=False)[feature].mean()
    meta = sub.drop_duplicates("recordingId")[["recordingId", *[c for c in keep if c != "recordingId"]]]
    return rec.merge(meta, on="recordingId", how="left")


def day_series(df: pd.DataFrame, feature: str, subset: pd.Series | None = None) -> pd.DataFrame:
    """Day-grain series of `feature` (recordings averaged within a day).

    `subset` is an optional boolean mask aligned to `df` selecting phonemes.
    """
    s = df if subset is None else df[subset]
    s = s.dropna(subset=[feature])
    rec = s.groupby(["date", "recordingId"], as_index=False)[feature].mean()
    day = rec.groupby("date", as_index=False)[feature].mean()
    meta_cols = ["date", "phase_label", "cycle_week", "cycle_start_date", "cycle_day", "day_index", "pdg", "e3g"]
    meta_cols = [c for c in meta_cols if c in df.columns]
    meta = df.drop_duplicates("date")[meta_cols]
    return day.merge(meta, on="date", how="left")


def within_cycle_z(day: pd.DataFrame, feature: str, cycle_col: str = "cycle_start_date") -> pd.Series:
    """Z-score `feature` inside each cycle (each cycle is its own baseline)."""
    def _z(x: pd.Series) -> pd.Series:
        sd = x.std(ddof=0)
        return (x - x.mean()) / sd if sd > 0 else x * 0.0

    return day.groupby(cycle_col)[feature].transform(_z)


def within_cycle_phase_shift(day: pd.DataFrame, feature: str, cycles=BALANCED_CYCLES) -> dict[str, float]:
    """Luteal-minus-follicular shift (within-cycle SD units) per balanced cycle."""
    d = day.dropna(subset=[feature]).copy()
    d["_z"] = within_cycle_z(d, feature)
    out: dict[str, float] = {}
    cyc = d["cycle_start_date"].astype(str).str[:10]
    for cs in cycles:
        g = d[cyc == cs]
        lut = g.loc[g["phase_label"] == "luteal", "_z"]
        fol = g.loc[g["phase_label"] == "follicular", "_z"]
        out[cs] = float(lut.mean() - fol.mean()) if len(lut) and len(fol) else np.nan
    return out
