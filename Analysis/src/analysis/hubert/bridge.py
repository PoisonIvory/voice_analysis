"""Triangulate the d-prime signals against the eGeMAPS phoneme study.

Single responsibility: join per-day HuBERT-base d-prime to the per-day acoustic
features the phoneme study already trusts, and ask whether representational
separability tracks the named acoustic effects. This is what connects the two
studies rather than re-running the paper:

- composite consonant d-prime vs the global luteal timbre / open-quotient
  setting (segment_mfcc2_mean, segment_h1h2_mean): expected weak, since the
  cycle moves the acoustic surface while leaving separability ~stable.
- voicing d-prime vs the diphthong open-quotient residual (diphthong
  segment_h1h2_mean): does the representational voiced/voiceless split move with
  the open-quotient residual the phoneme study localized to diphthongs?
- nasality d-prime vs the nasal timbre residual (nasal segment_mfcc2_mean): does
  representational nasal separability move with the luteal nasal-congestion
  timbre residual?

Reuses the phoneme study's loader + day-grain aggregation so the acoustic side
is identical to that study (shared, validated machinery).
"""

from __future__ import annotations

import pandas as pd
from scipy import stats

from ..phoneme.aggregation import day_series
from ..phoneme.load_phonemes import analyzable_segments, load_phonemes
from ..stats import partial_spearman
from .load_dprime import primary
from .taxonomy import COMPOSITE_CONSONANT, dprime_col

# (d-prime feature, eGeMAPS phoneme feature, manner subset or None, description)
_TRIANGULATION: list[tuple[str, str, str | None, str]] = [
    (COMPOSITE_CONSONANT, "segment_mfcc2_mean", None, "composite d-prime vs global timbre setting"),
    (COMPOSITE_CONSONANT, "segment_h1h2_mean", None, "composite d-prime vs global open quotient"),
    (dprime_col("voicing"), "segment_h1h2_mean", "diphthong", "voicing d-prime vs diphthong open quotient"),
    (dprime_col("nasality"), "segment_mfcc2_mean", "nasal", "nasality d-prime vs nasal timbre"),
]


def triangulation(df: pd.DataFrame) -> pd.DataFrame:
    """Per-day Spearman (raw + date-partial) of d-prime vs eGeMAPS phoneme effects."""
    prim = primary(df)
    phon = analyzable_segments(load_phonemes())

    rows: list[dict[str, object]] = []
    for dcol, scol, manner, description in _TRIANGULATION:
        d_day = day_series(prim, dcol)[["date", dcol]]
        mask = None if manner is None else (phon["phonemeManner"] == manner)
        s_day = day_series(phon, scol, subset=mask)[["date", scol]]
        joined = d_day.merge(s_day, on="date").dropna()
        n = len(joined)
        if n < 6:
            rows.append({"description": description, "dprime_feature": dcol, "egemaps_feature": scol,
                         "manner_subset": manner or "all", "n_days": n,
                         "raw_rho": float("nan"), "date_partial_rho": float("nan")})
            continue
        joined["day_index"] = (joined["date"] - joined["date"].min()).dt.days.astype(float)
        raw = stats.spearmanr(joined[dcol], joined[scol]).statistic
        partial, _ = partial_spearman(joined, dcol, scol, "day_index")
        rows.append({"description": description, "dprime_feature": dcol, "egemaps_feature": scol,
                     "manner_subset": manner or "all", "n_days": n,
                     "raw_rho": round(float(raw), 3), "date_partial_rho": round(float(partial), 3)})
    return pd.DataFrame(rows)
