Hypothesis
Hormonal fluctuations across the menstrual cycle cause selective physical changes to specific vocal tract substructures — most notably mucosal edema in the nasal passages driven by progesterone. These changes alter the acoustic properties of sounds that route through the affected substructure (nasal consonants and nasalized vowels) while leaving sounds that don't route through it (oral consonants, non-nasalized vowels) relatively unaffected. The result is a measurable, cyclic shift in the acoustic features of nasal-coupled phonemes that tracks with hormonal phase.
The whole-passage MFCC2 stddevNorm signal you're already seeing is a downstream consequence of this: the within-recording spread increases when the nasal phonemes shift away from the oral phonemes, and decreases when the tract is more uniform.
Goal
Demonstrate that the acoustic biomarker signal is phoneme-specific and anatomically localizable — not just a diffuse "voice sounds different" effect. If you can show that specific phoneme classes shift in predictable ways tied to specific hormonal drivers, you have something much more powerful than a black-box correlation. You have a mechanistic biomarker with an explainable physiological pathway.
This matters both scientifically (it's a testable, falsifiable mechanism) and commercially (explainability is critical for clinical adoption and regulatory conversations).
Investigation approaches
1. Phoneme-conditional longitudinal tracking
This is the direct test. Use forced alignment to segment your existing Rainbow Passage recordings into phonemes, extract MFCC2 (and other features) per phoneme, group by articulatory class, and track each group's mean longitudinally against your Inito hormone data.
What you're looking for: Nasal phoneme MFCC2 should correlate more strongly with PdG (and possibly E3G) than oral phoneme MFCC2. If the nasal-edema hypothesis is correct, the nasal group carries the signal and the oral group is relatively flat across the cycle. The difference between nasal and oral MFCC2 — a within-recording contrast that controls for day-to-day recording variability — might be the cleanest biomarker of all.
What you already have to do this: Your full library of Rainbow Passage recordings, Parselmouth, and your Inito hormone curves. You'd just need to add MFA for alignment.
2. Anatomical group contrasts
Go beyond nasal vs. oral. Define groups by which anatomical substructure is most involved:

Nasal-coupled: /m/, /n/, /ŋ/, nasalized vowels adjacent to nasals
Pharyngeal: low vowels like /ɑ/, pharyngeal constrictions, which involve the pharyngeal walls (also hormone-responsive mucosa)
Glottal-source-dominated: voiceless fricatives like /s/, /f/, where the tract shape matters less and the source spectrum dominates
Oral-anterior: /t/, /d/, /p/, /b/ — articulation at the lips and alveolar ridge, relatively less mucosal tissue involved

If the signal is truly about mucosal edema, you'd predict a gradient: nasals show the strongest effect, pharyngeal sounds show some effect, and oral-anterior stops and voiceless fricatives show little to none. That gradient would be strong evidence for the mechanism.
3. Feature selection within phoneme groups
MFCC2 happened to show up in the whole-passage analysis, but once you're analyzing per-phoneme, other features might be even more informative. Within nasal segments specifically:

Formant bandwidths (especially anti-resonance bandwidth) would directly reflect mucosal damping changes.
Nasalance-related features from your nasalance protocol could be more targeted.
MFCC1 within nasals might capture edema-driven changes to spectral tilt that are masked at the whole-passage level.
Harmonics-to-noise ratio within nasals could reflect how edema affects the coupling efficiency.

You'd essentially do feature discovery within the nasal phoneme class, which is a much more constrained and interpretable search than feature discovery across the whole recording.

4. Lag analysis by phoneme group
You mentioned the possibility of hormone-to-effect lag. Once you have phoneme-group time series, you can run lagged correlations for each group separately. It's plausible that different substructures respond on different timescales — nasal mucosal edema might lag PdG by 1–2 days, while laryngeal effects (which involve different tissue with potentially different receptor density) might lag differently. If the lag structure differs by phoneme group, that's further evidence that you're picking up distinct anatomical effects, not just a single systemic change.
6. Within-cycle averaging
Once you have enough cycles, you can create a phase-averaged profile: align all your cycles by a hormonal landmark (like the LH surge or ovulation day), then average the nasal-phoneme MFCC2 across cycles at each phase-relative day. This would show you the canonical shape of the effect — when it rises, when it peaks, when it returns to baseline — with individual-cycle noise averaged out. Even 4–5 cycles would start giving you a meaningful profile.

The bigger picture for Decibella
If this line of investigation holds up, the implication is significant: voice biomarker systems that treat the whole utterance as a single feature vector are leaving signal on the table and potentially introducing confounds. A phoneme-aware approach — where you extract features conditional on what sound is being produced — could yield cleaner, more interpretable, more robust biomarkers. That's a differentiating technical insight for the company and a strong foundation for your Bridge2AI confound argument: if cycle phase selectively affects nasal phonemes, then any disease-detection model trained on mixed phoneme features without controlling for cycle phase is potentially confounded, and the confound is anatomically specific rather than diffuse.