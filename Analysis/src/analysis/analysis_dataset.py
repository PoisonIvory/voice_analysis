"""Builds the unified daily analysis table from all four data sources.

One row per calendar date. Sources are joined on date and kept sparse (missing
values stay null) so each analysis can use pairwise-complete data.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import default_paths
from .load_data import (
    load_cycle_calendar,
    load_inito,
    load_oura_from_parquet,
    load_voice_daily_handoff,
)

# Oura fields kept for cycle-periodicity screening and positive controls.
OURA_KEEP: dict[str, str] = {
    "temperatureDeviation": "temp_deviation",
    "temperatureTrendDeviation": "temp_trend_deviation",
    "averageHrv": "hrv",
    "hrvBalance": "hrv_balance",
    "restingHeartRate": "resting_hr",
    "averageHeartRate": "average_hr",
    "lowestHeartRate": "lowest_hr",
    "averageBreath": "breath_rate",
    "sleepScore": "sleep_score",
    "readinessScore": "readiness_score",
    "activityScore": "activity_score",
    "totalSleepDuration": "total_sleep_sec",
    "remSleepDuration": "rem_sleep_sec",
    "deepSleepDuration": "deep_sleep_sec",
    "sleepEfficiency": "sleep_efficiency",
    "steps": "steps",
    "spo2Average": "spo2",
    "breathingDisturbanceIndex": "breathing_disturbance",
}


def _prepare_oura(path: Path) -> pd.DataFrame:
    oura = load_oura_from_parquet(path)
    available = {src: dst for src, dst in OURA_KEEP.items() if src in oura.columns}
    out = oura[["date", *available.keys()]].rename(columns=available)
    for col in available.values():
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out.sort_values("date").drop_duplicates(subset=["date"], keep="last")


def _prepare_hormones(path: Path) -> pd.DataFrame:
    inito = load_inito(path)
    inito = inito.rename(columns={"cycle_day": "hormone_cycle_day"})
    for col in ["e3g", "pdg", "fsh", "lh"]:
        if col in inito.columns:
            inito[col] = pd.to_numeric(inito[col], errors="coerce")
    return inito


def build_analysis_table(paths=None) -> pd.DataFrame:
    paths = paths or default_paths()

    voice = load_voice_daily_handoff(paths.voice_daily_parquet)
    voice = voice.drop(columns=["userId"], errors="ignore")

    calendar = load_cycle_calendar(paths.cycle_calendar_parquet)
    oura = _prepare_oura(paths.oura_parquet)
    hormones = _prepare_hormones(paths.inito_csv)

    table = calendar.merge(voice, on="date", how="outer")
    table = table.merge(oura, on="date", how="outer")
    table = table.merge(hormones, on="date", how="outer")

    table = table.sort_values("date").reset_index(drop=True)
    has_vowel = table["has_vowel"] == True if "has_vowel" in table else False  # noqa: E712
    has_prosody = table["has_prosody"] == True if "has_prosody" in table else False  # noqa: E712
    table["has_voice"] = has_vowel | has_prosody
    table["has_hormones"] = table[["e3g", "pdg"]].notna().any(axis=1)
    table["has_oura"] = table["temp_deviation"].notna() if "temp_deviation" in table else False
    return table


if __name__ == "__main__":
    df = build_analysis_table()
    print("rows:", len(df))
    print("date range:", df["date"].min(), "->", df["date"].max())
    print("labeled cycle days:", df["phase_label"].notna().sum())
    print("voice days:", df["has_voice"].sum())
    print("voice+phase days:", (df["has_voice"] & df["phase_label"].notna()).sum())
    print("voice+hormone days:", (df["has_voice"] & df["has_hormones"]).sum())
