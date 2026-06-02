"""Segment-level confound control: is the diphthong H1-H2 effect just pitch?

H1-H2 (open quotient) is mechanically correlated with F0. Here we regress every
voiced segment's H1-H2 on its own F0 (pooled OLS over all analyzable voiced
segments), keep the residual, then re-run the recording-demeaned per-manner
phase contrast on the residual. If the diphthong-specific excess survives, the
open-quotient signal is not a re-description of a pitch difference.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..stats import cliffs_delta, cliffs_magnitude
from .aggregation import day_series
from .localization import _phase_delta

MANNERS = ["vowel", "diphthong", "nasal", "approximant", "stop", "fricative"]


def residualize_h1h2_on_f0(df: pd.DataFrame) -> pd.DataFrame:
    """Return analyzable voiced segments with an F0-residualized H1-H2 column."""
    av = df.dropna(subset=["segment_h1h2_mean", "segment_f0_mean"]).copy()
    X = np.column_stack([np.ones(len(av)), av["segment_f0_mean"].to_numpy(float)])
    y = av["segment_h1h2_mean"].to_numpy(float)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    av["h1h2_resid_f0"] = y - X @ beta
    av.attrs["f0_r2"] = float(1.0 - np.var(av["h1h2_resid_f0"]) / np.var(y))
    return av


def diphthong_residual_table(df: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    """Recording-demeaned per-manner phase delta on F0-residualized H1-H2."""
    av = residualize_h1h2_on_f0(df)
    rec_mean = av.groupby("recordingId")["h1h2_resid_f0"].transform("mean")
    av["resid_demeaned"] = av["h1h2_resid_f0"] - rec_mean
    rows = []
    for m in MANNERS:
        mask = av["phonemeManner"] == m
        if mask.sum() == 0:
            continue
        day = day_series(av, "resid_demeaned", subset=mask)
        cd, nf, nl, _ = _phase_delta(day, "resid_demeaned")
        rows.append(
            {
                "phoneme_class": m,
                "n_follicular_days": nf,
                "n_luteal_days": nl,
                "cliffs_delta_resid_demeaned": round(cd, 3),
                "magnitude": cliffs_magnitude(cd),
            }
        )
    return pd.DataFrame(rows), av.attrs["f0_r2"]
