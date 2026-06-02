# Professor Presentation Story: Signal + Null Feature Contrast

Time window: `2026-01-01` to `2026-03-31`

This package is designed as a direct slide narrative where null results are used as mechanism filters, not as missing findings.

## Files in this folder (recommended slide order)

1. `01_signal_exists_cycling_features.png`
1b. `01b_signal_exists_cycling_features_weekly_mean.png`
2. `02_geometry_is_stable_formant_frequencies.png`
3. `03_gross_mechanics_are_stable.png`
4. `04_pair_f1_frequency_vs_f1_bandwidth.png`
5. `05_pair_f0_mean_vs_h1_h2.png`
6. `06_cycle_lag_strength_comparison.png`
7. `07_null_vs_signal_evidence_map.png`
8. `08_mechanism_concept_diagram.png`
9. `feature_evidence_table.csv`

## Section 1 - The signal exists

Use `01_signal_exists_cycling_features.png` to open with features already known to move with cycle-related hormone dynamics.
Use `01b_signal_exists_cycling_features_weekly_mean.png` as the week-over-week simplification of the same panel.

- **MFCC2 var**: flatness `0.264`, cycle lag `15d` (ACF `0.462`), best level linkage `0.613`
- **H1-H2**: flatness `0.225`, cycle lag `15d` (ACF `0.340`), best level linkage `0.562`
- **F1 bw var**: flatness `0.711`, cycle lag `15d` (ACF `0.445`), best level linkage `0.405`
- **MFCC3 mean**: flatness `0.134`, cycle lag `14d` (ACF `0.480`), best level linkage `0.404`

## Section 2 - Geometry anchor check

Use `02_geometry_is_stable_formant_frequencies.png`. The formant center frequencies are treated as tract geometry anchors.

- **F1 freq**: flatness `0.559`, cycle lag `16d` (ACF `0.361`), best level linkage `0.646`
- **F2 freq**: flatness `0.595`, cycle lag `18d` (ACF `0.426`), best level linkage `0.675`
- **F3 freq**: flatness `0.600`, cycle lag `15d` (ACF `0.401`), best level linkage `0.706`

Interpretation line: these features are comparatively range-stable by flatness and robust CV, but linkage strength is not zero; treat this as a partial null check rather than a hard null.

## Section 3 - Gross mechanics anchor check

Use `03_gross_mechanics_are_stable.png` for F0 mean, jitter, shimmer, and loudness.

- **F0 mean**: flatness `0.693`, cycle lag `20d` (ACF `0.257`), best level linkage `0.298`
- **Jitter**: flatness `0.652`, cycle lag `16d` (ACF `0.339`), best level linkage `0.321`
- **Loudness**: flatness `0.495`, cycle lag `10d` (ACF `0.347`), best level linkage `0.660`
- **Shimmer**: flatness `0.707`, cycle lag `18d` (ACF `0.412`), best level linkage `0.755`

Interpretation line: F0 and jitter look closer to null anchors, while shimmer and loudness show more coupling than expected. This narrows the mechanism argument but does not fully close alternatives.

## Section 4 - Pairwise contrasts isolate where change happens

- `04_pair_f1_frequency_vs_f1_bandwidth.png`: same formant family, center frequency mostly stable while bandwidth dynamics carry the cycle-linked pattern.
- `05_pair_f0_mean_vs_h1_h2.png`: fundamental rate mostly stable while source spectral balance carries stronger cycle-linked movement.

## Section 5 - Mechanism synthesis

- `06_cycle_lag_strength_comparison.png` shows cycle-lag periodicity values and lags for each selected feature.
- `07_null_vs_signal_evidence_map.png` places each feature on stability vs hormone-linkage axes as a direct null-check diagnostic.
- `08_mechanism_concept_diagram.png` is the conceptual close: surface-layer modulation remains plausible, with explicit acknowledgement that null-anchor evidence is mixed.

## Suggested spoken talk track (short)

1. We first confirm that selected acoustic features do track cycle-associated hormone dynamics.
2. We then run null checks on geometry and gross mechanics anchors instead of assuming they are flat.
3. Some anchors are comparatively stable, but a few still show moderate linkage, so the null evidence is mixed.
4. The clearest selective movement remains in spectral texture and damping-linked features.
5. Therefore surface-layer modulation is a plausible leading hypothesis, still exploratory and hypothesis-generating.

## Caution for claims

- Keep all wording exploratory, not causal.
- Treat exact lag values as dataset-specific.
- Emphasize that null results are evidence constraints, not absence of analysis.
