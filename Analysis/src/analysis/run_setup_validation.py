"""CLI entrypoint that validates input coverage and emits cycle diagnostics."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .config import default_paths
from .load_data import load_cycle_calendar, load_inito, load_oura_from_parquet, load_voice_features


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


def _setup_report(
    voice: pd.DataFrame,
    oura: pd.DataFrame,
    inito: pd.DataFrame,
    cycle_calendar: pd.DataFrame,
    voice_with_cycle: pd.DataFrame,
) -> str:
    overlap_dates = set(voice["date"].dropna()) & set(oura["date"].dropna()) & set(inito["date"].dropna())
    overlap_hormone = cycle_calendar[cycle_calendar["hormone_cycle_day"].notna()].copy()
    cycle_starts = sorted(cycle_calendar["cycle_start_date"].dropna().dt.strftime("%Y-%m-%d").unique().tolist())
    cycle_start_str = ", ".join(cycle_starts) if cycle_starts else "n/a"

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


def run(voice_path: Path, inito_path: Path, oura_path: Path, cycle_calendar_path: Path) -> None:
    voice = load_voice_features(voice_path)
    oura = load_oura_from_parquet(oura_path)
    inito = load_inito(inito_path)
    cycle_calendar = load_cycle_calendar(cycle_calendar_path)

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

    print(_setup_report(voice, oura, inito, cycle_calendar, voice_with_cycle))
    print(f"- Cycle source-of-truth table: {cycle_calendar_path}")


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
        "--cycle-calendar-path",
        type=Path,
        default=defaults.cycle_calendar_parquet,
        help="Input parquet path for source-of-truth cycle calendar",
    )
    args = parser.parse_args()

    run(args.voice_path, args.inito_path, args.oura_path, args.cycle_calendar_path)


if __name__ == "__main__":
    main()
