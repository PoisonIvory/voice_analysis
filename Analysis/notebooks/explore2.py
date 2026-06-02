"""Depth checks: confound control, replication, and acute premenstrual window.

Targets the candidate signals from explore.py:
- F0 (pitch) ~ estrogen (E3G)
- HNR (clarity) ~ estrogen & progesterone
and asks whether they survive a time-trend control and replicate in prosody.
"""

import numpy as np
import pandas as pd
from scipy import stats

from src.analysis.analysis_dataset import build_analysis_table

pd.set_option("display.width", 240)
pd.set_option("display.float_format", lambda v: f"{v:,.3f}")

F0 = "egemaps_F0semitoneFrom27.5Hz_sma3nz_amean"
HNR = "egemaps_HNRdBACF_sma3nz_amean"
JIT = "egemaps_jitterLocal_sma3nz_amean"
SHIM = "egemaps_shimmerLocaldB_sma3nz_amean"
ALPHA = "egemaps_alphaRatioV_sma3nz_amean"


def banner(t):
    print("\n" + "=" * 86 + f"\n{t}\n" + "=" * 86)


def partial_spearman(df, x, y, z):
    """First-order partial Spearman correlation of x,y controlling for z."""
    sub = df[[x, y, z]].dropna()
    if len(sub) < 6:
        return np.nan, len(sub)
    rxy = stats.spearmanr(sub[x], sub[y]).statistic
    rxz = stats.spearmanr(sub[x], sub[z]).statistic
    ryz = stats.spearmanr(sub[y], sub[z]).statistic
    denom = np.sqrt((1 - rxz**2) * (1 - ryz**2))
    if denom == 0:
        return np.nan, len(sub)
    return (rxy - rxz * ryz) / denom, len(sub)


df = build_analysis_table()
df["date_ord"] = df["date"].map(pd.Timestamp.toordinal)
hv = df[df["has_voice"] & df["has_hormones"]].copy()

banner("TIME-TREND CONFOUND CHECK (hormone window, vowel task)")
for name, base in [("F0", F0), ("HNR", HNR)]:
    col = f"vowel_{base}"
    for horm in ["e3g", "pdg"]:
        sub = hv[[col, horm, "date_ord"]].dropna()
        raw = stats.spearmanr(sub[col], sub[horm]).statistic
        feat_vs_time = stats.spearmanr(sub[col], sub["date_ord"]).statistic
        horm_vs_time = stats.spearmanr(sub[horm], sub["date_ord"]).statistic
        partial, n = partial_spearman(hv, col, horm, "date_ord")
        print(f"{name:4s} vs {horm.upper():4s} | n={n:2d} raw_rho={raw:+.3f} "
              f"feat~time={feat_vs_time:+.3f} horm~time={horm_vs_time:+.3f} "
              f"partial(rho|date)={partial:+.3f}")

banner("WITHIN-CYCLE replication of F0~E3G and HNR~hormones (per cycle)")
for cyc, g in hv.groupby("cycle_start_date"):
    n = g[["vowel_" + F0, "e3g"]].dropna().shape[0]
    if n < 5:
        print(f"  cycle {pd.to_datetime(cyc).date()}: n={n} (too few)")
        continue
    f0e = stats.spearmanr(g["vowel_" + F0], g["e3g"], nan_policy="omit").statistic
    hnre = stats.spearmanr(g["vowel_" + HNR], g["e3g"], nan_policy="omit").statistic
    hnrp = stats.spearmanr(g["vowel_" + HNR], g["pdg"], nan_policy="omit").statistic
    print(f"  cycle {pd.to_datetime(cyc).date()}: n={n}  F0~E3G={f0e:+.3f}  HNR~E3G={hnre:+.3f}  HNR~PdG={hnrp:+.3f}")

banner("PROSODY replication (does the coupling hold in connected speech?)")
for name, base in [("F0", F0), ("HNR", HNR)]:
    for horm in ["e3g", "pdg"]:
        col = f"prosody_{base}"
        sub = hv[[col, horm]].dropna()
        if len(sub) < 6:
            print(f"{name} vs {horm.upper()}: too few"); continue
        rho, p = stats.spearmanr(sub[col], sub[horm])
        print(f"prosody {name:4s} vs {horm.upper():4s} | n={len(sub):2d} rho={rho:+.3f} p={p:.3f}")

banner("ACUTE PREMENSTRUAL WINDOW (late luteal, days_to_next_start 1-5) vs follicular")
df["dtns"] = pd.to_numeric(df["days_to_next_start"], errors="coerce")
vp = df[df["has_voice"] & df["phase_label"].notna()].copy()
late_lut = vp[vp["dtns"].between(1, 5)]
foll = vp[vp["phase_label"] == "follicular"]
for name, base in [("F0", F0), ("HNR", HNR), ("Jitter", JIT), ("Shimmer", SHIM), ("Alpha ratio", ALPHA)]:
    col = f"vowel_{base}"
    a = late_lut[col].dropna()
    b = foll[col].dropna()
    if len(a) < 3 or len(b) < 3:
        print(f"{name}: too few (late_lut n={len(a)}, foll n={len(b)})"); continue
    u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
    print(f"{name:12s} | late-luteal n={len(a)} med={a.median():.3f} | follicular n={len(b)} med={b.median():.3f} | p={p:.3f}")

banner("PERI-OVULATORY F0 (does pitch peak near the estrogen/ovulation window?)")
# cycle_day buckets averaged across cycles for F0 (vowel)
vp2 = df[df["has_voice"] & df["cycle_day"].notna()].copy()
vp2["cd"] = pd.to_numeric(vp2["cycle_day"], errors="coerce")
vp2["cd_bucket"] = pd.cut(vp2["cd"], bins=[0, 7, 11, 16, 21, 60],
                          labels=["d1-7 early foll", "d8-11 late foll", "d12-16 periovul", "d17-21 early lut", "d22+ late lut"])
g = vp2.groupby("cd_bucket", observed=True)["vowel_" + F0].agg(["count", "median"])
print(g.to_string())
