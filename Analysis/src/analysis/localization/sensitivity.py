"""Thread 1 - the sensitivity floor: the spared channel could have moved.

A null only localizes a driver if the instrument that returned it is sensitive.
We show that vocal-tract geometry (formant frequencies) is hugely movable in
this very dataset - across vowels within a single recording, and between the
sustained-vowel and connected-speech tasks - yet barely moves across the cycle.
The dog could bark; it just did not.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..feature_taxonomy import with_task
from .config import GEOMETRY, localization_paths


def _median(series: pd.Series) -> float:
    return float(series.dropna().median()) if series.notna().any() else np.nan


def sensitivity_table(df: pd.DataFrame) -> pd.DataFrame:
    """Within-recording and cross-task formant movement vs the cycle shift (Hz)."""
    phase = df["phase_label"].notna()
    rows = []
    for base, label in GEOMETRY.items():
        sd_base = base.replace("_amean", "_stddevNorm")
        pros = with_task(base, "prosody")
        pros_sd = with_task(sd_base, "prosody")
        vow = with_task(base, "vowel")

        mean_hz = _median(df[pros]) if pros in df else np.nan
        # eGeMAPS stddevNorm = SD / mean, so within-recording SD(Hz) = stddevNorm * mean.
        within_sd_hz = (
            _median(df[pros_sd] * df[pros]) if (pros_sd in df and pros in df) else np.nan
        )

        foll = df.loc[phase & (df["phase_label"] == "follicular"), pros]
        lut = df.loc[phase & (df["phase_label"] == "luteal"), pros]
        cycle_shift_hz = abs(_median(lut) - _median(foll))

        task_shift_hz = (
            abs(_median(df[vow]) - _median(df[pros]))
            if (vow in df and pros in df)
            else np.nan
        )

        rows.append(
            {
                "formant": label,
                "mean_hz": mean_hz,
                "within_recording_sd_hz": within_sd_hz,
                "vowel_vs_prosody_shift_hz": task_shift_hz,
                "cycle_shift_hz": cycle_shift_hz,
                "sensitivity_ratio_withinrec": within_sd_hz / cycle_shift_hz
                if cycle_shift_hz
                else np.nan,
                "sensitivity_ratio_task": task_shift_hz / cycle_shift_hz
                if cycle_shift_hz
                else np.nan,
            }
        )
    return pd.DataFrame(rows)


def hubert_vowel_geometry() -> pd.DataFrame:
    """Optional: median vowel-geometry d-prime from the HuBERT study, if present.

    Demonstrates geometry is strongly separable in a third, independent
    representation. Degrades gracefully if the table is unavailable.
    """
    path = localization_paths().hubert_phase_contrasts
    if not path.exists():
        return pd.DataFrame()
    try:
        h = pd.read_csv(path)
    except Exception:
        return pd.DataFrame()
    cols = {c.lower(): c for c in h.columns}
    name_col = cols.get("contrast") or cols.get("feature")
    if name_col is None:
        return pd.DataFrame()
    geo = h[h[name_col].astype(str).str.contains("vowel|back|height|low", case=False, na=False)]
    return geo.reset_index(drop=True)
