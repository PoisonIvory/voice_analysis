"""CLI tool to export one-time MVP cycle calendar into processed data artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .cycle_calendar import (
    MVP_CYCLE_START_DATES,
    PERIOD_START_GAP_DAYS,
    build_cycle_calendar_daily,
    period_anchors_from_oura,
)


def _merge_anchors(derived: list[str], manual: list[str], gap_days: int) -> list[str]:
    """Merge derived (Oura) and manual anchors, collapsing near-duplicate bleeds.

    Two starts within `gap_days` are the same cycle; when that happens the
    Oura-derived date wins (sensor source of truth), so manual dates only add
    genuinely new cycles rather than perturbing already-validated anchors.
    """
    derived_set = {pd.Timestamp(d).normalize() for d in derived}
    all_dates = sorted(derived_set | {pd.Timestamp(d).normalize() for d in manual})
    kept: list[pd.Timestamp] = []
    for day in all_dates:
        if kept and (day - kept[-1]).days <= gap_days:
            if day in derived_set and kept[-1] not in derived_set:
                kept[-1] = day
            continue
        kept.append(day)
    return [d.date().isoformat() for d in kept]


def _resolve_anchors(oura_path: Path, extra_start_dates: list[str]) -> list[str]:
    """Period-start anchors from Oura tags, merged with any manual pre-sync dates.

    Oura tags are the source of truth; manual dates cover cycles that predate the
    Oura sync window (where the user logged periods in the app but no Oura record
    exists locally). Falls back to the frozen MVP list if Oura yields nothing.
    """
    oura = pd.read_parquet(oura_path)
    derived = [ts.date().isoformat() for ts in period_anchors_from_oura(oura)]
    if not derived:
        derived = list(MVP_CYCLE_START_DATES)
    return _merge_anchors(derived, extra_start_dates, PERIOD_START_GAP_DAYS)


def _resolve_date_window(
    oura_path: Path,
    start_date: str | None,
    end_date: str | None,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    if start_date and end_date:
        start = pd.Timestamp(start_date).normalize()
        end = pd.Timestamp(end_date).normalize()
        if end < start:
            raise ValueError("end-date must be on or after start-date")
        return start, end

    oura = pd.read_parquet(oura_path)
    if "day" in oura.columns:
        date_col = "day"
    elif "date" in oura.columns:
        date_col = "date"
    else:
        raise ValueError("Oura parquet must contain 'day' or 'date' to infer calendar window")

    dates = pd.to_datetime(oura[date_col], format="mixed", errors="coerce").dropna()
    if dates.empty:
        raise ValueError("Oura parquet has no valid dates to infer calendar window")

    inferred_start = dates.min().normalize()
    inferred_end = dates.max().normalize()

    start = pd.Timestamp(start_date).normalize() if start_date else inferred_start
    end = pd.Timestamp(end_date).normalize() if end_date else inferred_end
    if end < start:
        raise ValueError("Resolved end-date is before start-date")
    return start, end


def export_cycle_calendar(
    output_path: Path,
    oura_path: Path,
    start_date: str | None,
    end_date: str | None,
    extra_start_dates: list[str] | None = None,
) -> None:
    anchors = _resolve_anchors(oura_path, extra_start_dates or [])
    calendar_start, calendar_end = _resolve_date_window(oura_path, start_date, end_date)
    # Cover the full span from the earliest period start so cycles that predate the
    # Oura sync window still produce labeled days for voice recordings made then.
    earliest_anchor = pd.Timestamp(anchors[0]).normalize()
    calendar_start = min(calendar_start, earliest_anchor)
    cycle_calendar = build_cycle_calendar_daily(
        start_dates=anchors,
        calendar_start=calendar_start,
        calendar_end=calendar_end,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cycle_calendar.to_parquet(output_path, index=False)

    phase_counts = cycle_calendar["phase_label"].value_counts(dropna=False).to_dict()
    week_counts = cycle_calendar["cycle_week"].value_counts(dropna=False).to_dict()
    print("Cycle calendar export complete.")
    print(f"- Output: {output_path}")
    print(f"- Date window: {calendar_start.date()} to {calendar_end.date()}")
    print(f"- Rows: {len(cycle_calendar)}")
    print(f"- Cycle starts: {', '.join(anchors)}")
    print(f"- Phase counts: {phase_counts}")
    print(f"- Week counts: {week_counts}")


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Export source-of-truth cycle calendar parquet.")
    parser.add_argument(
        "--output-path",
        type=Path,
        default=root / "data" / "processed" / "cycle_calendar_daily.parquet",
        help="Destination parquet path for cycle calendar",
    )
    parser.add_argument(
        "--oura-path",
        type=Path,
        default=root / "data" / "raw" / "oura_daily_summaries_20260601.parquet",
        help="Oura parquet used to infer date window when dates are not provided",
    )
    parser.add_argument("--start-date", type=str, default=None, help="Optional inclusive start date YYYY-MM-DD")
    parser.add_argument("--end-date", type=str, default=None, help="Optional inclusive end date YYYY-MM-DD")
    parser.add_argument(
        "--extra-start-dates",
        type=str,
        default=None,
        help="Comma-separated period-start dates (YYYY-MM-DD) for cycles predating the Oura sync window",
    )
    args = parser.parse_args()

    extra = [d.strip() for d in args.extra_start_dates.split(",")] if args.extra_start_dates else []
    export_cycle_calendar(args.output_path, args.oura_path, args.start_date, args.end_date, extra)


if __name__ == "__main__":
    main()
