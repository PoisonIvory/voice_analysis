"""Utilities for building the one-time MVP cycle calendar dataset."""

from __future__ import annotations

import json
from collections.abc import Sequence

import pandas as pd


MVP_CYCLE_START_DATES: tuple[str, ...] = (
    "2025-12-18",
    "2026-01-14",
    "2026-02-12",
    "2026-03-09",
    "2026-04-11",
    "2026-05-11",
)

# Oura tag emitted on logged menstruation days.
OURA_PERIOD_TAG = "tag_generic_period"
# Consecutive period days within this gap belong to one bleed, not a new cycle.
PERIOD_START_GAP_DAYS = 3
# In an open (still-running) final cycle we cannot apply the last-14-days luteal
# rule, but the first days of a cycle are menstruation/early-follicular regardless
# of cycle length, so they are safe to label.
OPEN_CYCLE_FOLLICULAR_MAX_DAY = 7


def _row_has_period_tag(value: object) -> bool:
    if isinstance(value, (list, tuple)):
        tags = value
    elif isinstance(value, str):
        try:
            tags = json.loads(value)
        except (ValueError, TypeError):
            return False
    else:
        return False
    return OURA_PERIOD_TAG in tags


def period_anchors_from_oura(
    oura: pd.DataFrame, gap_days: int = PERIOD_START_GAP_DAYS
) -> list[pd.Timestamp]:
    """Derive cycle-start anchors from Oura period tags (the source of truth).

    A start is the first day of a run of period days; days within `gap_days` of
    the previous period day are treated as the same bleed.
    """
    day_col = "day" if "day" in oura.columns else "date" if "date" in oura.columns else None
    if day_col is None or "tags" not in oura.columns:
        return []
    days = pd.to_datetime(oura[day_col], format="mixed", errors="coerce")
    period_days = sorted(
        days[oura["tags"].map(_row_has_period_tag)].dropna().dt.normalize().unique()
    )
    anchors: list[pd.Timestamp] = []
    for raw in period_days:
        day = pd.Timestamp(raw)
        if not anchors or (day - anchors[-1]).days > gap_days:
            anchors.append(day)
    return anchors


def _normalize_start_dates(start_dates: Sequence[str | pd.Timestamp]) -> list[pd.Timestamp]:
    if not start_dates:
        raise ValueError("At least one cycle start date is required")

    normalized = sorted({pd.Timestamp(value).normalize() for value in start_dates})
    if len(normalized) < 2:
        raise ValueError("At least two cycle start dates are required to compute luteal boundaries")
    return normalized


def _cycle_week_label(cycle_day: pd.Series) -> pd.Series:
    week_number = ((cycle_day - 1) // 7) + 1
    return "week_" + week_number.astype("Int64").astype(str)


def build_cycle_calendar_daily(
    start_dates: Sequence[str | pd.Timestamp] = MVP_CYCLE_START_DATES,
    calendar_start: pd.Timestamp | None = None,
    calendar_end: pd.Timestamp | None = None,
) -> pd.DataFrame:
    anchors = _normalize_start_dates(start_dates)
    first_anchor = anchors[0]
    last_anchor = anchors[-1]

    if calendar_start is None:
        calendar_start = first_anchor
    else:
        calendar_start = pd.Timestamp(calendar_start).normalize()

    if calendar_end is None:
        calendar_end = last_anchor
    else:
        calendar_end = pd.Timestamp(calendar_end).normalize()

    if calendar_end < calendar_start:
        raise ValueError("calendar_end must be on or after calendar_start")

    rows: list[dict[str, object]] = []
    for idx, cycle_start in enumerate(anchors):
        next_start = anchors[idx + 1] if idx + 1 < len(anchors) else pd.NaT

        cycle_range_start = max(cycle_start, calendar_start)
        if pd.isna(next_start):
            cycle_range_end = calendar_end
        else:
            cycle_range_end = min(next_start - pd.Timedelta(days=1), calendar_end)

        if cycle_range_end < cycle_range_start:
            continue

        for date in pd.date_range(cycle_range_start, cycle_range_end, freq="D"):
            cycle_day = int((date - cycle_start).days + 1)
            days_to_next_start = int((next_start - date).days) if pd.notna(next_start) else pd.NA
            rows.append(
                {
                    "date": date,
                    "cycle_start_date": cycle_start,
                    "next_cycle_start_date": next_start,
                    "cycle_day": cycle_day,
                    "days_to_next_start": days_to_next_start,
                    "cycle_source": "oura_period_anchor",
                }
            )

    out = pd.DataFrame.from_records(rows)
    if out.empty:
        return out

    out["cycle_day"] = out["cycle_day"].astype("Int64")
    out["days_to_next_start"] = out["days_to_next_start"].astype("Int64")
    out["phase_label"] = pd.Series(pd.NA, index=out.index, dtype="string")
    luteal_mask = out["days_to_next_start"].between(1, 14, inclusive="both")
    known_cycle_mask = out["days_to_next_start"].notna()
    out.loc[known_cycle_mask, "phase_label"] = "follicular"
    out.loc[luteal_mask, "phase_label"] = "luteal"

    # Open final cycle (no next start yet): label only the early, unambiguously
    # follicular days; later days stay unlabeled until the next period is known.
    open_cycle_mask = out["next_cycle_start_date"].isna()
    open_follicular_mask = open_cycle_mask & out["cycle_day"].le(OPEN_CYCLE_FOLLICULAR_MAX_DAY)
    out.loc[open_follicular_mask, "phase_label"] = "follicular"
    out["phase_label"] = out["phase_label"].astype("string")
    out["cycle_week"] = _cycle_week_label(out["cycle_day"]).astype("string")

    out = out.sort_values("date").reset_index(drop=True)
    return out
