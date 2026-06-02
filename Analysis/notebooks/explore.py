"""Exploratory analysis: do voice features track the cycle, and which ones?

Prints structured diagnostics so we can decide whether patterns are real before
writing the report. Uses vowel-task features for voice-quality measures.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.analysis_dataset import build_analysis_table
from src.analysis import feature_taxonomy as tax
from src.analysis import stats as st

pd.set_option("display.max_columns", 50)
pd.set_option("display.width", 240)
pd.set_option("display.float_format", lambda v: f"{v:,.3f}")

ROOT = Path("/Users/ivyhamilton/Decibelle/Analysis")
TASK = "vowel"  # gold standard for voice-quality / surface measures


def banner(t):
    print("\n" + "#" * 90 + f"\n# {t}\n" + "#" * 90)


df = build_analysis_table()
# Save the unified table for reproducibility.
out_path = ROOT / "data/processed/analysis_daily.parquet"
df.to_parquet(out_path, index=False)
print("Saved unified table:", out_path, df.shape)

labeled = df[df["phase_label"].notna()].copy()
voice_phase = labeled[labeled["has_voice"]].copy()

banner("COVERAGE")
print("voice+phase days:", len(voice_phase))
print(voice_phase["phase_label"].value_counts())
print("by cycle:")
print(voice_phase.groupby("cycle_start_date")["phase_label"].value_counts().unstack(fill_value=0))

# ---------------------------------------------------------------------------
banner("POSITIVE CONTROLS (Oura) — does the body show the cycle?")
controls = ["temp_deviation", "resting_hr", "hrv", "average_hr", "breath_rate", "sleep_score"]
rows = []
for c in controls:
    if c not in labeled:
        continue
    pc = st.phase_contrast(labeled[labeled["has_oura"]], c)
    rows.append(
        dict(var=c, n_f=pc.n_follicular, n_l=pc.n_luteal, med_f=pc.median_follicular,
             med_l=pc.median_luteal, delta=pc.delta_luteal_minus_follicular,
             cliff=pc.cliffs_delta, mag=pc.magnitude, p=pc.mann_whitney_p,
             cyc=f"{pc.cycles_consistent}/{pc.cycles_total}")
    )
print(pd.DataFrame(rows).to_string(index=False))

# ---------------------------------------------------------------------------
banner("HORMONE WINDOW — ovulation anchoring")
hw = df[df["has_hormones"]].copy().sort_values("date")
print("hormone days:", len(hw), hw["date"].min().date(), "->", hw["date"].max().date())
for _, g in hw.groupby("cycle_start_date"):
    if g["lh"].notna().any():
        peak = g.loc[g["lh"].idxmax()]
        print(f"  cycle {pd.to_datetime(g['cycle_start_date'].iloc[0]).date()}: "
              f"LH peak {peak['lh']:.1f} on cycle_day {peak['cycle_day']} ({peak['date'].date()}), "
              f"max PdG {g['pdg'].max():.1f}, max E3G {g['e3g'].max():.1f}")

# ---------------------------------------------------------------------------
banner(f"VOICE PHASE CONTRAST by family (task={TASK}) — luteal vs follicular")
results = []
for base in tax.base_features():
    col = tax.with_task(base, TASK)
    if col not in voice_phase:
        continue
    pc = st.phase_contrast(voice_phase, col)
    results.append(
        dict(family=tax.family_of(base), feature=tax.label_of(base), col=base,
             n_f=pc.n_follicular, n_l=pc.n_luteal,
             cliff=pc.cliffs_delta, mag=pc.magnitude, delta=pc.delta_luteal_minus_follicular,
             p=pc.mann_whitney_p, cyc=f"{pc.cycles_consistent}/{pc.cycles_total}")
    )
res = pd.DataFrame(results)
res["q"] = st.benjamini_hochberg(res["p"].to_numpy())
res["abs_cliff"] = res["cliff"].abs()
for fam in ["geometric_vocal_tract", "source_pitch", "surface_damping"]:
    block = res[res["family"] == fam].sort_values("abs_cliff", ascending=False)
    print(f"\n--- {tax.FAMILY_LABELS[fam]} ---")
    print(block[["feature", "n_f", "n_l", "cliff", "mag", "delta", "p", "q", "cyc"]].to_string(index=False))

banner("GEOMETRIC vs SURFACE meta-contrast: |effect size| by family")
fam_summary = res.groupby("family")["abs_cliff"].agg(["mean", "median", "max", "count"])
print(fam_summary.to_string())
geo = res.loc[res["family"] == "geometric_vocal_tract", "abs_cliff"].dropna()
sur = res.loc[res["family"] == "surface_damping", "abs_cliff"].dropna()
if len(geo) and len(sur):
    from scipy import stats as sstats
    u, p = sstats.mannwhitneyu(sur, geo, alternative="greater")
    print(f"Surface |delta| > Geometric |delta|? Mann-Whitney p = {p:.3f} "
          f"(surface median={sur.median():.3f}, geometric median={geo.median():.3f})")

# ---------------------------------------------------------------------------
banner(f"HORMONE COUPLING (task={TASK}) — voice vs PdG (progesterone) & E3G (estrogen)")
hv = df[df["has_voice"] & df["has_hormones"]].copy()
print("voice+hormone days:", len(hv))
coup = []
for base in tax.base_features():
    col = tax.with_task(base, TASK)
    if col not in hv:
        continue
    for horm in ["pdg", "e3g"]:
        hc = st.hormone_coupling(hv, col, horm)
        coup.append(dict(family=tax.family_of(base), feature=tax.label_of(base),
                         hormone=horm, n=hc.n, rho=hc.spearman_rho, p=hc.spearman_p,
                         ci=f"[{hc.boot_lo:.2f},{hc.boot_hi:.2f}]"))
cp = pd.DataFrame(coup)
for horm in ["pdg", "e3g"]:
    block = cp[cp["hormone"] == horm].copy()
    block["abs_rho"] = block["rho"].abs()
    block = block.sort_values("abs_rho", ascending=False)
    print(f"\n--- vs {horm.upper()} (top couplings) ---")
    print(block[["family", "feature", "n", "rho", "p", "ci"]].head(12).to_string(index=False))
