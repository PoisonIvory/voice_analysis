# Feature Trust Readme (Speech-Hormone Figures)

Date: 2026-06-02

This note is meant to reduce confusion and clearly state what we can trust right now from the current analysis artifacts.

## Short answer

You can trust the **data processing and plotting pipeline** as a descriptive workflow, but you should treat the figure-level conclusions as **exploratory** (not confirmatory).

For the five featured speech variables used in `outputs/figures`, confidence is mixed:

- Most stable/reliable for repeated visualization: `prosody_egemaps_F1bandwidth_sma3nz_stddevNorm`
- Most likely to be genuinely shifting: `prosody_egemaps_mfcc3_sma3_amean`, `prosody_egemaps_logRelF0-H1-H2_sma3nz_amean`
- Mixed/uncertain but still interesting: `prosody_egemaps_mfcc2_sma3_stddevNorm`, `prosody_egemaps_alphaRatioUV_sma3nz_amean`

## Why this felt contradictory

Three different concepts were being discussed as if they were one thing:

1. **Stability / consistency**: does a feature stay relatively steady over time?
2. **Periodicity**: does a feature repeat with a lag pattern?
3. **Hormone linkage strength**: how strongly does a feature co-vary with hormone signals (Spearman rho)?

A feature can be stable **and** periodic.  
A feature can be unstable **and** strongly linked to hormones.  
So these metrics do not have to agree.

## What the figure set includes

The presentation figures in `outputs/figures` are built from this 5-feature panel:

- `prosody_egemaps_F1bandwidth_sma3nz_stddevNorm`
- `prosody_egemaps_alphaRatioUV_sma3nz_amean`
- `prosody_egemaps_logRelF0-H1-H2_sma3nz_amean`
- `prosody_egemaps_mfcc2_sma3_stddevNorm`
- `prosody_egemaps_mfcc3_sma3_amean`

Figures are generated via daily aggregation, smoothing, and normalized hormone overlays (level or rate-change mode). They are valid for **pattern inspection**, but not by themselves proof of mechanism.

## Current evidence table (for the 5 plotted features)

Canonical source-of-truth datasets (reusable) are stored in `data/processed`:

- `data/processed/speech_feature_stability_periodicity_cycle_relevant.parquet`
- `data/processed/speech_feature_behavior_buckets.parquet`

Reporting/export copies can live in `outputs`:

- `outputs/speech_feature_stability_periodicity_scan_cycle_relevant.csv`
- `outputs/phase2_hormone_lag_scan.csv`

Important periodicity rule used here: only lags in the `7-20` day range are considered "cycle-relevant".
Short lags (for example, 2 days) are intentionally excluded from periodicity interpretation.

Interpretation labels are practical categories for decision-making (not hard biological truth).

- `prosody_egemaps_F1bandwidth_sma3nz_stddevNorm`
  - Stability score: `0.711` (highest of 5)
  - Cycle-relevant periodicity strength: `0.445` at lag `15` days (moderate; not top overall)
  - Best hormone linkage (`max |rho|`): `0.477`
  - Practical label: **more consistent anchor feature**

- `prosody_egemaps_alphaRatioUV_sma3nz_amean`
  - Stability score: `0.284`
  - Periodicity strength: `0.438` at lag `15` days
  - Best hormone linkage (`max |rho|`): `0.315`
  - Practical label: **mixed / weaker linkage**

- `prosody_egemaps_mfcc2_sma3_stddevNorm`
  - Stability score: `0.264`
  - Periodicity strength: `0.462` at lag `15` days
  - Best hormone linkage (`max |rho|`): `0.613` (strongest in panel)
  - Practical label: **mixed stability, high linkage**

- `prosody_egemaps_logRelF0-H1-H2_sma3nz_amean`
  - Stability score: `0.225`
  - Cycle-relevant periodicity strength: `0.340` at lag `15` days
  - Best hormone linkage (`max |rho|`): `0.562`
  - Practical label: **more shifting, strong linkage**

- `prosody_egemaps_mfcc3_sma3_amean`
  - Stability score: `0.134` (lowest of 5)
  - Cycle-relevant periodicity strength: `0.480` at lag `14` days
  - Best hormone linkage (`max |rho|`): `0.404`
  - Practical label: **more shifting**

## What to trust now for presentations

### High confidence (descriptive)

- The figures accurately display smoothed temporal co-movement patterns.
- The feature panel does show meaningful differences in behavior (stable vs shifting).
- Two strongest exploratory hormone-coupled signals remain:
  - `prosody_egemaps_mfcc2_sma3_stddevNorm` vs `pdg`
  - `prosody_egemaps_logRelF0-H1-H2_sma3nz_amean` vs `e3g`

### Medium confidence

- Ranking of which panel features are more stable vs more shifting is directionally useful.
- Periodicity findings are useful for hypothesis generation but are sensitive to preprocessing choices.

### Low confidence (do not over-claim)

- Any causal statement ("hormone X causes voice feature Y").
- Exact lag values as fixed biological constants.
- Generalization beyond this participant/time window.

## Recommended narrative for current figure deck

Use this wording style:

- "These plots show exploratory temporal alignment between selected speech features and hormone signals."
- "Some features appear relatively stable (for example, F1 bandwidth variability), while others appear more dynamic (for example, MFCC3 mean and spectral balance)."
- "This motivates confirmatory repeated-measures modeling rather than causal claims from overlays alone."

Avoid this wording:

- "This proves hormone-driven voice changes."
- "Lag is exactly N days for everyone."

## If you want a safer final subset right now

For a conservative presentation subset (balance of interpretability + signal):

1. Keep: `prosody_egemaps_F1bandwidth_sma3nz_stddevNorm` (stable anchor)
2. Keep: `prosody_egemaps_mfcc2_sma3_stddevNorm` (strongest linkage signal)
3. Keep: `prosody_egemaps_logRelF0-H1-H2_sma3nz_amean` (second strongest linkage)
4. De-emphasize or mark exploratory-only: `prosody_egemaps_mfcc3_sma3_amean`, `prosody_egemaps_alphaRatioUV_sma3nz_amean`

## Bottom line

You should not discard all figure features.  
A better interpretation is:

- **Some features are stable anchors**
- **Some are shifting signals**
- **All current results are exploratory and suitable for hypothesis refinement**

That is a trustworthy and defensible position for this stage.
