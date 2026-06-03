"""Phonological-contrast taxonomy and directional roles for the cycle test.

The nine binary contrasts mirror the paper's nine segmental d-prime features
(five consonant, four vowel). Here each is tagged with the role it plays in the
*menstrual-cycle* hypothesis set, which is what makes this study a test rather
than a re-run of the paper:

- cycle_privileged: a mechanism in the prior eGeMAPS/phoneme results predicts
  this contrast could move. `voicing` because the luteal open-quotient rise
  re-weights the voiced/voiceless split (and the read-speech literature reports
  an enhanced voiced/voiceless contrast in the high-hormone phase); `nasality`
  because luteal nasal congestion is the mechanism behind the prior nasal-MFCC2
  residual.
- geometry_control: vowel tongue-body geometry, expected to be inert, mirroring
  the inert formant geometry in the whole-recording study (negative control).
- other_consonant: the remaining consonant contrasts; part of the composite but
  with no specific directional prior.
- underpowered: `vowel_rounding` clears the 5-token minimum in ~0% of
  recordings of this passage, so it is excluded from all tests.
"""

from __future__ import annotations

CONSONANT_CONTRASTS: list[str] = ["nasality", "voicing", "sonorance", "stridency", "manner"]
VOWEL_CONTRASTS: list[str] = ["vowel_height", "vowel_lowness", "vowel_backness"]
EXCLUDED_CONTRASTS: list[str] = ["vowel_rounding"]

# Every contrast we test (rounding excluded by the minimum-token rule).
USABLE_CONTRASTS: list[str] = CONSONANT_CONTRASTS + VOWEL_CONTRASTS

# Mean of the five consonant d-primes; the paper's per-speaker composite and the
# primary outcome of the stability hypothesis (H1).
COMPOSITE_CONSONANT: str = "dprime_consonant_composite"

CYCLE_PRIVILEGED: list[str] = ["voicing", "nasality"]
GEOMETRY_CONTROLS: list[str] = ["vowel_height", "vowel_lowness", "vowel_backness"]

# contrast key -> (human label, family, role)
CONTRAST_META: dict[str, tuple[str, str, str]] = {
    "nasality": ("Nasality (nasal vs oral stop)", "consonant", "cycle_privileged"),
    "voicing": ("Voicing (obstruents)", "consonant", "cycle_privileged"),
    "sonorance": ("Sonorance (sonorant vs obstruent)", "consonant", "other_consonant"),
    "stridency": ("Stridency (sibilant vs non-sibilant)", "consonant", "other_consonant"),
    "manner": ("Manner (continuant: fricative vs stop)", "consonant", "other_consonant"),
    "vowel_height": ("Vowel height (high vs non-high)", "vowel", "geometry_control"),
    "vowel_lowness": ("Vowel lowness (low vs non-low)", "vowel", "geometry_control"),
    "vowel_backness": ("Vowel backness (back vs front)", "vowel", "geometry_control"),
    "vowel_rounding": ("Vowel rounding (rounded vs unrounded)", "vowel", "underpowered"),
}


def dprime_col(contrast_key: str) -> str:
    """Per-recording d-prime column name for a contrast (matches the parquet)."""
    return f"dprime_{contrast_key}"


def role(contrast_key: str) -> str:
    """Directional role of a contrast in the cycle hypothesis set."""
    return CONTRAST_META[contrast_key][2]


def label(contrast_key: str) -> str:
    """Human-readable label for a contrast."""
    return CONTRAST_META[contrast_key][0]
