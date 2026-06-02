"""Within-recording self-normalizing contrasts (the methodological core).

Each recording contains many phonemes, so we can form contrasts *inside* a
recording - e.g. (voiced - voiceless) timbre, (high - low vowel) open quotient.
Because both groups come from the same recording, any recording-wide offset
(mic gain, distance, overall level, day-to-day technique, slow drift) cancels
exactly. A contrast that still moves with phase/progesterone is therefore a
change in the *relative* acoustics between phoneme categories, not a global
shift. This is a stronger confound control than anything the whole-file series
can express, and it is the test that separates "global per-recording shift"
from "phoneme-structure reorganization".

We also report within-recording dispersion (phoneme-to-phoneme SD), a second
quantity invisible to whole-file means.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from ..stats import cliffs_delta, cliffs_magnitude, partial_spearman
from .aggregation import BALANCED_CYCLES
from .taxonomy import CONTRAST_SPECS

REC_META = ["date", "phase_label", "cycle_start_date", "day_index", "pdg", "e3g"]


def _predicate(df: pd.DataFrame, key: str) -> pd.Series:
    table = {
        "voiced": df["phonemeVoicing"] == "voiced",
        "voiceless": df["phonemeVoicing"] == "voiceless",
        "high_vowel": df["phonemeHeight"] == "high",
        "low_vowel": df["phonemeHeight"] == "low",
        "nasal_adjacent_vowel": (df["phonemeManner"] == "vowel") & (df["coarticulationContext"] != "none"),
        "oral_vowel": (df["phonemeManner"] == "vowel") & (df["coarticulationContext"] == "none"),
        "sonorant": df["phonemeBroadClass"] == "sonorant",
        "obstruent": df["phonemeBroadClass"] == "obstruent",
    }
    return table[key]


def _recording_contrast(df: pd.DataFrame, feature: str, key_a: str, key_b: str, name: str) -> pd.DataFrame:
    a = df[_predicate(df, key_a)].dropna(subset=[feature]).groupby("recordingId")[feature].mean()
    b = df[_predicate(df, key_b)].dropna(subset=[feature]).groupby("recordingId")[feature].mean()
    contrast = (a - b).rename(name)
    meta = df.drop_duplicates("recordingId").set_index("recordingId")[REC_META]
    rec = meta.join(contrast, how="inner").dropna(subset=[name]).reset_index()
    # day grain: average the contrast over recordings in a day
    day = rec.groupby("date", as_index=False).agg(
        {name: "mean", "phase_label": "first", "cycle_start_date": "first",
         "day_index": "first", "pdg": "first", "e3g": "first"}
    )
    return day


def _summarize(day: pd.DataFrame, name: str) -> dict:
    d = day.dropna(subset=[name, "phase_label"])
    lut = d.loc[d["phase_label"] == "luteal", name].to_numpy(float)
    fol = d.loc[d["phase_label"] == "follicular", name].to_numpy(float)
    cd = cliffs_delta(lut, fol)
    signs = []
    cyc = d["cycle_start_date"].astype(str).str[:10]
    for cs in BALANCED_CYCLES:
        g = d[cyc == cs]
        gl = g.loc[g["phase_label"] == "luteal", name]
        gf = g.loc[g["phase_label"] == "follicular", name]
        if len(gl) and len(gf):
            signs.append(int(np.sign(gl.median() - gf.median())))
    sub = day.dropna(subset=[name, "pdg"])
    raw = stats.spearmanr(sub[name], sub["pdg"]).statistic if len(sub) >= 5 else np.nan
    pr, n_h = partial_spearman(day, name, "pdg", "day_index")
    return {
        "n_follicular_days": int(fol.size),
        "n_luteal_days": int(lut.size),
        "cliffs_delta_phase": round(cd, 3),
        "magnitude": cliffs_magnitude(cd),
        "balanced_cycle_signs": signs,
        "cross_cycle_consistent": len(signs) == 2 and signs[0] == signs[1],
        "pdg_n": int(n_h),
        "pdg_raw_rho": round(float(raw), 3) if not np.isnan(raw) else np.nan,
        "pdg_partial_rho": round(float(pr), 3) if not np.isnan(pr) else np.nan,
    }


def contrast_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for spec in CONTRAST_SPECS:
        day = _recording_contrast(df, spec["feature"], spec["group_a"], spec["group_b"], spec["name"])
        summary = _summarize(day, spec["name"])
        rows.append({"contrast": spec["name"], "feature": spec["feature"],
                     "rationale": spec["rationale"], **summary})
    return pd.DataFrame(rows)


def dispersion_table(df: pd.DataFrame, feature: str = "segment_h1h2_mean",
                     manner: str = "vowel") -> pd.DataFrame:
    """Phase contrast on within-recording phoneme-to-phoneme SD of a feature."""
    sub = df[df["phonemeManner"] == manner].dropna(subset=[feature])
    sd = sub.groupby("recordingId")[feature].std(ddof=0).rename("within_rec_sd")
    meta = df.drop_duplicates("recordingId").set_index("recordingId")[REC_META]
    rec = meta.join(sd, how="inner").dropna(subset=["within_rec_sd"]).reset_index()
    day = rec.groupby("date", as_index=False).agg(
        {"within_rec_sd": "mean", "phase_label": "first", "cycle_start_date": "first",
         "day_index": "first", "pdg": "first", "e3g": "first"}
    )
    summary = _summarize(day, "within_rec_sd")
    return pd.DataFrame([{"quantity": f"within_recording_sd_{manner}_{feature}", **summary}])
