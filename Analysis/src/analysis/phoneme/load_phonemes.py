"""Load the phoneme-prosody parquet and join it to cycle and hormone context.

Single responsibility: produce one tidy phoneme-grain frame with cycle/phase,
cycle-week, measured hormones, and a numeric drift axis attached by date, plus
the QC gates the handoff documents as mandatory.
"""

from __future__ import annotations

import pandas as pd

from .config import PhonemePaths, default_paths

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


def load_phonemes(paths: PhonemePaths | None = None) -> pd.DataFrame:
    """Return the phoneme-grain frame with cycle + hormone context attached.

    No QC filtering is applied here; callers select the view they need via the
    helper masks below so the QC decision is always explicit in the analysis.
    """
    paths = paths or default_paths()
    df = pd.read_parquet(paths.phoneme_parquet)
    df["date"] = pd.to_datetime(df["recordedDate"], errors="coerce").dt.normalize()

    cal = _load_cycle(paths.cycle_calendar_parquet)
    horm = _load_hormones(paths.hormone_levels_parquet, paths.hormone_change_parquet)

    df = df.merge(cal, on="date", how="left").merge(horm, on="date", how="left")

    # Numeric drift axis: days since the first recording (for date-partial control).
    df["day_index"] = (df["date"] - df["date"].min()).dt.days.astype("Int64")
    return df


def clean_recordings(df: pd.DataFrame) -> pd.DataFrame:
    """Drop the 6 misaligned recordings (wrong-content); mandatory first gate."""
    return df[df["qc_recording_ok"] == True].copy()  # noqa: E712


def analyzable_segments(df: pd.DataFrame) -> pd.DataFrame:
    """Recording-clean AND segment-reliable (>=4 frames): valid for spectral measures."""
    return clean_recordings(df)[lambda d: d["qc_segment_ok"] == True].copy()  # noqa: E712


def voiced(df: pd.DataFrame, feature: str) -> pd.DataFrame:
    """Analyzable segments with a non-null value for a voiced-only feature."""
    return analyzable_segments(df).dropna(subset=[feature]).copy()


if __name__ == "__main__":
    d = load_phonemes()
    clean = clean_recordings(d)
    print("phonemes:", len(d), "| clean:", len(clean))
    print("recordings:", d["recordingId"].nunique(), "| clean:", clean["recordingId"].nunique())
    print("clean days:", clean["date"].nunique())
    rec = clean.drop_duplicates("recordingId")
    print("recording-day phase balance:\n", rec.drop_duplicates(["date"]).groupby(["cycle_start_date", "phase_label"]).size())
