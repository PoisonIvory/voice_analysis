"""Level 2 - localize the cycle signal within the phonetic inventory.

For each (feature, phoneme class) we compute, at the day grain:
- raw luteal-vs-follicular Cliff's delta,
- the same contrast after removing each recording's own mean for that feature
  (the "de-meaning" test: how much of a class effect is just a recording-wide
  offset re-expressed at that class vs a phoneme-selective change),
- within-cycle-normalized luteal-follicular shift in each balanced cycle,
- drift-controlled progesterone coupling,
- Mann-Whitney p and a BH-FDR q across the whole (feature x class) grid.

The de-meaning column subtracts, per recording, the mean of the SAME feature
over the phonemes for which it is defined (voiced segments for the voiced-only
features), i.e. the recording-wide setting of that feature.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from ..stats import benjamini_hochberg, cliffs_delta, cliffs_magnitude, partial_spearman
from .aggregation import day_series, within_cycle_phase_shift
from .taxonomy import PRIMARY_FEATURES

CLASS_SETS: dict[str, list[str]] = {
    "phonemeManner": ["vowel", "diphthong", "nasal", "approximant", "stop", "fricative"],
    "phonemeVoicing": ["voiced", "voiceless"],
    "phonemeBroadClass": ["sonorant", "obstruent"],
    "phonemeHeight": ["high", "mid", "low"],
}


def _add_recording_demeaned(df: pd.DataFrame, feature: str) -> pd.DataFrame:
    """Add `<feature>__demeaned` = value minus the recording's mean for that feature."""
    out = df.copy()
    rec_mean = out.groupby("recordingId")[feature].transform("mean")
    out[f"{feature}__demeaned"] = out[feature] - rec_mean
    return out


def _phase_delta(day: pd.DataFrame, feature: str) -> tuple[float, int, int, float]:
    d = day.dropna(subset=[feature, "phase_label"])
    lut = d.loc[d["phase_label"] == "luteal", feature].to_numpy(float)
    fol = d.loc[d["phase_label"] == "follicular", feature].to_numpy(float)
    cd = cliffs_delta(lut, fol)
    if lut.size and fol.size:
        try:
            _, p = stats.mannwhitneyu(lut, fol, alternative="two-sided")
        except ValueError:
            p = np.nan
    else:
        p = np.nan
    return cd, int(fol.size), int(lut.size), float(p)


def localize(df: pd.DataFrame, features: list[str] | None = None) -> pd.DataFrame:
    features = features or PRIMARY_FEATURES
    rows = []
    for feature in features:
        dfd = _add_recording_demeaned(df, feature)
        for class_col, class_vals in CLASS_SETS.items():
            # voiced-only features are undefined for the voiceless class
            for class_val in class_vals:
                mask = dfd[class_col] == class_val
                if mask.sum() == 0:
                    continue
                day_raw = day_series(dfd, feature, subset=mask)
                if day_raw[feature].notna().sum() < 8:
                    continue
                cd, nf, nl, p = _phase_delta(day_raw, feature)
                day_dm = day_series(dfd, f"{feature}__demeaned", subset=mask)
                cd_dm, _, _, _ = _phase_delta(day_dm, f"{feature}__demeaned")
                wc = within_cycle_phase_shift(day_raw, feature)
                pr, n_h = partial_spearman(day_raw.dropna(subset=["pdg"]), feature, "pdg", "day_index")
                rows.append(
                    {
                        "feature": feature,
                        "class_axis": class_col,
                        "phoneme_class": class_val,
                        "n_follicular_days": nf,
                        "n_luteal_days": nl,
                        "cliffs_delta_raw": round(cd, 3),
                        "magnitude_raw": cliffs_magnitude(cd),
                        "cliffs_delta_demeaned": round(cd_dm, 3),
                        "wc_shift_jan": round(wc["2026-01-14"], 3),
                        "wc_shift_feb": round(wc["2026-02-12"], 3),
                        "wc_consistent": bool(
                            np.sign(wc["2026-01-14"]) == np.sign(wc["2026-02-12"])
                            and not np.isnan(wc["2026-01-14"]) and not np.isnan(wc["2026-02-12"])
                        ),
                        "pdg_partial_rho": round(pr, 3) if not np.isnan(pr) else np.nan,
                        "pdg_n": int(n_h),
                        "mann_whitney_p": round(p, 4) if not np.isnan(p) else np.nan,
                    }
                )
    out = pd.DataFrame(rows)
    out["bh_q"] = benjamini_hochberg(out["mann_whitney_p"].to_numpy()).round(4)
    return out.sort_values(["feature", "class_axis", "phoneme_class"]).reset_index(drop=True)
