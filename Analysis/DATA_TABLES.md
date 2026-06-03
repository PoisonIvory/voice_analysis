# Data tables: hormone-anchored voice-cycle analysis

Supporting tables for the presentation *"Where does a cycle-linked voice signal live?"*
Each table is tied to the slide it backs. All values come directly from the analysis output tables in `outputs/`.

**Scope and framing.** Single speaker, exploratory, hypothesis-generating. Effect sizes are within-person associations, not causal effects or population findings. Hormone links are date-partial Spearman associations on hormone-overlap days, not causal claims.

**Conventions.**
- **Cliff's δ** = nonparametric luteal-vs-follicular effect size. Magnitude bands: negligible < 0.147, small < 0.33, medium < 0.474, large ≥ 0.474.
- **Partial ρ** = date-partial Spearman correlation (controls for month-over-month drift).
- **BH q** = Benjamini-Hochberg FDR-adjusted p-value.
- Tasks: **prosody** = read/connected speech; **vowel** = sustained vowel.
- Hormones: **E3G** = estrone-3-glucuronide (estrogen metabolite); **PdG** = pregnanediol glucuronide (progesterone metabolite).

---

## Table 1 - Data coverage and sample sizes
*Backs slide 3 (Data foundation). Sources: `outputs/localization/tables/summary.json`, `outputs/phoneme/tables/summary.json`.*

| Measure | Count |
|---|---|
| Voice recording days | 59 |
| Voice days with a phase label | 57 |
| Voice + hormone overlap days | 29 |
| Phase-balanced cycles (recordings in both phases) | 2 (2026-01-14, 2026-02-12) |
| Follicular days (analyzable phoneme set) | 30 |
| Luteal days (analyzable phoneme set) | 22 |
| Clean recordings (phoneme/SSL set) | 71 |
| Analyzable force-aligned phonemes | 7,519 |
| SSL model backbones | 3 (HuBERT, wav2vec2, WavLM) |

**Read with caution.** The main cycle contrast rests on 2 cycles with recordings in both phases. Coverage is densest January-March 2026.

---

## Table 2 - Localization: signal-vs-spared dissociation test
*Backs slide 6 (Localization). Source: `outputs/localization/tables/dissociation_test.csv` (5,000 permutations).*

| Task | Feature set | Moved \|δ\| | Spared (geometry) \|δ\| | Dissociation D | Permutation p |
|---|---|---|---|---|---|
| Prosody | Focused | 0.519 | 0.287 | 0.232 | **0.008** |
| Vowel | Focused | 0.369 | 0.201 | 0.168 | **0.049** |
| Prosody | Broad | 0.408 | 0.287 | 0.121 | 0.100 |
| Vowel | Broad | 0.278 | 0.201 | 0.077 | 0.233 |

**Interpretation.** The moved feature set (surface/source quality + timbre) separates from the spared set (vocal-tract geometry) in both tasks under the focused contrast. The broad contrast is the more conservative variant and does not reach significance, so this is moderate, not decisive, evidence.

---

## Table 3 - What moved vs what stayed, by mechanism
*Backs slide 6 (Localization). Source: `outputs/localization/tables/feature_effects.csv`, prosody task, n = 33 days.*

| Mechanism | Feature | Cliff's δ | Magnitude |
|---|---|---|---|
| Surface / source quality | Clarity (HNR) | 0.588 | large |
| Surface / source quality | Alpha ratio (spectral tilt) | -0.713 | large |
| Surface / source quality | Source tilt (H1-A3) | 0.559 | large |
| Surface / source quality | Hammarberg index | 0.434 | medium |
| Surface / source quality | Shimmer | -0.368 | medium |
| Surface / source quality | Open quotient (H1-H2) | 0.272 | small |
| Timbre | MFCC2 (low-vs-mid colour) | 0.743 | large |
| Timbre | MFCC3 | 0.478 | large |
| Timbre | MFCC1 (brightness) | 0.243 | small |
| Pitch level | F0 mean | -0.051 | negligible |
| Pitch level | F0 median | -0.007 | negligible |
| Vocal-tract geometry | F1 (mouth openness) | 0.162 | small |
| Vocal-tract geometry | F2 (tongue front-back) | 0.324 | small |
| Vocal-tract geometry | F3 (fine tract shape) | 0.375 | medium |

**Interpretation.** The largest effects concentrate in surface/source quality and timbre. Mean pitch is negligible. Geometry formant frequencies are small-to-medium and clearly below the surface/timbre cluster; the dissociation test (Table 2) and sensitivity floor (Table 4) formalize that this geometry result is a genuine null, not a measurement limit. F3 is the least clean of the geometry anchors and is flagged as such.

---

## Table 4 - Sensitivity floor: the geometry null is not insensitivity
*Backs slide 11 (Appendix - sensitivity). Source: `outputs/localization/tables/sensitivity_floor.csv`.*

| Formant | Mean (Hz) | Within-recording SD (Hz) | Vowel-vs-prosody shift (Hz) | Across-cycle shift (Hz) | Sensitivity ratio (within-rec) | Sensitivity ratio (task) |
|---|---|---|---|---|---|---|
| F1 (mouth openness) | 615 | 184 | 36.7 | 1.8 | 105x | 20.9x |
| F2 (tongue front-back) | 1674 | 210 | 114.3 | 5.8 | 36x | 19.8x |
| F3 (fine tract shape) | 2770 | 235 | 30.0 | 34.9 | 6.7x | 0.86x |

**Interpretation.** F1 and F2 resolve much larger movements within speech and between tasks than they show across the cycle (sensitivity ratios up to ~105x), so their flat cycle response is informative. F3 is the exception: its across-cycle shift (34.9 Hz) is comparable to its task shift, so F3 is not used as a clean geometry anchor.

---

## Table 5 - Hormone coupling: PdG vs E3G after drift control
*Backs slide 7 (Hormones and drift). Source: `outputs/localization/tables/summary.json` (arm summary) and `outputs/localization/tables/hormone_coupling.csv` (per-feature), prosody, n = 29.*

Arm-level mean absolute partial ρ:

| Arm | E3G (estrogen) | PdG (progesterone) |
|---|---|---|
| Peripheral (surface/source quality) | 0.075 | **0.237** |
| Central (pitch/timing control) | 0.149 | 0.172 |

Selected per-feature date-partial ρ:

| Feature | E3G partial ρ | PdG partial ρ |
|---|---|---|
| Hammarberg index (spectral tilt) | 0.140 | 0.434 |
| MFCC2 (timbre) | 0.121 | 0.408 |
| Clarity (HNR) | 0.088 | 0.349 |
| Alpha ratio (spectral tilt) | 0.054 | -0.292 |
| Source tilt (H1-A3) | -0.012 | 0.281 |

**Interpretation.** After removing shared month-over-month drift, surface/source-quality measures couple more with PdG than E3G. A raw pitch-estrogen correlation weakened under the same drift control. These are associations on 29 overlap days, not a PMDD biomarker.

---

## Table 6 - Phoneme residuals that survived de-meaning + FDR
*Backs slides 8 and 12 (phoneme grain). Source: `outputs/phoneme/tables/localization.csv`. follicular = 30 days, luteal = 22 days; PdG partial n = 29.*

| Feature | Phoneme class | Raw δ (magnitude) | De-meaned δ | Mann-Whitney p | BH q |
|---|---|---|---|---|---|
| Open quotient (H1-H2) | Diphthong | 0.561 (large) | 0.312 | 0.0006 | **0.023** |
| Timbre (MFCC2) | Nasal | 0.497 (large) | 0.361 | 0.0025 | **0.049** |

For comparison, the same features in other classes mostly collapse toward zero once the recording-wide offset is removed (consistent with a global setting):

| Feature | Phoneme class | Raw δ | De-meaned δ |
|---|---|---|---|
| Open quotient (H1-H2) | Vowel | 0.330 | -0.052 |
| Open quotient (H1-H2) | Obstruent | 0.233 | 0.012 |
| Timbre (MFCC2) | Vowel | 0.288 | -0.167 |
| Timbre (MFCC2) | Obstruent | 0.464 | 0.003 |

**Interpretation.** Most of the per-phoneme signal behaves like a recording-wide setting (raw effects shrink to negligible after de-meaning). Two residuals survive de-meaning and FDR and are mechanistically coherent (diphthong open quotient, nasal timbre), but remain single-subject leads. The diphthong residual holds after an F0 control (residual R² = 0.097).

---

## Table 7 - SSL negative control: cycle does not resemble degraded articulation
*Backs slide 9 (Negative control). Source: `outputs/hubert/tables/phase_contrasts.csv` and `summary.json`. HuBERT-base shown; follicular = 30, luteal = 22.*

| Contrast | Role | Cliff's δ | Magnitude | BH q |
|---|---|---|---|---|
| Consonant composite (mean of 5) | Composite | -0.121 | negligible | 0.836 |
| Sonorance (sonorant vs obstruent) | Other consonant | -0.418 | medium | 0.098 |
| Vowel height (high vs non-high) | Geometry control | -0.358 | medium | 0.133 |
| Nasality (nasal vs oral stop) | Cycle-privileged | -0.218 | small | 0.556 |
| Voicing (obstruents) | Cycle-privileged | 0.121 | negligible | 0.836 |
| Stridency (sibilant vs non-sibilant) | Other consonant | 0.018 | negligible | 0.934 |
| Manner (continuant: fricative vs stop) | Other consonant | -0.036 | negligible | 0.934 |
| Vowel lowness (low vs non-low) | Geometry control | 0.015 | negligible | 0.934 |
| Vowel backness (back vs front) | Geometry control | -0.048 | negligible | 0.934 |

**Cross-backbone robustness:** 0 of 8 contrasts survive FDR across all three backbones (HuBERT, wav2vec2, WavLM). Inter-backbone agreement ρ = 0.39-0.75; profile cosine ≥ 0.959.

**Interpretation.** Frozen speech-model phonological separability does not collapse with cycle phase (composite δ = -0.12, negligible). This argues against an articulation-degradation explanation and is consistent with the acoustic surface/timbre interpretation.
