"""Phoneme-level feature taxonomy, grouping axes, and contrast definitions.

The four segment features available at the phoneme grain map onto the
source-filter mechanism families established in the whole-recording study
(`src/analysis/feature_taxonomy.py`):

- segment_h1h2_mean       -> SURFACE (glottal open-quotient / breathiness proxy)
- segment_f1_bandwidth_mean -> SURFACE (resonance damping)
- segment_mfcc2_mean      -> TIMBRE  (low-vs-mid spectral shape)
- segment_f0_mean         -> SOURCE PITCH (used mainly as a confound covariate)

`voiced_only` marks features computed over F0>0 frames only; their nulls on
voiceless phonemes are expected (not missing data) and must never be imputed.
"""

from __future__ import annotations

# Segment feature -> (human label, mechanism family, voiced_only, unit)
SEGMENT_FEATURES: dict[str, tuple[str, str, bool, str]] = {
    "segment_h1h2_mean": ("H1-H2 (open quotient / breathiness)", "surface", True, "dB"),
    "segment_f1_bandwidth_mean": ("F1 bandwidth (resonance damping)", "surface", True, "Hz"),
    "segment_mfcc2_mean": ("MFCC2 (low-vs-mid timbre)", "timbre", False, "unitless"),
    "segment_f0_mean": ("F0 (source pitch)", "source_pitch", True, "semitones"),
}

FAMILY_LABELS: dict[str, str] = {
    "surface": "Surface / damping (mucosa & closure)",
    "timbre": "Spectral envelope / timbre (MFCC)",
    "source_pitch": "Source pitch (fold mass/tension)",
}

# Primary outcome features (exclude F0, which is the pitch confound we control for).
PRIMARY_FEATURES: list[str] = [
    "segment_h1h2_mean",
    "segment_f1_bandwidth_mean",
    "segment_mfcc2_mean",
]

# Articulatory grouping axes (the "middle" analysis level).
GROUPING_AXES: list[str] = [
    "phonemeManner",
    "phonemeVoicing",
    "phonemeBroadClass",
    "phonemeHeight",
]

# Vowel height as an ordinal axis (consonants are null by design).
HEIGHT_ORDER: dict[str, int] = {"low": 0, "mid": 1, "high": 2}


# --- Within-recording contrasts (self-normalizing biomarkers) -----------------
# Each contrast is the within-recording mean difference (group_a - group_b) of a
# feature. Because both groups come from the same recording, any recording-level
# offset (mic gain, distance, overall loudness, day-to-day technique) cancels.
#
# spec: name -> (feature, group_a_predicate_key, group_b_predicate_key, rationale)
# predicate keys are resolved in contrasts.py against the phoneme frame.
CONTRAST_SPECS: list[dict[str, str]] = [
    {
        "name": "voiced_minus_voiceless_mfcc2",
        "feature": "segment_mfcc2_mean",
        "group_a": "voiced",
        "group_b": "voiceless",
        "rationale": "Phonatory vs aperiodic timbre; literature reports an enhanced "
        "voiced/voiceless contrast in the high-hormone phase (VOT/plosive work).",
    },
    {
        "name": "highvowel_minus_lowvowel_h1h2",
        "feature": "segment_h1h2_mean",
        "group_a": "high_vowel",
        "group_b": "low_vowel",
        "rationale": "Open-quotient difference between high and low vowels; a "
        "self-normalizing breathiness contrast independent of recording gain.",
    },
    {
        "name": "nasaladj_minus_oral_h1h2",
        "feature": "segment_h1h2_mean",
        "group_a": "nasal_adjacent_vowel",
        "group_b": "oral_vowel",
        "rationale": "Nasal coupling probe; congestion/edema is reported to raise "
        "nasalance premenstrually, which should widen this contrast.",
    },
    {
        "name": "sonorant_minus_obstruent_mfcc2",
        "feature": "segment_mfcc2_mean",
        "group_a": "sonorant",
        "group_b": "obstruent",
        "rationale": "Broad-class timbre contrast; sonorants carry sustained "
        "phonation where mucosal-cover effects should concentrate.",
    },
]
