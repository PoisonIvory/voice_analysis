from __future__ import annotations

import numpy as np
import pandas as pd


def _contains_period_tag(tag_text: str) -> bool:
    return "period" in tag_text.lower()


def _infer_cycle_group(df: pd.DataFrame) -> pd.Series:
    cycle_start = (df["cycle_day"] == 1).fillna(False)
    return cycle_start.cumsum()


def _phase_for_row(row: pd.Series) -> str:
    cycle_day = row.get("cycle_day")
    lh = row.get("lh")
    pdg = row.get("pdg")
    period_tag = row.get("period_tag", False)
    ovulation_day = row.get("ovulation_cycle_day")

    if period_tag:
        return "menstrual"

    if pd.notna(cycle_day) and cycle_day <= 5:
        return "menstrual"

    if pd.notna(cycle_day) and pd.notna(ovulation_day):
        if abs(cycle_day - ovulation_day) <= 1:
            return "ovulatory"
        if cycle_day > ovulation_day and pd.notna(pdg) and pdg >= 5:
            return "luteal"
        if cycle_day < ovulation_day:
            return "follicular"

    if pd.notna(lh) and lh >= 10:
        return "ovulatory"

    if pd.notna(pdg) and pdg >= 7:
        return "luteal"

    return "follicular"


def assign_cycle_phase(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["tags"] = out.get("tags", "").fillna("").astype(str)
    out["period_tag"] = out["tags"].apply(_contains_period_tag)
    out["cycle_group"] = _infer_cycle_group(out)

    ov_day_by_group = (
        out.dropna(subset=["cycle_day", "lh"])
        .sort_values(["cycle_group", "lh"], ascending=[True, False])
        .groupby("cycle_group", as_index=False)
        .first()[["cycle_group", "cycle_day"]]
        .rename(columns={"cycle_day": "ovulation_cycle_day"})
    )
    out = out.merge(ov_day_by_group, on="cycle_group", how="left")
    out["cycle_phase"] = out.apply(_phase_for_row, axis=1)

    phase_order = ["menstrual", "follicular", "ovulatory", "luteal"]
    out["cycle_phase"] = pd.Categorical(out["cycle_phase"], categories=phase_order, ordered=True)
    return out


def cycle_window(df: pd.DataFrame) -> pd.DataFrame:
    mask = df["lh"].notna() | df["pdg"].notna() | df["e3g"].notna()
    return df[mask].copy()

