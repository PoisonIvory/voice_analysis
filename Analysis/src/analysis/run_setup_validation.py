"""CLI entrypoint that validates input coverage and emits cycle diagnostics."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .config import default_paths
from .cycle_calendar import MVP_CYCLE_START_DATES, build_cycle_calendar_daily
from .load_data import load_inito, load_oura_from_parquet, load_voice_features


def _date_window(df: pd.DataFrame) -> str:
    if df.empty or "date" not in df.columns:
        return "n/a to n/a (0 rows)"
    min_date = df["date"].min()
    max_date = df["date"].max()
    return f"{min_date.date() if pd.notna(min_date) else 'n/a'} to {max_date.date() if pd.notna(max_date) else 'n/a'} ({len(df)} rows)"


def _phase_count_line(df: pd.DataFrame, column: str) -> str:
    if column not in df.columns or df.empty:
        return "n/a"
    counts = df[column].value_counts(dropna=False)
    parts = [f"{label}: {int(value)}" for label, value in counts.items()]
    return ", ".join(parts) if parts else "n/a"


def _compute_calendar_range(*frames: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp]:
    mins: list[pd.Timestamp] = []
    maxs: list[pd.Timestamp] = []
    for frame in frames:
        if "date" not in frame.columns or frame.empty:
            continue
        min_date = frame["date"].min()
        max_date = frame["date"].max()
        if pd.notna(min_date):
            mins.append(pd.Timestamp(min_date).normalize())
        if pd.notna(max_date):
            maxs.append(pd.Timestamp(max_date).normalize())
    if not mins or not maxs:
        raise ValueError("Cannot build cycle calendar without at least one non-empty date series")
    return min(mins), max(maxs)


def _setup_report(
    voice: pd.DataFrame,
    oura: pd.DataFrame,
    inito: pd.DataFrame,
    cycle_calendar: pd.DataFrame,
    voice_with_cycle: pd.DataFrame,
) -> str:
    overlap_dates = set(voice["date"].dropna()) & set(oura["date"].dropna()) & set(inito["date"].dropna())
    overlap_hormone = cycle_calendar[cycle_calendar["hormone_cycle_day"].notna()].copy()
    cycle_start_str = ", ".join(pd.to_datetime(MVP_CYCLE_START_DATES).strftime("%Y-%m-%d").tolist())

    if overlap_hormone.empty:
        hormone_agreement_line = "n/a (no overlap dates)"
    else:
        exact = int((overlap_hormone["cycle_day_delta_vs_hormone"] == 0).sum())
        total = len(overlap_hormone)
        pct = exact / total * 100
        median_abs_delta = overlap_hormone["cycle_day_delta_vs_hormone"].abs().median()
        hormone_agreement_line = (
            f"{exact}/{total} exact ({pct:.1f}%), "
            f"median |delta|={median_abs_delta:.1f} days"
        )

    return (
        "Cycle tracking MVP complete.\n"
        f"- Voice date window: {_date_window(voice)}\n"
        f"- Oura date window: {_date_window(oura)}\n"
        f"- Inito date window: {_date_window(inito)}\n"
        f"- Cycle calendar date window: {_date_window(cycle_calendar)}\n"
        f"- Cycle starts (MVP anchors): {cycle_start_str}\n"
        f"- Three-way date overlap: {len(overlap_dates)} days\n"
        f"- Hormone cycle-day agreement: {hormone_agreement_line}\n"
        f"- Cycle phase counts (calendar): {_phase_count_line(cycle_calendar, 'phase_label')}\n"
        f"- Cycle week counts (calendar): {_phase_count_line(cycle_calendar, 'cycle_week')}\n"
        f"- Phase counts on voice dates: {_phase_count_line(voice_with_cycle, 'phase_label')}\n"
        f"- Week counts on voice dates: {_phase_count_line(voice_with_cycle, 'cycle_week')}\n"
    )


def run(voice_path: Path, inito_path: Path, oura_path: Path, cycle_calendar_out: Path) -> None:
    voice = load_voice_features(voice_path)
    oura = load_oura_from_parquet(oura_path)
    inito = load_inito(inito_path)

    calendar_start, calendar_end = _compute_calendar_range(voice, oura, inito)
    cycle_calendar = build_cycle_calendar_daily(
        start_dates=MVP_CYCLE_START_DATES,
        calendar_start=calendar_start,
        calendar_end=calendar_end,
    )

    hormone_cycle = inito[["date", "cycle_day"]].rename(columns={"cycle_day": "hormone_cycle_day"})
    cycle_calendar = cycle_calendar.merge(hormone_cycle, on="date", how="left")
    cycle_calendar["hormone_cycle_day"] = pd.to_numeric(
        cycle_calendar["hormone_cycle_day"], errors="coerce"
    ).astype("Int64")
    cycle_calendar["cycle_day_delta_vs_hormone"] = (
        cycle_calendar["cycle_day"] - cycle_calendar["hormone_cycle_day"]
    ).astype("Int64")

    voice_with_cycle = voice.merge(
        cycle_calendar[["date", "cycle_day", "cycle_week", "phase_label", "cycle_source"]],
        on="date",
        how="left",
    )

    cycle_calendar_out.parent.mkdir(parents=True, exist_ok=True)
    cycle_calendar.to_parquet(cycle_calendar_out, index=False)

    print(_setup_report(voice, oura, inito, cycle_calendar, voice_with_cycle))
    print(f"- Wrote cycle source-of-truth table: {cycle_calendar_out}")


def main() -> None:
    defaults = default_paths()
    parser = argparse.ArgumentParser(description="Run setup validation for voice-cycle analysis.")
    parser.add_argument("--voice-path", type=Path, default=defaults.voice_parquet)
    parser.add_argument("--inito-path", type=Path, default=defaults.inito_csv)
    parser.add_argument(
        "--oura-path",
        type=Path,
        default=defaults.oura_parquet,
        help="Local Oura parquet snapshot path",
    )
    parser.add_argument(
        "--cycle-calendar-out",
        type=Path,
        default=defaults.processed_dir / "cycle_calendar_daily.parquet",
        help="Output parquet path for source-of-truth cycle calendar",
    )
    args = parser.parse_args()

    run(args.voice_path, args.inito_path, args.oura_path, args.cycle_calendar_out)


if __name__ == "__main__":
    main()
