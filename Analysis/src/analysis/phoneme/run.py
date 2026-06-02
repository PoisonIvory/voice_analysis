"""Run the full phoneme-prosody analysis and write tables to outputs/phoneme/tables.

Single responsibility: orchestrate the analysis modules and persist their result
tables + a coverage summary. Figures are built separately in figures.py.
"""

from __future__ import annotations

import json

import pandas as pd

from .aggregation import BALANCED_CYCLES
from .bridge import bridge_validation, global_coupling
from .config import default_paths
from .contrasts import contrast_table, dispersion_table
from .load_phonemes import analyzable_segments, clean_recordings, load_phonemes
from .localization import localize
from .multivariate import classify
from .residual_segments import diphthong_residual_table


def coverage_summary(raw: pd.DataFrame, clean: pd.DataFrame, analyzable: pd.DataFrame) -> dict:
    # one row per (date, phase, cycle): day grain is the unit for phase tests
    days = clean.drop_duplicates("date")[["date", "phase_label", "cycle_start_date"]]
    balance = (
        days.dropna(subset=["phase_label"])
        .groupby([days["cycle_start_date"].astype(str).str[:10], "phase_label"])
        .size()
        .unstack(fill_value=0)
    )
    pdg_days = clean.dropna(subset=["pdg"])["date"].nunique()
    return {
        "phonemes_total": int(len(raw)),
        "phonemes_clean": int(len(clean)),
        "phonemes_analyzable": int(len(analyzable)),
        "recordings_total": int(raw["recordingId"].nunique()),
        "recordings_clean": int(clean["recordingId"].nunique()),
        "days_clean": int(clean["date"].nunique()),
        "date_min": str(clean["date"].min().date()),
        "date_max": str(clean["date"].max().date()),
        "follicular_days": int((days["phase_label"] == "follicular").sum()),
        "luteal_days": int((days["phase_label"] == "luteal").sum()),
        "hormone_overlap_days": int(pdg_days),
        "balanced_cycles": list(BALANCED_CYCLES),
        "phase_balance_by_cycle_days": balance.to_dict(orient="index"),
    }


def main() -> None:
    paths = default_paths()
    paths.tables_dir.mkdir(parents=True, exist_ok=True)

    raw = load_phonemes(paths)
    clean = clean_recordings(raw)
    analyzable = analyzable_segments(raw)

    cov = coverage_summary(raw, clean, analyzable)

    bridge = bridge_validation(analyzable, paths)
    gcoup = global_coupling(analyzable)
    loc = localize(analyzable)
    diph_resid, f0_r2 = diphthong_residual_table(analyzable)
    contrasts = contrast_table(analyzable)
    dispersion = dispersion_table(analyzable)
    mv = classify(analyzable)

    bridge.to_csv(paths.tables_dir / "bridge_validation.csv", index=False)
    gcoup.to_csv(paths.tables_dir / "global_coupling.csv", index=False)
    loc.to_csv(paths.tables_dir / "localization.csv", index=False)
    diph_resid.to_csv(paths.tables_dir / "diphthong_f0_residual.csv", index=False)
    contrasts.to_csv(paths.tables_dir / "within_recording_contrasts.csv", index=False)
    dispersion.to_csv(paths.tables_dir / "dispersion.csv", index=False)
    mv.to_csv(paths.tables_dir / "multivariate_classifier.csv", index=False)

    summary = {"coverage": cov, "f0_residual_r2": round(f0_r2, 4)}
    (paths.tables_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    print("=== coverage ===")
    print(json.dumps(cov, indent=2))
    print("\n=== bridge validation ===\n", bridge.to_string(index=False))
    print("\n=== global coupling ===\n", gcoup.to_string(index=False))
    print("\n=== localization (key rows) ===")
    print(loc[loc.feature == "segment_h1h2_mean"].to_string(index=False))
    print(f"\n=== diphthong F0-residual (F0 explains {f0_r2*100:.1f}% of segment H1-H2) ===\n",
          diph_resid.to_string(index=False))
    print("\n=== within-recording contrasts ===\n",
          contrasts.drop(columns=["rationale"]).to_string(index=False))
    print("\n=== dispersion ===\n", dispersion.to_string(index=False))
    print("\n=== multivariate ===\n", mv.to_string(index=False))


if __name__ == "__main__":
    main()
