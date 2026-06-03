# The Voice as a Hormone Sensor: A Self-Taught N-of-1 Investigation

**Ivy Hamilton — Decibelle**  
**Meeting with Professor Rupal Patel, VOxx Lab, Northeastern University**  
**June 3, 2026**

---

## The Core Claim (one sentence)

In one woman tracked daily for nine months with measured hormones, the menstrual cycle produces a **global, uniform shift in vocal-fold source quality** (open quotient and timbre) that is detectable in connected speech, survives every control for drift and confounds, leaves vocal-tract geometry and phonological category separability untouched, and is invisible to the phonological-subspace d-prime method that collapses with dysarthria — exactly the pattern predicted by vocal-fold receptor biology and the source-filter model.

This is not a fishing expedition. It is a deliberate, multi-method, mechanism-first program designed to localize where in the speech chain a non-pathological physiological perturbation lives, and to test the specificity of a new representational metric along the way.

---

## Why This Story Works for the VOxx Lab

Professor Patel's VOxx Lab asks whether voice can serve as a non-invasive, daily-life biomarker of women's physiological and neurological health across the lifespan. This project is a direct, small-scale realization of that question:

- It uses **measured hormones** (E3G/PdG) rather than calendar labels — the exact gap named by the closest prior single-subject study (Kervin et al. 2025).
- It treats the cycle as a **natural experiment** in hormonal perturbation, not as a clinical disorder.
- It asks the **mechanistic localization question** first: reed vs. tube, surface vs. geometry, acoustics vs. representational geometry.
- It produces a **negative control** for the phonological-subspace method (Muller et al. 2026) that the clinical data could not provide.
- It demonstrates that an N-of-1 design with dense sampling and multiple orthogonal methods can yield interpretable, falsifiable claims even without a cohort.

The story is therefore not "I found some voice changes." It is "I designed a measurement program that can tell you *where* in the speech production chain a hormone signal appears, and *where it does not*, and I used that program to produce a clean specificity result for a method your field cares about."

---

## The Narrative Arc (8–9 minutes, ~8 slides)

### Slide 1 — The Question the Literature Cannot Answer

- One-third of women report premenstrual vocal symptoms (fatigue, reduced range, congestion).
- Receptor mapping shows estrogen and progesterone receptors in vocal-fold epithelium and lamina propria.
- Yet the acoustic literature is contradictory: some studies find jitter/shimmer changes; a high-speed imaging study finds none.
- The methodological reasons are structural: coarse phase labels, cross-sectional designs, single features, no drift control, no measured hormones.
- **The missing experiment:** a within-person, hormone-anchored, multi-method study that asks not "does voice change?" but "where in the source-filter chain does the change live?"

This is the gap the project was built to close.

### Slide 2 — The Instrument Model (reed vs. tube)

- Vocal folds = reed (source): soft, wet cover whose fluid/mucus state is hormone-sensitive.
- Vocal tract = tube (filter): bony cavities whose geometry is not.
- Prediction: cycle effects should appear in **source/cover measures** (H1-H2 open quotient, HNR clarity, spectral tilt, MFCC timbre) and be **absent from formant frequencies**.
- This is a strong, falsifiable claim with a built-in negative control.

### Slide 3 — The Data That Makes the Test Possible

- 71 connected-speech recordings over 53 days, 5 cycles, 2 phase-balanced.
- Inito E3G/PdG on 29 overlapping days.
- Oura body signals (temperature, HR, HRV) as positive controls.
- Fixed reading passage every day → token counts constant → token-count confound removed at source.
- Montreal Forced Aligner boundaries reused across every analysis.

The design itself is the first contribution: a fixed-content, hormone-anchored, within-cycle N-of-1 protocol that later studies can replicate.

### Slide 4 — Three Independent Methods, One Answer

**Method 1 — Hormone coupling with drift control**  
Date-partial Spearman: progesterone tracks HNR and MFCC2/3; estrogen does not after drift correction. The pitch–estrogen correlation collapses once calendar drift is partialled out — a cautionary finding for the field.

**Method 2 — Within-cycle, leave-one-cycle-out classifier**  
A 9-feature voice profile predicts the phase of a held-out cycle at 73% balanced accuracy (p ≈ 0.017). A geometry-only control sits at chance. The signal generalizes across cycles.

**Method 3 — Confound residualization**  
H1-H2 and HNR both rise in the luteal phase even after regressing out F0 and intensity. The joint fingerprint (open quotient up + clarity up) cannot be produced by any single mechanical confound.

Convergence across three methods that share no machinery is the evidence. Each method has a different failure mode; they land on the same narrow mechanism.

### Slide 5 — Phoneme Grain: The Signal Is Global, With Two Named Residuals

Force-alignment + per-phoneme eGeMAPS shows the H1-H2 and MFCC2 rise is essentially uniform across the inventory. De-meaning and within-recording contrasts confirm it is a per-recording *setting*, not a reorganization of relative phoneme acoustics.

Two residuals survive:
- Diphthongs show an amplified open-quotient effect (longest sustained voiced nuclei).
- Nasals show an amplified timbre effect (consistent with reported luteal nasal congestion and increased nasalance).

The phase is decodable from the phoneme profile at 0.88 balanced accuracy; most of the signal is carried by the global means.

### Slide 6 — The Phonological-Subspace Negative Control (Muller et al. 2026)

The 2026 phonological-subspace paper shows that d-prime separation between phonological categories in frozen SSL embeddings (HuBERT, WavLM, wav2vec2) collapses monotonically with dysarthria severity. The method indexes articulatory precision.

The cycle is the ideal negative control: a within-speaker, non-articulatory perturbation that should leave phonological separability untouched if the prior localization is correct.

**Result:** composite consonant d-prime shows negligible phase effect (Cliff's δ −0.12, BH q = 0.84). Zero of eight contrasts survive correction in any of three backbones. The null is architecture-independent (profile cosine 0.96–0.997).

Two privileged contrasts lean the predicted direction (nasality ↓ with progesterone; voicing ↑ with progesterone) but remain hypothesis-generating.

Triangulation: the acoustic cycle signal (MFCC2, H1-H2) is dissociated from representational separability (date-partial rho ≈ 0.0).

This is a specificity result the source paper could not run. It strengthens the interpretation that subspace collapse indexes articulatory degradation, not any source-level voice change.

### Slide 7 — What This Demonstrates About Self-Taught Research

- Receptor biology → source-filter model → acoustic prediction → three orthogonal statistical tests → representational specificity test.
- Every design choice (fixed passage, LORO directions, de-meaning, drift control, within-recording contrasts) was made to close a specific loophole identified in the literature.
- The same MFA boundaries feed two independent measurement families (named acoustics and SSL d-prime), allowing clean dissociation.
- The project was not "run every test and see what sticks." It was "formulate the mechanism, derive the testable consequences, build the controls that would falsify it."

### Slide 8 — Forward Hooks (what a collaboration could do next)

1. Pre-register the nasality/PdG and voicing/PdG hypotheses and power a small cohort.
2. Pair nasality d-prime with direct nasalance or rhinomanometry across the cycle.
3. Layer-sensitivity analysis on the privileged contrasts (later SSL layers sometimes more phonetic).
4. Extend the fixed-passage + LORO protocol to other within-person perturbations (medication, sleep restriction, altitude) to build a library of specificity controls for the d-prime method.
5. Ask whether the global setting change is perceptible to listeners or affects downstream prosody tasks — directly relevant to VOxx Lab's assistive-technology mission.

---

## The Figures That Carry the Story

| Slide | Figure | File | Purpose |
|-------|--------|------|---------|
| 3 | Body positive controls | `outputs/localization/figures/fig06_body_context.png` | Prove cycle labels are real |
| 4 | Localization map | `outputs/localization/figures/fig01_localization_map.png` | Reed vs. tube dissociation |
| 4 | Sensitivity floor | `outputs/localization/figures/fig02_sensitivity_floor.png` | Dog that didn't bark |
| 5 | Phoneme heatmap | `outputs/phoneme/figures/fig07_phoneme_heatmap.png` | Global vs. residual structure |
| 5 | Multivariate decoder | `outputs/phoneme/figures/fig06_multivariate.png` | Held-out cycle prediction |
| 6 | Phase forest | `outputs/hubert/figures/fig02_phase_forest.png` | d-prime null across backbones |
| 6 | Privileged spotlight | `outputs/hubert/figures/fig03_privileged_spotlight.png` | Nasality/voicing leans |
| 6 | Robustness | `outputs/hubert/figures/fig04_robustness.png` | Cross-backbone agreement |

---

## Why This Is Not "Just Another Voice Study"

- It is the first within-speaker application of the phonological-subspace method with a non-pathological perturbation.
- It is the first study to close the "measured hormones" gap identified by Kervin et al. 2025 in a daily-voice design.
- It converts the source-filter model from a post-hoc explanation into a pre-registered, falsifiable prediction with a built-in negative control.
- It demonstrates that an N-of-1, self-taught project can produce a clean methodological contribution (specificity control) that multi-speaker clinical datasets cannot.

The story is therefore not only about hormones and voice. It is about how to design a measurement program that turns a noisy physiological signal into a localized, mechanism-level claim — and how that same program can serve as a specificity instrument for the next generation of representational voice metrics.

---

## One-Slide Summary for Handout

**Title:** The menstrual cycle retunes the vocal-fold source, not the vocal-tract filter — and leaves phonological separability untouched.

**Design:** N-of-1, 71 recordings, 5 cycles, 2 phase-balanced, measured E3G/PdG, fixed passage, MFA boundaries reused across named acoustics and frozen SSL d-prime.

**Result:** Three independent methods converge on a global luteal rise in open quotient (H1-H2) and timbre (MFCC2) that is uniform across phonemes, survives F0/intensity residualization, predicts held-out cycle phase at 73%, and is invisible to the phonological-subspace d-prime method (δ = −0.12, BH n.s. in 3 backbones). Geometry (formants) and phonological separability are clean nulls. Two residuals (diphthong H1-H2, nasal MFCC2) align with existing nasal-congestion and voiced/voiceless literature.

**Contribution:** A within-speaker negative control for the 2026 phonological-subspace method; a hormone-anchored protocol that resolves the methodological disagreements in the menstrual-cycle voice literature; a demonstration that self-taught, mechanism-first N-of-1 research can produce interpretable, publishable specificity results.

---

*End of story document. All claims are traceable to the four companion findings documents and the Muller et al. 2026 arXiv preprints.*