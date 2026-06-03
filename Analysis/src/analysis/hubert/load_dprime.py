"""Load the per-backbone d-prime tables and join cycle + hormone context.

Single responsibility: produce one tidy per-recording frame stacking all SSL
backbones, with cycle/phase, cycle-week, measured hormones, a numeric drift
axis, and the composite consonant d-prime attached. The d-prime tables are the
upstream contract; no QC filtering is needed here because the fixed passage
yields near-constant token counts and the upstream pipeline already drops the
misaligned recordings before pooling embeddings.
"""

from __future__ import annotations

import pandas as pd

from .config import PRIMARY_BACKBONE, HubertPaths, default_paths
from .taxonomy import COMPOSITE_CONSONANT, CONSONANT_CONTRASTS, dprime_col

CYCLE_KEEP = [
    "date",
    "cycle_start_date",
    "phase_label",
    "cycle_week",
    "cycle_day",
    "days_to_next_start",
]


def _load_cycle(path) -> pd.DataFrame:
    cal = pd.read_parquet(path)
    cal["date"] = pd.to_datetime(cal["date"], format="mixed", errors="coerce").dt.normalize()
    cal["cycle_start_date"] = pd.to_datetime(
        cal["cycle_start_date"], format="mixed", errors="coerce"
    ).dt.normalize()
    keep = [c for c in CYCLE_KEEP if c in cal.columns]
    return cal[keep].dropna(subset=["date"]).drop_duplicates("date")


def _load_hormones(levels_path, change_path) -> pd.DataFrame:
    lvl = pd.read_parquet(levels_path)
    lvl["date"] = pd.to_datetime(lvl["date"], errors="coerce").dt.normalize()
    out = lvl[["date", "e3g", "pdg"]].copy()
    try:
        chg = pd.read_parquet(change_path)
        chg["date"] = pd.to_datetime(chg["date"], errors="coerce").dt.normalize()
        out = out.merge(chg, on="date", how="left")
    except FileNotFoundError:
        pass
    return out


def add_composite(df: pd.DataFrame) -> pd.DataFrame:
    """Add the mean-of-five-consonant-d-primes composite column."""
    cols = [dprime_col(k) for k in CONSONANT_CONTRASTS]
    df[COMPOSITE_CONSONANT] = df[cols].mean(axis=1)
    return df


def load_dprime(paths: HubertPaths | None = None) -> pd.DataFrame:
    """Return the per-recording d-prime frame for all backbones, cycle-joined.

    One row per (recording, backbone). Carries a ``backbone`` label, the cycle
    calendar fields, measured hormones, a ``day_index`` drift axis, and the
    consonant composite.
    """
    paths = paths or default_paths()

    frames: list[pd.DataFrame] = []
    for backbone, parquet in paths.dprime_parquets.items():
        table = pd.read_parquet(parquet)
        table["backbone"] = backbone
        frames.append(table)
    df = pd.concat(frames, ignore_index=True)

    df["date"] = pd.to_datetime(df["recordedDate"], errors="coerce").dt.normalize()
    cal = _load_cycle(paths.cycle_calendar_parquet)
    horm = _load_hormones(paths.hormone_levels_parquet, paths.hormone_change_parquet)
    df = df.merge(cal, on="date", how="left").merge(horm, on="date", how="left")

    df["day_index"] = (df["date"] - df["date"].min()).dt.days.astype("Int64")
    return add_composite(df)


def backbone(df: pd.DataFrame, name: str) -> pd.DataFrame:
    """Single-backbone view of the stacked frame."""
    return df[df["backbone"] == name].copy()


def primary(df: pd.DataFrame) -> pd.DataFrame:
    """The primary (HuBERT-base) backbone view."""
    return backbone(df, PRIMARY_BACKBONE)


if __name__ == "__main__":
    d = load_dprime()
    prim = primary(d)
    print("rows (all backbones):", len(d), "| backbones:", sorted(d["backbone"].unique()))
    print("primary recordings:", prim["recordingId"].nunique(), "| days:", prim["date"].nunique())
    days = prim.drop_duplicates("date")
    print("phase balance by cycle (days):")
    print(
        days.dropna(subset=["phase_label"])
        .groupby([days["cycle_start_date"].astype(str).str[:10], "phase_label"])
        .size()
    )
