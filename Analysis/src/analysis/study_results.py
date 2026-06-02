"""Computes all result tables for the voice-cycle study and saves them as CSV.

Pure computation: no plotting. Tables are the single source of truth that both
the figures and the written report consume.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .analysis_dataset import build_analysis_table
from . import feature_taxonomy as tax
from . import stats as st

OURA_CONTROLS: dict[str, str] = {
    "temp_deviation": "Body temperature deviation",
    "hrv": "Heart-rate variability (HRV)",
    "average_hr": "Daytime average heart rate",
    "resting_hr": "Resting heart rate",
    "breath_rate": "Respiration rate",
    "sleep_score": "Sleep score",
}


def _positive_controls(labeled: pd.DataFrame) -> pd.DataFrame:
    rows = []
    sub = labeled[labeled["has_oura"]]
    for col, label in OURA_CONTROLS.items():
        if col not in sub:
            continue
        pc = st.phase_contrast(sub, col)
        rows.append(
            dict(variable=label, n_follicular=pc.n_follicular, n_luteal=pc.n_luteal,
                 median_follicular=pc.median_follicular, median_luteal=pc.median_luteal,
                 luteal_minus_follicular=pc.delta_luteal_minus_follicular,
                 cliffs_delta=pc.cliffs_delta, magnitude=pc.magnitude,
                 mann_whitney_p=pc.mann_whitney_p,
                 cycles_consistent=pc.cycles_consistent, cycles_total=pc.cycles_total)
        )
    return pd.DataFrame(rows)


def _voice_phase_contrast(voice_phase: pd.DataFrame, task: str) -> pd.DataFrame:
    rows = []
    for base in tax.base_features():
        col = tax.with_task(base, task)
        if col not in voice_phase:
            continue
        pc = st.phase_contrast(voice_phase, col)
        rows.append(
            dict(family=tax.family_of(base), feature=tax.label_of(base), base=base,
                 n_follicular=pc.n_follicular, n_luteal=pc.n_luteal,
                 cliffs_delta=pc.cliffs_delta, magnitude=pc.magnitude,
                 luteal_minus_follicular=pc.delta_luteal_minus_follicular,
                 mann_whitney_p=pc.mann_whitney_p,
                 cycles_consistent=pc.cycles_consistent, cycles_total=pc.cycles_total)
        )
    out = pd.DataFrame(rows)
    out["fdr_q"] = st.benjamini_hochberg(out["mann_whitney_p"].to_numpy())
    out["family_label"] = out["family"].map(tax.FAMILY_LABELS)
    return out


def _hormone_coupling(hv: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for base in tax.base_features():
        for task in ["vowel", "prosody"]:
            col = tax.with_task(base, task)
            if col not in hv:
                continue
            for horm, horm_label in [("e3g", "Estrogen (E3G)"), ("pdg", "Progesterone (PdG)")]:
                hc = st.hormone_coupling(hv, col, horm, n_boot=1000)
                partial, _ = st.partial_spearman(hv, col, horm, "date_ord")
                rows.append(
                    dict(family=tax.family_of(base), feature=tax.label_of(base), base=base,
                         task=task, hormone=horm_label, n=hc.n,
                         raw_rho=hc.spearman_rho, raw_p=hc.spearman_p,
                         boot_lo=hc.boot_lo, boot_hi=hc.boot_hi,
                         partial_rho_date=partial)
                )
    out = pd.DataFrame(rows)
    out["family_label"] = out["family"].map(tax.FAMILY_LABELS)
    return out


def _family_meta(voice_phase_vowel: pd.DataFrame) -> pd.DataFrame:
    out = voice_phase_vowel.copy()
    out["abs_cliff"] = out["cliffs_delta"].abs()
    return out.groupby("family_label")["abs_cliff"].agg(["count", "mean", "median", "max"]).reset_index()


def compute_all(outputs_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    df = build_analysis_table()
    df["date_ord"] = df["date"].map(lambda d: d.toordinal() if pd.notna(d) else np.nan)

    labeled = df[df["phase_label"].notna()].copy()
    voice_phase = labeled[labeled["has_voice"]].copy()
    hv = df[df["has_voice"] & df["has_hormones"]].copy()

    results = {
        "analysis_table": df,
        "positive_controls": _positive_controls(labeled),
        "voice_phase_vowel": _voice_phase_contrast(voice_phase, "vowel"),
        "voice_phase_prosody": _voice_phase_contrast(voice_phase, "prosody"),
        "hormone_coupling": _hormone_coupling(hv),
    }
    results["family_meta"] = _family_meta(results["voice_phase_vowel"])

    if outputs_dir is not None:
        outputs_dir.mkdir(parents=True, exist_ok=True)
        for name, table in results.items():
            if name == "analysis_table":
                continue
            table.to_csv(outputs_dir / f"{name}.csv", index=False)
    return results


if __name__ == "__main__":
    from .config import default_paths

    res = compute_all(default_paths().outputs_dir / "tables")
    for k, v in res.items():
        if k == "analysis_table":
            continue
        print(f"\n=== {k} ===")
        print(v.to_string(index=False))
