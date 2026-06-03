"""Does the menstrual cycle move phonological separability?

Single responsibility: for one backbone, test each contrast's d-prime (and the
consonant composite) for a luteal-vs-follicular difference and for hormone
coupling, at the day grain (recordings averaged within a day) to avoid
pseudo-replication. Reuses the shared N-of-1 engine and the phoneme study's
day-grain aggregation so the machinery is identical to the sibling analyses.

The headline is expected to be a near-null (H1): unlike dysarthria, the cycle is
a global phonatory setting, not articulatory degradation, so representational
separability should be stable. The cycle-privileged contrasts (voicing,
nasality) and the geometry controls (vowel height/lowness/backness) are tagged
so the pattern of any movement can be read against the prior mechanism.
"""

from __future__ import annotations

import pandas as pd
from scipy import stats

from ..phoneme.aggregation import BALANCED_CYCLES, day_series, within_cycle_phase_shift
from ..stats import benjamini_hochberg, partial_spearman, phase_contrast
from .taxonomy import COMPOSITE_CONSONANT, USABLE_CONTRASTS, dprime_col, label, role

# Composite first, then every usable single contrast.
_FEATURES: list[tuple[str, str, str]] = [
    (COMPOSITE_CONSONANT, "Consonant composite (mean of 5)", "composite"),
    *[(dprime_col(k), label(k), role(k)) for k in USABLE_CONTRASTS],
]


def phase_table(df_backbone: pd.DataFrame) -> pd.DataFrame:
    """Per-contrast luteal-vs-follicular contrast at the day grain, with BH-FDR.

    Cliff's delta is luteal-minus-follicular (positive = higher in luteal).
    Per-cycle within-cycle-normalized shifts isolate the two phase-balanced
    cycles; ``cycles_consistent`` counts cycles agreeing in sign with the pool.
    """
    rows: list[dict[str, object]] = []
    for feature, feature_label, feature_role in _FEATURES:
        day = day_series(df_backbone, feature)
        pc = phase_contrast(day, feature)
        shifts = within_cycle_phase_shift(day, feature)
        rows.append(
            {
                "feature": feature,
                "label": feature_label,
                "role": feature_role,
                "n_follicular_days": pc.n_follicular,
                "n_luteal_days": pc.n_luteal,
                "cliffs_delta": round(pc.cliffs_delta, 3),
                "magnitude": pc.magnitude,
                "mann_whitney_p": pc.mann_whitney_p,
                "shift_jan_sd": round(shifts.get(BALANCED_CYCLES[0], float("nan")), 3),
                "shift_feb_sd": round(shifts.get(BALANCED_CYCLES[1], float("nan")), 3),
                "cycles_consistent": pc.cycles_consistent,
                "cycles_total": pc.cycles_total,
            }
        )
    out = pd.DataFrame(rows)
    out["bh_q"] = benjamini_hochberg(out["mann_whitney_p"].to_numpy())
    return out


def hormone_table(df_backbone: pd.DataFrame) -> pd.DataFrame:
    """Raw and date-partial Spearman of each contrast d-prime with PdG / E3G."""
    rows: list[dict[str, object]] = []
    for feature, feature_label, feature_role in _FEATURES:
        day = day_series(df_backbone, feature)
        drift = stats.spearmanr(day[feature], day["day_index"].astype(float)).statistic
        for hormone in ("pdg", "e3g"):
            sub = day.dropna(subset=[feature, hormone])
            n = len(sub)
            if n < 5:
                rows.append(
                    {
                        "feature": feature, "label": feature_label, "role": feature_role,
                        "hormone": hormone, "n": n, "raw_rho": float("nan"),
                        "date_partial_rho": float("nan"), "feature_drift": float(drift),
                    }
                )
                continue
            raw = stats.spearmanr(sub[feature], sub[hormone]).statistic
            partial, _ = partial_spearman(day, feature, hormone, "day_index")
            rows.append(
                {
                    "feature": feature, "label": feature_label, "role": feature_role,
                    "hormone": hormone, "n": n, "raw_rho": round(float(raw), 3),
                    "date_partial_rho": round(float(partial), 3), "feature_drift": round(float(drift), 3),
                }
            )
    return pd.DataFrame(rows)
