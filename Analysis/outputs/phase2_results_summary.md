# Phase 2 Results Summary (Hormone-Voice Linkage)

## What was run

- Command: `python -m src.analysis.run_phase2_hormone_linkage`
- Input: `data/processed/analysis_first_pass_merged.parquet`
- Candidate features (prosody): MFCC2 variability, spectral balance (H1-H2), MFCC3 mean, F1 bandwidth variability, alpha ratio (unvoiced)
- Hormones: `pdg`, `e3g`
- Smoothing windows: `3` and `5` days
- Lag scan: `0-3` days where hormone leads feature
- Start date filter: `2026-01-16`

## Primary findings

1. **Strongest overall linkage**
   - `prosody_egemaps_mfcc2_sma3_stddevNorm` vs `pdg`
   - Spearman rho: `-0.613`
   - Best config: `5-day` rolling, lag `0`, `n=51`
   - Interpretation: higher PdG aligns with lower MFCC2 variability in this dataset.

2. **Second strongest linkage**
   - `prosody_egemaps_logRelF0-H1-H2_sma3nz_amean` vs `e3g`
   - Spearman rho: `0.562`
   - Best config: `3-day` rolling, lag `3`, `n=31`
   - Interpretation: spectral balance increases as E3G rises, with a short delay.

3. **Moderate linkage tier**
   - `prosody_egemaps_F1bandwidth_sma3nz_stddevNorm` vs `pdg`: rho `0.405` (5-day, lag 1, n=51)
   - `prosody_egemaps_mfcc3_sma3_amean` vs `pdg`: rho `-0.404` (3-day, lag 1, n=31)

## Pattern consistency with figure review

- The quantified results are directionally consistent with hormone-overlay figures in `outputs/figures`.
- Repeating cycle windows (late Jan to early Feb, late Feb to early Mar) visually match top lag-scan associations.
- Strongest pair (`MFCC2 variability` vs `PdG`) remains strong across both `3-day` and `5-day` windows.

## What this means now

- The analysis supports a **targeted hormone-coupling hypothesis** for at least two candidate features.
- These are still **exploratory** associations and should not be presented as causal effects.
- This is sufficient to justify a confirmatory next pass focused on a short, pre-registered feature-hormone panel.

## Immediate next step (confirmatory pass)

- Fit repeated-measures models for:
  - `MFCC2 variability ~ PdG (+ lag sensitivity)`
  - `Spectral balance (H1-H2) ~ E3G (+ lag sensitivity)`
- Report effect size, confidence interval, and robustness to outlier-day exclusions.

## Related generated files

- Detailed scan table: `outputs/phase2_hormone_lag_scan.csv`
- Detailed report: `outputs/phase2_hormone_linkage_report.md`
