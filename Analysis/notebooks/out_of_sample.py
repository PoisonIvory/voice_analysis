"""Out-of-sample validation + hypothesis-free scan.

Two questions:
1. Do the in-window findings (esp. HNR ~ progesterone) reappear on voice days
   that had NO hormone measurement, using only a progesterone PROXY?
   Proxies: Oura body-temperature deviation (measured, thermogenic effect of
   progesterone) and a cycle-position PdG template estimated from the hormone
   window.
2. Hypothesis-free: scan EVERY voice feature against the temperature proxy with
   no taxonomy and FDR correction. Does the surface/quality cluster still win?
"""

import numpy as np
import pandas as pd
from scipy import stats

from src.analysis.analysis_dataset import build_analysis_table
from src.analysis import feature_taxonomy as tax
from src.analysis import stats as st

pd.set_option("display.width", 240)
pd.set_option("display.max_rows", 120)
pd.set_option("display.float_format", lambda v: f"{v:,.3f}")


def banner(t):
    print("\n" + "=" * 92 + f"\n{t}\n" + "=" * 92)


df = build_analysis_table()
df["date_ord"] = df["date"].map(lambda d: d.toordinal() if pd.notna(d) else np.nan)
df["dtns"] = pd.to_numeric(df["days_to_next_start"], errors="coerce")

# --- Build a cycle-position progesterone template from the hormone window ---
# Progesterone is keyed to days-before-next-period (luteal length is stable).
hw = df[df["has_hormones"]].copy()
hw["dtns_bin"] = pd.cut(hw["dtns"], bins=[-1, 2, 5, 9, 14, 100],
                        labels=["1-2", "3-5", "6-9", "10-14", "15+"])
template = hw.groupby("dtns_bin", observed=True)["pdg"].median()
banner("PROGESTERONE TEMPLATE (median PdG by days-to-next-period, from hormone window)")
print(template.to_string())

bin_map = {"1-2": (-1, 2), "3-5": (2, 5), "6-9": (5, 9), "10-14": (9, 14), "15+": (14, 100)}
def est_pdg(dtns):
    if pd.isna(dtns):
        return np.nan
    for label, (lo, hi) in bin_map.items():
        if lo < dtns <= hi:
            return template.get(label, np.nan)
    return np.nan
df["est_pdg"] = df["dtns"].map(est_pdg)

# --- Cohorts ---
voice = df[df["has_voice"]].copy()
in_win = voice[voice["has_hormones"]].copy()
out_win = voice[(voice["phase_label"].notna()) & (voice["temp_deviation"].notna()) & (~voice["has_hormones"])].copy()
banner("COHORTS")
print(f"In-window (had hormones):   n={len(in_win)}")
print(f"Held-out (no hormones):     n={len(out_win)}")
print("Held-out by cycle:\n", out_win.groupby("cycle_start_date")["phase_label"].value_counts().unstack(fill_value=0))

ROBUST = [
    ("HNR (vowel)", "vowel_egemaps_HNRdBACF_sma3nz_amean"),
    ("HNR (prosody)", "prosody_egemaps_HNRdBACF_sma3nz_amean"),
    ("MFCC1 (vowel)", "vowel_egemaps_mfcc1V_sma3nz_amean"),
    ("Hammarberg (prosody)", "prosody_egemaps_hammarbergIndexV_sma3nz_amean"),
    ("F2 bandwidth (prosody)", "prosody_egemaps_F2bandwidth_sma3nz_amean"),
    ("MFCC2 (prosody)", "prosody_egemaps_mfcc2V_sma3nz_amean"),
    ("MFCC3 (vowel)", "vowel_egemaps_mfcc3V_sma3nz_amean"),
]


def rho(a, b):
    s = pd.DataFrame({"a": a, "b": b}).dropna()
    if len(s) < 5:
        return np.nan, len(s)
    return stats.spearmanr(s["a"], s["b"]).statistic, len(s)


banner("OUT-OF-SAMPLE: do the robust features track progesterone PROXIES on held-out days?")
print(f"{'feature':24s} | in-win vs PdG | OUT vs temp | OUT vs temp (date-ctrl) | OUT vs est_PdG | OUT luteal-vs-foll (delta)")
for name, col in ROBUST:
    r_in, _ = rho(in_win[col], in_win["pdg"])
    r_temp, n_t = rho(out_win[col], out_win["temp_deviation"])
    r_temp_p, _ = st.partial_spearman(out_win, col, "temp_deviation", "date_ord")
    r_est, _ = rho(out_win[col], out_win["est_pdg"])
    pc = st.phase_contrast(out_win, col)
    print(f"{name:24s} |   {r_in:+.2f} (n={len(in_win)})  |  {r_temp:+.2f} (n={n_t}) | {r_temp_p:+.2f}                  | {r_est:+.2f}          | {pc.cliffs_delta:+.2f} ({pc.cycles_consistent}/{pc.cycles_total} cyc)")

banner("DIRECTION-AGREEMENT SUMMARY (sign of in-window PdG coupling vs out-of-sample temp coupling)")
agree = 0
for name, col in ROBUST:
    r_in, _ = rho(in_win[col], in_win["pdg"])
    r_temp, _ = rho(out_win[col], out_win["temp_deviation"])
    same = (np.sign(r_in) == np.sign(r_temp))
    agree += int(same)
    print(f"  {name:24s}: in {np.sign(r_in):+.0f}  out {np.sign(r_temp):+.0f}  -> {'AGREE' if same else 'disagree'}")
print(f"Agreement: {agree}/{len(ROBUST)} features keep the same direction out-of-sample")

# ---------------------------------------------------------------------------
banner("HYPOTHESIS-FREE SCAN: every voice feature vs temperature proxy (all voice+oura days)")
allv = voice[voice["temp_deviation"].notna()].copy()
print("n days:", len(allv))
rows = []
base_all = sorted({c[len(t)+1:] for c in voice.columns for t in ("vowel", "prosody")
                   if c.startswith(t + "_egemaps_")})
for base in base_all:
    for task in ["vowel", "prosody"]:
        col = f"{task}_{base}"
        if col not in allv:
            continue
        r, n = rho(allv[col], allv["temp_deviation"])
        rp, _ = st.partial_spearman(allv, col, "temp_deviation", "date_ord")
        _, p = stats.spearmanr(allv[[col, "temp_deviation"]].dropna()[col],
                               allv[[col, "temp_deviation"]].dropna()["temp_deviation"]) if n >= 5 else (np.nan, np.nan)
        fam = tax.family_of(base) or "other"
        rows.append(dict(base=base, task=task, family=fam, n=n, rho=r, p=p, partial=rp))
scan = pd.DataFrame(rows)
scan["q"] = st.benjamini_hochberg(scan["p"].to_numpy())
scan["abs_partial"] = scan["partial"].abs()
top = scan.sort_values("abs_partial", ascending=False).head(20)
def short(b):
    return tax.label_of(b) if tax.family_of(b) else b.replace("egemaps_", "").replace("_sma3nz", "").replace("_sma3", "")
top = top.assign(feature=top["base"].map(short))
print(top[["feature", "task", "family", "n", "rho", "partial", "p", "q"]].to_string(index=False))

banner("SCAN: how do families rank by |date-controlled rho| with temperature?")
fam = scan.groupby("family")["abs_partial"].agg(["count", "mean", "median", "max"]).sort_values("median", ascending=False)
print(fam.to_string())
