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

# Candidate signals surfaced by the (hypothesis-led) in-window analysis. These
# are the features the robustness checks try to break.
CANDIDATES: list[tuple[str, str, str]] = [
    ("HNR (vowel)", "vowel", "egemaps_HNRdBACF_sma3nz_amean"),
    ("HNR (prosody)", "prosody", "egemaps_HNRdBACF_sma3nz_amean"),
    ("MFCC1 (vowel)", "vowel", "egemaps_mfcc1V_sma3nz_amean"),
    ("Hammarberg (prosody)", "prosody", "egemaps_hammarbergIndexV_sma3nz_amean"),
    ("F2 bandwidth (prosody)", "prosody", "egemaps_F2bandwidth_sma3nz_amean"),
    ("MFCC2 (prosody)", "prosody", "egemaps_mfcc2V_sma3nz_amean"),
    ("MFCC3 (vowel)", "vowel", "egemaps_mfcc3V_sma3nz_amean"),
]


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


def _estimate_progesterone(df: pd.DataFrame) -> pd.Series:
    """Estimate progesterone from cycle position (days-to-next-period) using a
    template learned only from the hormone window. Lets us project an expected
    PdG onto days that were never measured."""
    dtns = pd.to_numeric(df["days_to_next_start"], errors="coerce")
    hw = df[df["has_hormones"]].copy()
    hw["dtns"] = pd.to_numeric(hw["days_to_next_start"], errors="coerce")
    bins = [-1, 2, 5, 9, 14, 100]
    labels = ["1-2", "3-5", "6-9", "10-14", "15+"]
    hw["bin"] = pd.cut(hw["dtns"], bins=bins, labels=labels)
    template = hw.groupby("bin", observed=True)["pdg"].median()
    binned = pd.cut(dtns, bins=bins, labels=labels)
    return binned.map(template).astype(float)


def _robustness(df: pd.DataFrame) -> pd.DataFrame:
    """Try to break the candidate signals: out-of-sample replication on held-out
    days using a temperature progesterone-proxy, plus a template estimate."""
    voice = df[df["has_voice"]].copy()
    in_win = voice[voice["has_hormones"]]
    out_win = voice[(voice["phase_label"].notna()) & (voice["temp_deviation"].notna()) & (~voice["has_hormones"])]

    def _rho(frame, x, y):
        s = frame[[x, y]].dropna()
        if len(s) < 5:
            return np.nan, len(s)
        from scipy import stats
        return float(stats.spearmanr(s[x], s[y]).statistic), len(s)

    rows = []
    for name, task, base in CANDIDATES:
        col = tax.with_task(base, task)
        if col not in df:
            continue
        in_rho, in_n = _rho(in_win, col, "pdg")
        out_temp, out_n = _rho(out_win, col, "temp_deviation")
        out_temp_dc, _ = st.partial_spearman(out_win, col, "temp_deviation", "date_ord")
        out_est, _ = _rho(out_win, col, "est_pdg")
        rows.append(dict(
            feature=name, in_window_n=in_n, in_window_rho_pdg=in_rho,
            heldout_n=out_n, heldout_rho_temp=out_temp,
            heldout_rho_temp_datectrl=out_temp_dc, heldout_rho_est_pdg=out_est,
            direction_agrees=bool(np.sign(in_rho) == np.sign(out_temp)) if not (np.isnan(in_rho) or np.isnan(out_temp)) else False,
        ))
    return pd.DataFrame(rows)


def _agnostic_temp_scan(df: pd.DataFrame) -> pd.DataFrame:
    """Hypothesis-free scan: every voice feature vs the temperature proxy."""
    from scipy import stats
    voice = df[df["has_voice"] & df["temp_deviation"].notna()].copy()
    base_all = sorted({c.split("_", 1)[1] for c in df.columns for t in ("vowel", "prosody")
                       if c.startswith(t + "_egemaps_")})
    rows = []
    for base in base_all:
        for task in ["vowel", "prosody"]:
            col = f"{task}_{base}"
            if col not in voice:
                continue
            s = voice[[col, "temp_deviation"]].dropna()
            if len(s) < 8:
                continue
            r, p = stats.spearmanr(s[col], s["temp_deviation"])
            rp, _ = st.partial_spearman(voice, col, "temp_deviation", "date_ord")
            rows.append(dict(base=base, task=task, family=tax.family_of(base) or "other",
                             n=len(s), rho=float(r), p=float(p), partial_rho_date=rp))
    out = pd.DataFrame(rows)
    out["fdr_q"] = st.benjamini_hochberg(out["p"].to_numpy())
    return out.sort_values("p").reset_index(drop=True)


def _family_meta(voice_phase_vowel: pd.DataFrame) -> pd.DataFrame:
    out = voice_phase_vowel.copy()
    out["abs_cliff"] = out["cliffs_delta"].abs()
    return out.groupby("family_label")["abs_cliff"].agg(["count", "mean", "median", "max"]).reset_index()


def compute_all(outputs_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    df = build_analysis_table()
    df["date_ord"] = df["date"].map(lambda d: d.toordinal() if pd.notna(d) else np.nan)
    df["est_pdg"] = _estimate_progesterone(df)

    labeled = df[df["phase_label"].notna()].copy()
    voice_phase = labeled[labeled["has_voice"]].copy()
    hv = df[df["has_voice"] & df["has_hormones"]].copy()

    coupling = _hormone_coupling(hv)
    coupling["fdr_q"] = st.benjamini_hochberg(coupling["raw_p"].to_numpy())

    results = {
        "analysis_table": df,
        "positive_controls": _positive_controls(labeled),
        "voice_phase_vowel": _voice_phase_contrast(voice_phase, "vowel"),
        "voice_phase_prosody": _voice_phase_contrast(voice_phase, "prosody"),
        "hormone_coupling": coupling,
        "robustness": _robustness(df),
        "agnostic_temp_scan": _agnostic_temp_scan(df),
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
