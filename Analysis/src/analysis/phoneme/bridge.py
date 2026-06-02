"""Level 1 - bridge the phoneme grain back to the whole-recording pipeline.

Two jobs:
1. Validation: aggregate phoneme features to the day grain and correlate with
   the independently-produced whole-file eGeMAPS prosody features. High
   agreement shows the phoneme extractor and the production pipeline measure the
   same thing, so phoneme-level results inherit the whole-file study's trust.
2. Global drift + hormone coupling of each phoneme feature (day grain), which
   anchors the localization analysis and exposes the drift each feature carries.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from ..stats import partial_spearman
from .aggregation import day_series
from .config import PhonemePaths, default_paths

# phoneme feature -> whole-file prosody eGeMAPS column it should reproduce
BRIDGE_PAIRS = {
    "segment_h1h2_mean": "prosody_egemaps_logRelF0-H1-H2_sma3nz_amean",
    "segment_f0_mean": "prosody_egemaps_F0semitoneFrom27.5Hz_sma3nz_amean",
    "segment_f1_bandwidth_mean": "prosody_egemaps_F1bandwidth_sma3nz_amean",
}

GLOBAL_FEATURES = [
    "segment_h1h2_mean",
    "segment_mfcc2_mean",
    "segment_f1_bandwidth_mean",
    "segment_f0_mean",
]


def bridge_validation(df: pd.DataFrame, paths: PhonemePaths | None = None) -> pd.DataFrame:
    paths = paths or default_paths()
    wr = pd.read_parquet(paths.whole_recording_daily_parquet)
    wr["date"] = pd.to_datetime(wr["date"], errors="coerce").dt.normalize()
    wr = wr.set_index("date")

    rows = []
    for pf, wf in BRIDGE_PAIRS.items():
        if wf not in wr.columns:
            continue
        day = day_series(df, pf).set_index("date")[[pf]]
        j = day.join(wr[[wf]]).dropna()
        if len(j) < 5:
            continue
        rows.append(
            {
                "phoneme_feature": pf,
                "whole_file_feature": wf,
                "n_days": len(j),
                "pearson_r": float(stats.pearsonr(j[pf], j[wf])[0]),
                "spearman_rho": float(stats.spearmanr(j[pf], j[wf]).statistic),
            }
        )
    return pd.DataFrame(rows)


def global_coupling(df: pd.DataFrame) -> pd.DataFrame:
    """Drift and drift-controlled hormone coupling for each global feature."""
    rows = []
    for f in GLOBAL_FEATURES:
        day = day_series(df, f)
        drift = stats.spearmanr(day[f], day["day_index"].astype(float)).statistic
        for h in ["pdg", "e3g"]:
            sub = day.dropna(subset=[f, h])
            n = len(sub)
            if n < 5:
                rows.append({"feature": f, "hormone": h, "n": n, "raw_rho": np.nan,
                             "date_partial_rho": np.nan, "feature_drift": drift})
                continue
            raw = stats.spearmanr(sub[f], sub[h]).statistic
            partial, _ = partial_spearman(day, f, h, "day_index")
            rows.append({"feature": f, "hormone": h, "n": n, "raw_rho": float(raw),
                         "date_partial_rho": float(partial), "feature_drift": float(drift)})
    return pd.DataFrame(rows)
