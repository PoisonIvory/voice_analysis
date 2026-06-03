"""Run the HuBERT phonological-subspace cycle analysis; write tables + summary.

Single responsibility: orchestrate the analysis modules over the three backbones
and persist their result tables and a headline summary. Figures are built
separately in figures.py.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from ..phoneme.aggregation import BALANCED_CYCLES
from .bridge import triangulation
from .config import PRIMARY_BACKBONE, default_paths
from .cycle_tests import hormone_table, phase_table
from .load_dprime import load_dprime, primary
from .robustness import inter_backbone_rho, profile_cosine
from .taxonomy import COMPOSITE_CONSONANT, CONSONANT_CONTRASTS, USABLE_CONTRASTS, dprime_col


def coverage_summary(df: pd.DataFrame) -> dict:
    prim = primary(df)
    days = prim.drop_duplicates("date")[["date", "phase_label", "cycle_start_date"]]
    balance = (
        days.dropna(subset=["phase_label"])
        .groupby([days["cycle_start_date"].astype(str).str[:10], "phase_label"])
        .size()
        .unstack(fill_value=0)
    )
    # Per-contrast token counts (pos+neg) show the fixed passage keeps tokens
    # near-constant across recordings - the paper's token-count confound removed
    # at source rather than corrected after the fact.
    tokens = {}
    for key in USABLE_CONTRASTS:
        total = prim[f"n_{key}_pos"] + prim[f"n_{key}_neg"]
        tokens[key] = {"median": int(total.median()), "min": int(total.min()), "max": int(total.max())}
    return {
        "backbones": sorted(df["backbone"].unique()),
        "recordings": int(prim["recordingId"].nunique()),
        "days": int(prim["date"].nunique()),
        "date_min": str(prim["date"].min().date()),
        "date_max": str(prim["date"].max().date()),
        "hormone_overlap_days": int(prim.dropna(subset=["pdg"])["date"].nunique()),
        "balanced_cycles": list(BALANCED_CYCLES),
        "phase_balance_by_cycle_days": balance.to_dict(orient="index"),
        "tokens_per_contrast": tokens,
    }


def _headline(phase_primary: pd.DataFrame, rho: pd.DataFrame, cosine: pd.DataFrame) -> dict:
    comp = phase_primary[phase_primary["feature"] == COMPOSITE_CONSONANT].iloc[0]
    single = phase_primary[phase_primary["feature"] != COMPOSITE_CONSONANT]
    sig = single[single["bh_q"] < 0.05]
    return {
        "composite_cliffs_delta": float(comp["cliffs_delta"]),
        "composite_magnitude": str(comp["magnitude"]),
        "composite_bh_q": None if pd.isna(comp["bh_q"]) else round(float(comp["bh_q"]), 4),
        "n_usable_contrasts": int(len(single)),
        "n_contrasts_bh_sig": int(len(sig)),
        "contrasts_bh_sig": sig["feature"].tolist(),
        "inter_backbone_rho_min": round(float(rho["spearman_rho"].min()), 3),
        "inter_backbone_rho_max": round(float(rho["spearman_rho"].max()), 3),
        "profile_cosine_min": round(float(cosine["profile_cosine"].min()), 4),
    }


def main() -> None:
    paths = default_paths()
    paths.tables_dir.mkdir(parents=True, exist_ok=True)

    df = load_dprime(paths)

    cov = coverage_summary(df)

    phase_all = pd.concat(
        [phase_table(df[df["backbone"] == b]).assign(backbone=b) for b in cov["backbones"]],
        ignore_index=True,
    )
    phase_primary = phase_all[phase_all["backbone"] == PRIMARY_BACKBONE].reset_index(drop=True)
    hormones = hormone_table(primary(df))
    rho = inter_backbone_rho(df)
    cosine = profile_cosine(df)
    tri = triangulation(df)

    phase_all.to_csv(paths.tables_dir / "phase_contrasts.csv", index=False)
    hormones.to_csv(paths.tables_dir / "hormone_coupling.csv", index=False)
    rho.to_csv(paths.tables_dir / "inter_backbone_rho.csv", index=False)
    cosine.to_csv(paths.tables_dir / "profile_cosine.csv", index=False)
    tri.to_csv(paths.tables_dir / "triangulation.csv", index=False)

    summary = {"coverage": cov, "headline": _headline(phase_primary, rho, cosine)}
    (paths.tables_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    print("=== coverage ===")
    print(json.dumps(cov, indent=2))
    print("\n=== phase contrasts (HuBERT-base) ===")
    print(phase_primary.drop(columns=["backbone"]).to_string(index=False))
    print("\n=== hormone coupling (HuBERT-base) ===")
    print(hormones.to_string(index=False))
    print("\n=== inter-backbone agreement (composite) ===\n", rho.to_string(index=False))
    print("\n=== consonant profile cosine ===\n", cosine.to_string(index=False))
    print("\n=== triangulation vs eGeMAPS phoneme study ===\n", tri.to_string(index=False))
    print("\n=== headline ===")
    print(json.dumps(_headline(phase_primary, rho, cosine), indent=2))


if __name__ == "__main__":
    main()
