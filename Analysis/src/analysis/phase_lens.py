"""Within-cycle phase lens: a second, hormone-free look at the voice by phase.

The first study (`study_results`) treated the coarse follicular-vs-luteal split as
a blunt instrument and pivoted to continuous hormone coupling with date-based drift
control on the 29 voice+hormone days. This module takes the opposite stance and
rehabilitates the phase comparison by fixing the two reasons it was abandoned:

1. Slow cross-cycle drift is removed *by design* via **within-cycle normalization**
   (each feature is z-scored inside its own cycle, so every cycle is its own
   baseline). No hormone series and no partial-correlation are needed, so the lens
   uses *all* voice+phase days, not only the hormone-overlap days.
2. Single-feature bluntness is replaced by a **multivariate** question: does the
   voice profile as a whole separate the phases, and does that separation generalise
   to a held-out cycle (leave-one-cycle-out classification)?

All functions are pure and operate on the unified daily analysis table.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import feature_taxonomy as tax

TASKS: tuple[str, ...] = ("vowel", "prosody")
MIN_PER_PHASE: int = 2  # a cycle needs >=2 days in each phase to contribute a contrast


def voice_phase_days(df: pd.DataFrame) -> pd.DataFrame:
    """Rows with voice and a follicular/luteal label (the lens operates on these)."""
    return df[df["has_voice"] & df["phase_label"].notna()].copy()


def within_cycle_zscore(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Z-score each column inside each cycle (mean 0, sd 1 per cycle).

    Centering per cycle removes any slow between-cycle drift without touching the
    within-cycle phase structure. Columns whose cycle has zero variance (or a single
    day) become NaN for that cycle and are dropped by downstream consumers.
    """
    z = df[cols].astype(float).copy()
    for _, idx in df.groupby("cycle_start_date").groups.items():
        block = z.loc[idx]
        sd = block.std(ddof=0).replace(0, np.nan)
        z.loc[idx] = (block - block.mean()) / sd
    return z


def _resolve_cols(df: pd.DataFrame, bases: list[str]) -> list[str]:
    cols = [tax.with_task(b, t) for b in bases for t in TASKS]
    return [c for c in cols if c in df.columns]


def usable_cycles(vp: pd.DataFrame) -> list[pd.Timestamp]:
    """Cycles with at least MIN_PER_PHASE voice days in *both* phases."""
    counts = vp.groupby(["cycle_start_date", "phase_label"]).size().unstack(fill_value=0)
    mask = (counts.get("follicular", 0) >= MIN_PER_PHASE) & (counts.get("luteal", 0) >= MIN_PER_PHASE)
    return list(counts[mask].index)


def phase_shift_table(df: pd.DataFrame) -> pd.DataFrame:
    """Per-feature within-cycle luteal-minus-follicular shift, in within-cycle SD units.

    For every feature the shift is computed *inside each usable cycle* (so it is drift
    free) and then pooled. `cycles_concordant` counts how many cycles share the sign of
    the pooled shift -- the cross-cycle reproducibility that single-snapshot studies
    cannot see.
    """
    vp = voice_phase_days(df)
    cycles = usable_cycles(vp)
    rows = []
    for base in tax.base_features():
        for task in TASKS:
            col = tax.with_task(base, task)
            if col not in vp.columns:
                continue
            z = within_cycle_zscore(vp, [col])[col]
            sub = pd.DataFrame({"z": z, "phase": vp["phase_label"], "cyc": vp["cycle_start_date"]}).dropna()
            shifts = []
            for cyc in cycles:
                g = sub[sub["cyc"] == cyc]
                gf = g.loc[g["phase"] == "follicular", "z"]
                gl = g.loc[g["phase"] == "luteal", "z"]
                if len(gf) >= MIN_PER_PHASE and len(gl) >= MIN_PER_PHASE:
                    shifts.append(gl.mean() - gf.mean())
            if len(shifts) < 2:
                continue
            shifts = np.array(shifts, dtype=float)
            pooled = float(shifts.mean())
            concordant = int(np.sum(np.sign(shifts) == np.sign(pooled)))
            rows.append(
                dict(family=tax.family_of(base), family_label=tax.FAMILY_LABELS[tax.family_of(base)],
                     feature=tax.label_of(base), base=base, task=task,
                     pooled_shift_z=pooled, abs_shift_z=abs(pooled),
                     cycles_concordant=concordant, cycles_total=len(shifts))
            )
    return pd.DataFrame(rows).sort_values("abs_shift_z", ascending=False).reset_index(drop=True)


def family_shift_summary(shift_table: pd.DataFrame) -> pd.DataFrame:
    """Mean absolute within-cycle phase shift per mechanism family (magnitude, not sign).

    A magnitude summary is non-circular: it asks "how much does each family move with
    phase", which is exactly the geometry-vs-surface question, recovered without hormones.
    """
    out = (shift_table.groupby("family_label")["abs_shift_z"]
           .agg(n_features="size", mean_abs="mean", median_abs="median", max_abs="max")
           .reset_index().sort_values("mean_abs", ascending=False))
    return out.reset_index(drop=True)


def week_trajectory(df: pd.DataFrame, bases: list[str], task: str) -> pd.DataFrame:
    """Within-cycle z of each feature averaged per cycle_week, pooled across all cycles.

    cycle_week is the documented second analysis lens; tracing the normalised feature
    week by week shows the voice as a *trajectory across the cycle* rather than a binary
    contrast. Pooling uses every cycle (including the ones with only one phase sampled).
    """
    vp = voice_phase_days(df)
    cols = [tax.with_task(b, task) for b in bases if tax.with_task(b, task) in vp.columns]
    z = within_cycle_zscore(vp, cols)
    long = z.join(vp[["cycle_week"]]).melt(id_vars="cycle_week", var_name="col", value_name="z").dropna()
    long["base"] = long["col"].str.replace(f"{task}_", "", regex=False)
    long["feature"] = long["base"].map(tax.label_of)
    long["task"] = task
    agg = (long.groupby(["feature", "base", "task", "cycle_week"])["z"]
           .agg(mean="mean", sem=lambda s: s.std(ddof=1) / np.sqrt(len(s)) if len(s) > 1 else np.nan,
                n="size").reset_index())
    return agg


@dataclass(frozen=True)
class Separability:
    feature_set: str
    n_features: int
    n_days: int
    cycles: list[str]
    balanced_accuracy: float
    null_mean: float
    null_p95: float
    p_value: float
    fold_recalls: dict[str, float]


def _loco_balanced_accuracy(frame: pd.DataFrame, cols: list[str]) -> tuple[float, dict[str, float]]:
    """Leave-one-cycle-out nearest-centroid balanced accuracy for follicular vs luteal."""
    correct = {"follicular": 0, "luteal": 0}
    total = {"follicular": 0, "luteal": 0}
    for test_c in frame["cycle_start_date"].unique():
        train = frame[frame["cycle_start_date"] != test_c]
        test = frame[frame["cycle_start_date"] == test_c]
        cent = train.groupby("phase_label")[cols].mean()
        if not {"follicular", "luteal"}.issubset(set(cent.index)):
            continue
        cf = cent.loc["follicular"].to_numpy(float)
        cl = cent.loc["luteal"].to_numpy(float)
        for _, row in test.iterrows():
            x = row[cols].to_numpy(float)
            pred = "luteal" if np.linalg.norm(x - cl) < np.linalg.norm(x - cf) else "follicular"
            total[row["phase_label"]] += 1
            correct[row["phase_label"]] += int(pred == row["phase_label"])
    recalls = {k: (correct[k] / total[k]) for k in ("follicular", "luteal") if total[k]}
    bal = float(np.mean(list(recalls.values()))) if recalls else np.nan
    return bal, recalls


def loco_separability(
    df: pd.DataFrame, bases: list[str], feature_set: str, n_perm: int = 2000, seed: int = 7
) -> Separability:
    """Can the within-cycle voice profile predict the phase of a held-out cycle?

    The null shuffles phase labels *within each cycle* (preserving the design) and
    re-runs the same leave-one-cycle-out classifier, giving an honest small-sample
    p-value for an N-of-1 design.
    """
    vp = voice_phase_days(df)
    # Restrict to phase-balanced cycles *before* z-scoring: within-cycle normalization
    # is undefined for single-day cycles (sd = 0 -> NaN) and a mostly-one-phase cycle's
    # mean is not a phase-neutral baseline, so such cycles cannot carry this method.
    vp = vp[vp["cycle_start_date"].isin(usable_cycles(vp))].copy()
    cols = _resolve_cols(vp, bases)
    z = within_cycle_zscore(vp, cols).dropna(axis=1, how="any")
    cols = z.columns.tolist()
    frame = vp[["cycle_start_date", "phase_label"]].join(z).dropna(subset=cols)

    obs, recalls = _loco_balanced_accuracy(frame, cols)
    rng = np.random.default_rng(seed)
    null = []
    for _ in range(n_perm):
        perm = frame.copy()
        perm["phase_label"] = perm.groupby("cycle_start_date")["phase_label"].transform(
            lambda s: rng.permutation(s.to_numpy()))
        b, _ = _loco_balanced_accuracy(perm, cols)
        if not np.isnan(b):
            null.append(b)
    null = np.array(null)
    p = float((np.sum(null >= obs) + 1) / (len(null) + 1))
    return Separability(
        feature_set=feature_set, n_features=len(cols), n_days=len(frame),
        cycles=[str(pd.Timestamp(c).date()) for c in frame["cycle_start_date"].unique()],
        balanced_accuracy=obs, null_mean=float(null.mean()), null_p95=float(np.percentile(null, 95)),
        p_value=p, fold_recalls=recalls,
    )


def separability_table(df: pd.DataFrame, n_perm: int = 2000) -> tuple[pd.DataFrame, dict]:
    """Run the multivariate phase classifier for the signal set and the geometry control."""
    surface_timbre = list(tax.SURFACE_DAMPING) + list(tax.SPECTRAL_ENVELOPE_MFCC)
    sets = {
        "Surface + timbre (mechanism signal)": surface_timbre,
        "Geometry only (negative control)": list(tax.GEOMETRIC_VOCAL_TRACT),
    }
    results = {name: loco_separability(df, bases, name, n_perm=n_perm) for name, bases in sets.items()}
    rows = [dict(feature_set=r.feature_set, n_features=r.n_features, n_days=r.n_days,
                 balanced_accuracy=r.balanced_accuracy, null_mean=r.null_mean,
                 null_p95=r.null_p95, p_value=r.p_value) for r in results.values()]
    return pd.DataFrame(rows), results
