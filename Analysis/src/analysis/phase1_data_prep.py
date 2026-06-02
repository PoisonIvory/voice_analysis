"""Phase 1 data prep workflow for voice handoff validation and merge readiness."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

import pandas as pd

from .load_data import (
    load_cycle_calendar,
    load_inito,
    load_oura_from_parquet,
    load_voice_daily_handoff,
)


@dataclass(frozen=True)
class Phase1Artifacts:
    merged_output_path: Path
    readiness_report_path: Path
    voice_validation_report_path: Path


def _date_window(df: pd.DataFrame, date_column: str = "date") -> str:
    if df.empty or date_column not in df.columns:
        return "n/a to n/a (0 rows)"
    min_date = df[date_column].min()
    max_date = df[date_column].max()
    return f"{min_date.date()} to {max_date.date()} ({len(df)} rows)"


def _voice_summary(voice: pd.DataFrame) -> dict[str, object]:
    has_vowel = voice["has_vowel"].fillna(False) if "has_vowel" in voice.columns else pd.Series(False, index=voice.index)
    has_prosody = (
        voice["has_prosody"].fillna(False) if "has_prosody" in voice.columns else pd.Series(False, index=voice.index)
    )

    return {
        "rows": len(voice),
        "unique_users": int(voice["userId"].nunique()),
        "user_id": str(voice["userId"].iloc[0]),
        "date_min": voice["date"].min(),
        "date_max": voice["date"].max(),
        "duplicate_rows": int(voice.duplicated(subset=["userId", "date"], keep=False).sum()),
        "unique_user_day_rows": int(voice[["userId", "date"]].drop_duplicates().shape[0]),
        "complete_days": int((has_vowel & has_prosody).sum()),
        "vowel_only_days": int((has_vowel & ~has_prosody).sum()),
        "prosody_only_days": int((~has_vowel & has_prosody).sum()),
        "diagnostics": {
            "voice_recording_count": "voice_recording_count" in voice.columns,
            "voice_task_count": "voice_task_count" in voice.columns,
            "voice_duration_sec_median": "voice_duration_sec_median" in voice.columns,
            "vowel_recording_count": "vowel_recording_count" in voice.columns,
            "prosody_recording_count": "prosody_recording_count" in voice.columns,
        },
    }


def _build_merged_dataset(
    voice: pd.DataFrame,
    oura: pd.DataFrame,
    inito: pd.DataFrame,
    cycle: pd.DataFrame,
) -> pd.DataFrame:
    inito_phase1 = inito.rename(columns={"cycle_day": "hormone_cycle_day"})
    merged = voice.merge(oura, on="date", how="outer")
    merged = merged.merge(inito_phase1, on="date", how="outer")
    merged = merged.merge(cycle, on="date", how="left")
    return merged.sort_values("date").reset_index(drop=True)


def _overlap_count(left: pd.DataFrame, right: pd.DataFrame) -> int:
    left_dates = set(left["date"].dropna().tolist())
    right_dates = set(right["date"].dropna().tolist())
    return len(left_dates & right_dates)


def _non_null_counts(df: pd.DataFrame, columns: list[str]) -> list[tuple[str, int]]:
    return [(column, int(df[column].notna().sum())) for column in columns if column in df.columns]


def _voice_feature_columns(voice: pd.DataFrame) -> list[str]:
    excluded = {"userId", "dayUtc", "date", "vowel_recording_ids", "prosody_recording_ids"}
    return [column for column in voice.columns if column not in excluded]


def _oura_columns(oura: pd.DataFrame) -> list[str]:
    return [column for column in oura.columns if column != "date"]


def _render_voice_handoff_validation_report(
    voice_path: Path,
    audit_path: Path,
    staging_path: Path,
    summary: dict[str, object],
) -> str:
    diagnostics = summary["diagnostics"]
    date_min = summary["date_min"]
    date_max = summary["date_max"]

    return (
        "# Voice Handoff Validation Report (Phase 1)\n\n"
        "## Scope\n\n"
        "- Validation scope is limited to file readability, one-user scope, and one-row-per-day contract.\n"
        "- No aggregation-rule validation is performed in this phase.\n\n"
        "## Inputs\n\n"
        f"- Canonical voice daily input: `{voice_path}`\n"
        f"- Supporting voice audit file: `{audit_path}`\n"
        f"- Supporting staging file (reference only): `{staging_path}`\n\n"
        "## Results\n\n"
        f"- Rows: `{summary['rows']}`\n"
        f"- Unique users: `{summary['unique_users']}`\n"
        f"- User ID: `{summary['user_id']}`\n"
        f"- Date range: `{date_min.date()} to {date_max.date()}`\n"
        f"- One-row-per-day contract: `pass` (`{summary['duplicate_rows']}` duplicate rows)\n"
        f"- Unique (userId, day) rows: `{summary['unique_user_day_rows']}`\n"
        f"- Complete days (`has_vowel && has_prosody`): `{summary['complete_days']}`\n"
        f"- Vowel-only days: `{summary['vowel_only_days']}`\n"
        f"- Prosody-only days: `{summary['prosody_only_days']}`\n\n"
        "## Diagnostics Columns Present\n\n"
        f"- `voice_recording_count`: `{diagnostics['voice_recording_count']}`\n"
        f"- `voice_task_count`: `{diagnostics['voice_task_count']}`\n"
        f"- `voice_duration_sec_median`: `{diagnostics['voice_duration_sec_median']}`\n"
        f"- `vowel_recording_count`: `{diagnostics['vowel_recording_count']}`\n"
        f"- `prosody_recording_count`: `{diagnostics['prosody_recording_count']}`\n"
    )


def _render_phase1_readiness_report(
    voice: pd.DataFrame,
    oura: pd.DataFrame,
    inito: pd.DataFrame,
    cycle: pd.DataFrame,
    merged: pd.DataFrame,
) -> str:
    source_frames = {
        "voice_daily": voice,
        "oura_snapshot": oura,
        "hormone_csv": inito,
        "cycle_calendar": cycle,
    }
    window_lines = [f"- `{name}`: {_date_window(frame)}" for name, frame in source_frames.items()]

    pairwise_lines: list[str] = []
    for left_name, right_name in combinations(source_frames.keys(), 2):
        overlap = _overlap_count(source_frames[left_name], source_frames[right_name])
        pairwise_lines.append(f"- `{left_name}` x `{right_name}`: `{overlap}` days")

    date_sets = [set(frame["date"].dropna().tolist()) for frame in source_frames.values()]
    four_way_overlap = len(set.intersection(*date_sets)) if date_sets else 0

    voice_n_lines = [
        f"- `{column}`: `{count}`"
        for column, count in _non_null_counts(merged, _voice_feature_columns(voice))
    ]
    oura_n_lines = [f"- `{column}`: `{count}`" for column, count in _non_null_counts(merged, _oura_columns(oura))]

    return (
        "# Phase 1 Readiness Report\n\n"
        "## Date Windows by Source\n\n"
        + "\n".join(window_lines)
        + "\n\n## Overlap Coverage\n\n"
        + "\n".join(pairwise_lines)
        + f"\n- 4-way overlap (`voice_daily` x `oura_snapshot` x `hormone_csv` x `cycle_calendar`): `{four_way_overlap}` days\n\n"
        + "## Per-Variable Non-Null N (Voice)\n\n"
        + ("\n".join(voice_n_lines) if voice_n_lines else "- n/a")
        + "\n\n## Per-Variable Non-Null N (Oura)\n\n"
        + ("\n".join(oura_n_lines) if oura_n_lines else "- n/a")
        + "\n\n## Outputs\n\n"
        "- First-pass merged dataset is ready for exploratory analysis.\n"
    )


def run_phase1_data_prep(
    voice_daily_path: Path,
    voice_audit_path: Path,
    voice_staging_path: Path,
    oura_path: Path,
    inito_path: Path,
    cycle_calendar_path: Path,
    expected_user_id: str,
    artifacts: Phase1Artifacts,
) -> None:
    voice = load_voice_daily_handoff(voice_daily_path, expected_user_id=expected_user_id)
    oura = load_oura_from_parquet(oura_path).sort_values("date").drop_duplicates(subset=["date"], keep="last")
    inito = load_inito(inito_path).sort_values("date").drop_duplicates(subset=["date"], keep="last")
    cycle = load_cycle_calendar(cycle_calendar_path).sort_values("date").drop_duplicates(subset=["date"], keep="last")
    merged = _build_merged_dataset(voice=voice, oura=oura, inito=inito, cycle=cycle)

    artifacts.merged_output_path.parent.mkdir(parents=True, exist_ok=True)
    artifacts.readiness_report_path.parent.mkdir(parents=True, exist_ok=True)
    artifacts.voice_validation_report_path.parent.mkdir(parents=True, exist_ok=True)

    merged.to_parquet(artifacts.merged_output_path, index=False)
    artifacts.voice_validation_report_path.write_text(
        _render_voice_handoff_validation_report(
            voice_path=voice_daily_path,
            audit_path=voice_audit_path,
            staging_path=voice_staging_path,
            summary=_voice_summary(voice),
        ),
        encoding="utf-8",
    )
    artifacts.readiness_report_path.write_text(
        _render_phase1_readiness_report(voice=voice, oura=oura, inito=inito, cycle=cycle, merged=merged),
        encoding="utf-8",
    )
