from __future__ import annotations

import pandas as pd

from .load_data import KEY_VOICE_FEATURES


def aggregate_voice_daily(voice_df: pd.DataFrame) -> pd.DataFrame:
    feature_cols = [c for c in KEY_VOICE_FEATURES if c in voice_df.columns]
    grouped = (
        voice_df.groupby("date", as_index=False)
        .agg(
            recording_count=("taskType", "count"),
            vowel_count=("taskType", lambda s: (s == "vowel").sum()),
            prosody_count=("taskType", lambda s: (s == "prosody").sum()),
            clipping_rate=("qc_clipping_detected", "mean"),
            duration_sec_mean=("qc_duration_sec", "mean"),
            **{f"{col}_median": (col, "median") for col in feature_cols},
        )
        .sort_values("date")
    )
    return grouped


def align_daily_data(
    voice_daily_df: pd.DataFrame,
    oura_df: pd.DataFrame,
    inito_df: pd.DataFrame,
) -> pd.DataFrame:
    merged = voice_daily_df.merge(oura_df, on="date", how="left")
    merged = merged.merge(inito_df, on="date", how="left")
    merged = merged.sort_values("date").reset_index(drop=True)
    return merged

