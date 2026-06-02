# Phase 2 Hormone Linkage Report

## Scope

- Start date: `2026-01-16`
- Candidate features: `5`
- Hormones: `e3g, pdg`
- Rolling windows: `[3, 5]`
- Lag scan (hormone leads): `[0, 1, 2, 3]` days

## Best Linkage Per Feature-Hormone Pair

- `prosody_egemaps_mfcc2_sma3_stddevNorm` x `pdg` (level): rho `-0.613` at lag `0` (window `5` days, n `51`)
- `prosody_egemaps_logRelF0-H1-H2_sma3nz_amean` x `e3g` (level): rho `0.562` at lag `3` (window `3` days, n `31`)
- `prosody_egemaps_F1bandwidth_sma3nz_stddevNorm` x `e3g_rate_change_per_day` (rate_change): rho `0.477` at lag `0` (window `3` days, n `30`)
- `prosody_egemaps_F1bandwidth_sma3nz_stddevNorm` x `pdg_rate_change_per_day` (rate_change): rho `0.408` at lag `2` (window `5` days, n `50`)
- `prosody_egemaps_F1bandwidth_sma3nz_stddevNorm` x `pdg` (level): rho `0.405` at lag `1` (window `5` days, n `51`)
- `prosody_egemaps_mfcc3_sma3_amean` x `pdg` (level): rho `-0.404` at lag `1` (window `3` days, n `31`)
- `prosody_egemaps_mfcc2_sma3_stddevNorm` x `e3g` (level): rho `-0.369` at lag `3` (window `5` days, n `51`)
- `prosody_egemaps_logRelF0-H1-H2_sma3nz_amean` x `e3g_rate_change_per_day` (rate_change): rho `-0.341` at lag `1` (window `3` days, n `30`)
- `prosody_egemaps_mfcc2_sma3_stddevNorm` x `pdg_rate_change_per_day` (rate_change): rho `-0.325` at lag `3` (window `5` days, n `50`)
- `prosody_egemaps_alphaRatioUV_sma3nz_amean` x `pdg` (level): rho `0.315` at lag `3` (window `3` days, n `31`)
- `prosody_egemaps_logRelF0-H1-H2_sma3nz_amean` x `pdg` (level): rho `0.301` at lag `0` (window `3` days, n `31`)
- `prosody_egemaps_mfcc3_sma3_amean` x `e3g` (level): rho `0.295` at lag `3` (window `5` days, n `51`)
- `prosody_egemaps_mfcc2_sma3_stddevNorm` x `e3g_rate_change_per_day` (rate_change): rho `0.282` at lag `0` (window `5` days, n `50`)
- `prosody_egemaps_alphaRatioUV_sma3nz_amean` x `pdg_rate_change_per_day` (rate_change): rho `-0.279` at lag `3` (window `5` days, n `50`)
- `prosody_egemaps_mfcc3_sma3_amean` x `pdg_rate_change_per_day` (rate_change): rho `0.270` at lag `3` (window `5` days, n `50`)
- `prosody_egemaps_mfcc3_sma3_amean` x `e3g_rate_change_per_day` (rate_change): rho `0.259` at lag `3` (window `3` days, n `31`)
- `prosody_egemaps_alphaRatioUV_sma3nz_amean` x `e3g_rate_change_per_day` (rate_change): rho `0.257` at lag `0` (window `3` days, n `30`)
- `prosody_egemaps_alphaRatioUV_sma3nz_amean` x `e3g` (level): rho `-0.248` at lag `2` (window `5` days, n `51`)
- `prosody_egemaps_F1bandwidth_sma3nz_stddevNorm` x `e3g` (level): rho `-0.244` at lag `3` (window `3` days, n `31`)
- `prosody_egemaps_logRelF0-H1-H2_sma3nz_amean` x `pdg_rate_change_per_day` (rate_change): rho `0.182` at lag `3` (window `5` days, n `50`)

## Aggregate Level vs Rate-Change Top Links

### Level (smoothed hormone concentration)

- `prosody_egemaps_mfcc2_sma3_stddevNorm` x `pdg`: rho `-0.613` (lag `0`, window `5`, n `51`)
- `prosody_egemaps_logRelF0-H1-H2_sma3nz_amean` x `e3g`: rho `0.562` (lag `3`, window `3`, n `31`)
- `prosody_egemaps_F1bandwidth_sma3nz_stddevNorm` x `pdg`: rho `0.405` (lag `1`, window `5`, n `51`)

### Rate of change (first-difference of hormone concentration)

- `prosody_egemaps_F1bandwidth_sma3nz_stddevNorm` x `e3g_rate_change_per_day`: rho `0.477` (lag `0`, window `3`, n `30`)
- `prosody_egemaps_F1bandwidth_sma3nz_stddevNorm` x `pdg_rate_change_per_day`: rho `0.408` (lag `2`, window `5`, n `50`)
- `prosody_egemaps_logRelF0-H1-H2_sma3nz_amean` x `e3g_rate_change_per_day`: rho `-0.341` (lag `1`, window `3`, n `30`)

## Strong Candidate Links (|rho| >= 0.45)

- `prosody_egemaps_mfcc2_sma3_stddevNorm` x `pdg` (level): rho `-0.613` (lag `0`, window `5`, n `51`)
- `prosody_egemaps_logRelF0-H1-H2_sma3nz_amean` x `e3g` (level): rho `0.562` (lag `3`, window `3`, n `31`)
- `prosody_egemaps_F1bandwidth_sma3nz_stddevNorm` x `e3g_rate_change_per_day` (rate_change): rho `0.477` (lag `0`, window `3`, n `30`)

## Interpretation Notes

- This scan quantifies pattern strength and lag direction from the overlay plots.
- This is still exploratory linkage, not causal inference.
- Use as inputs for confirmatory repeated-measures modeling in the next pass.
