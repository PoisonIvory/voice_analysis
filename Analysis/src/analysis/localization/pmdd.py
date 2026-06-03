"""Thread 4 - the PMDD lens: amplified, late-luteal, central.

PMDD is an abnormal sensitivity to the normal luteal rise/fall of progesterone-
derived neurosteroids (allopregnanolone -> GABA-A), acting through the central
pathway. Predictions: the voice perturbation concentrates in the late-luteal /
premenstrual window and in the central pitch-control arm, and may look larger or
different from Kervin's normal-cycling (trained, compensating) singer. The body
(HRV) is shown only as secondary corroboration that the cycle is real.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..feature_taxonomy import with_task
from ..stats import cliffs_delta
from .config import CENTRAL_SET, PERIPHERAL_COVER, TIMBRE
from .dataset import standardized_phase_effect
from .rate_variability import _z_within_cycle_all

# Features tracked across the premenstrual window (plain-language labels).
_PERI_FEATURES = {
    "egemaps_logRelF0-H1-H2_sma3nz_amean": ("cover", "Open quotient (H1-H2)"),
    "egemaps_HNRdBACF_sma3nz_amean": ("cover", "Clarity (HNR)"),
    "egemaps_mfcc2V_sma3nz_amean": ("cover", "Timbre (MFCC2)"),
    "egemaps_F0semitoneFrom27.5Hz_sma3nz_stddevNorm": ("central", "Pitch variability (F0 SD)"),
    "egemaps_F0semitoneFrom27.5Hz_sma3nz_meanFallingSlope": ("central", "Pitch falling slope"),
}


def _luteal_window(row) -> str:
    dn = row.get("days_to_next_start")
    if row.get("phase_label") == "follicular":
        return "follicular"
    dn = None if pd.isna(dn) else int(dn)
    if dn is not None and dn <= 4:
        return "premenstrual"
    if dn is not None and 5 <= dn <= 10:
        return "mid_luteal"
    return "other"


def premenstrual_window(df: pd.DataFrame, task: str) -> pd.DataFrame:
    """Median within-cycle-z of cover and central features by luteal sub-window."""
    work = df[df["phase_label"].notna()].copy()
    work["window"] = work.apply(_luteal_window, axis=1)
    rows = []
    for base, (arm, label) in _PERI_FEATURES.items():
        col = with_task(base, task)
        work[f"_z_{base}"] = _z_within_cycle_all(work, col)
        med = work.groupby("window")[f"_z_{base}"].median()
        rows.append({
            "arm": arm, "feature": base, "label": label, "task": task,
            "follicular_z": float(med.get("follicular", np.nan)),
            "mid_luteal_z": float(med.get("mid_luteal", np.nan)),
            "premenstrual_z": float(med.get("premenstrual", np.nan)),
            "premenstrual_minus_follicular": float(med.get("premenstrual", np.nan) - med.get("follicular", np.nan)),
        })
    return pd.DataFrame(rows)


def kervin_contrast(df: pd.DataFrame, task: str) -> pd.DataFrame:
    """Our luteal directions beside Kervin 2025's reported normal-cycling pattern."""
    def direction(base):
        eff = standardized_phase_effect(df, base, task)
        if eff is None:
            return np.nan, "insufficient data"
        d = eff["std_mean_diff"]
        return d, ("higher in luteal" if d > 0 else "lower in luteal")

    f0_d, f0_dir = direction("egemaps_F0semitoneFrom27.5Hz_sma3nz_amean")
    hnr_d, hnr_dir = direction("egemaps_HNRdBACF_sma3nz_amean")
    h1h2_d, h1h2_dir = direction("egemaps_logRelF0-H1-H2_sma3nz_amean")

    return pd.DataFrame([
        {"measure": "Pitch (F0), luteal", "kervin_normal_cycling": "highest in luteal",
         "ours_pmdd": f0_dir, "ours_value_sd": f0_d},
        {"measure": "Clarity (Kervin CPPS / our HNR), luteal", "kervin_normal_cycling": "best near fertile window",
         "ours_pmdd": hnr_dir, "ours_value_sd": hnr_d},
        {"measure": "Glottal closure / open quotient, luteal",
         "kervin_normal_cycling": "GAI lowest in luteal (more closure, kinematic)",
         "ours_pmdd": f"open quotient {h1h2_dir} (acoustic)", "ours_value_sd": h1h2_d},
    ])


def hrv_context(df: pd.DataFrame) -> pd.DataFrame:
    """Secondary corroboration: the body's autonomic shift across the phase."""
    rows = []
    for col, label, kervin_note in [
        ("temp_trend_deviation", "Body temperature trend", "classic luteal rise (positive control)"),
        ("hrv", "Heart-rate variability (HRV)", "luteal dip; PMDD linked to blunted/dysregulated HRV"),
        ("average_hr", "Daytime heart rate", "classic luteal rise (positive control)"),
    ]:
        if col not in df.columns:
            continue
        sub = df[[col, "phase_label"]].dropna()
        foll = sub.loc[sub["phase_label"] == "follicular", col].to_numpy(float)
        lut = sub.loc[sub["phase_label"] == "luteal", col].to_numpy(float)
        if foll.size < 3 or lut.size < 3:
            continue
        rows.append({
            "signal": label,
            "median_follicular": float(np.median(foll)),
            "median_luteal": float(np.median(lut)),
            "cliffs_delta_luteal_vs_foll": float(cliffs_delta(lut, foll)),
            "n_foll": int(foll.size), "n_lut": int(lut.size),
            "note": kervin_note,
        })
    return pd.DataFrame(rows)
