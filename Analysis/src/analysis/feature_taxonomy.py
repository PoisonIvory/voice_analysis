"""Mechanism-based taxonomy of eGeMAPS voice features.

The taxonomy expresses a physiological hypothesis using the source-filter model
of voice production. It separates features by *what part of the system they
describe*, so cycle effects can be localized to a mechanism:

- GEOMETRIC features describe the *shape and size* of the vocal apparatus.
  The vocal tract (formant frequencies) is bony/cartilaginous and should be
  relatively stable across the cycle. This is our built-in negative control.

- SOURCE_PITCH features describe vocal-fold mass and tension (F0). Fluid shifts
  can move these modestly, so they sit between geometry and surface.

- SURFACE_DAMPING features describe the vocal-fold *cover* (mucosa), closure
  quality, turbulent noise, and how energy is damped. These are exactly what
  hormone-driven fluid/viscosity changes in the mucosa would move.

Base feature names omit the task prefix. Use `with_task` to resolve the actual
column name in the daily handoff table (e.g. `vowel_egemaps_...`).
"""

from __future__ import annotations

# --- Geometry: vocal-tract resonance positions (negative control) ---
GEOMETRIC_VOCAL_TRACT: dict[str, str] = {
    "egemaps_F1frequency_sma3nz_amean": "F1 frequency (vowel openness / front cavity)",
    "egemaps_F2frequency_sma3nz_amean": "F2 frequency (tongue advancement / back cavity)",
    "egemaps_F3frequency_sma3nz_amean": "F3 frequency (lip rounding / fine vocal-tract shape)",
}

# --- Source pitch: vocal-fold mass and tension ---
SOURCE_PITCH: dict[str, str] = {
    "egemaps_F0semitoneFrom27.5Hz_sma3nz_amean": "Mean pitch (F0)",
    "egemaps_F0semitoneFrom27.5Hz_sma3nz_percentile50.0": "Median pitch (F0)",
    "egemaps_F0semitoneFrom27.5Hz_sma3nz_percentile20.0": "Low pitch (F0 20th pct)",
    "egemaps_F0semitoneFrom27.5Hz_sma3nz_percentile80.0": "High pitch (F0 80th pct)",
}

# --- Surface / damping: mucosa, closure quality, noise, spectral tilt ---
SURFACE_DAMPING: dict[str, str] = {
    # Cycle-to-cycle perturbation of the mucosal wave
    "egemaps_jitterLocal_sma3nz_amean": "Jitter (pitch perturbation)",
    "egemaps_shimmerLocaldB_sma3nz_amean": "Shimmer (loudness perturbation)",
    # Turbulent noise from incomplete / leaky closure
    "egemaps_HNRdBACF_sma3nz_amean": "Harmonics-to-noise ratio (HNR)",
    # Spectral tilt: how sharply energy falls with frequency (glottal closure / damping)
    "egemaps_alphaRatioV_sma3nz_amean": "Alpha ratio (low-vs-high energy balance)",
    "egemaps_hammarbergIndexV_sma3nz_amean": "Hammarberg index (low-vs-high peak balance)",
    "egemaps_slopeV0-500_sma3nz_amean": "Spectral slope 0-500 Hz",
    "egemaps_slopeV500-1500_sma3nz_amean": "Spectral slope 500-1500 Hz",
    "egemaps_logRelF0-H1-H2_sma3nz_amean": "H1-H2 (glottal open quotient proxy)",
    "egemaps_logRelF0-H1-A3_sma3nz_amean": "H1-A3 (glottal source tilt)",
    # Vocal-tract damping: bandwidth is the energy loss of each resonance
    "egemaps_F1bandwidth_sma3nz_amean": "F1 bandwidth (resonance damping)",
    "egemaps_F2bandwidth_sma3nz_amean": "F2 bandwidth (resonance damping)",
    "egemaps_F3bandwidth_sma3nz_amean": "F3 bandwidth (resonance damping)",
}

# --- Spectral envelope / timbre: MFCCs (composite filter + source coloring) ---
# MFCCs summarize the overall "tone colour" of the voice. MFCC1 tracks gross
# spectral balance/brightness (sensitive to source tilt and damping); higher
# coefficients capture finer envelope detail (closer to vocal-tract filter shape).
# They straddle geometry and surface, so they get their own exploratory family.
SPECTRAL_ENVELOPE_MFCC: dict[str, str] = {
    "egemaps_mfcc1V_sma3nz_amean": "MFCC1 (overall spectral balance / brightness)",
    "egemaps_mfcc2V_sma3nz_amean": "MFCC2 (low-vs-mid spectral shape)",
    "egemaps_mfcc3V_sma3nz_amean": "MFCC3 (mid spectral detail)",
    "egemaps_mfcc4V_sma3nz_amean": "MFCC4 (finer envelope detail)",
}

FAMILIES: dict[str, dict[str, str]] = {
    "geometric_vocal_tract": GEOMETRIC_VOCAL_TRACT,
    "source_pitch": SOURCE_PITCH,
    "surface_damping": SURFACE_DAMPING,
    "spectral_envelope_mfcc": SPECTRAL_ENVELOPE_MFCC,
}

# Human-readable family labels used in figures and the report.
FAMILY_LABELS: dict[str, str] = {
    "geometric_vocal_tract": "Geometric (vocal-tract shape)",
    "source_pitch": "Source pitch (fold mass/tension)",
    "surface_damping": "Surface / damping (mucosa & closure)",
    "spectral_envelope_mfcc": "Spectral envelope / timbre (MFCC)",
}


def with_task(base_feature: str, task: str) -> str:
    """Return the task-prefixed daily column name (task in {vowel, prosody})."""
    return f"{task}_{base_feature}"


def base_features() -> list[str]:
    """All base feature names in the taxonomy, de-duplicated, in family order."""
    seen: list[str] = []
    for family in FAMILIES.values():
        for feature in family:
            if feature not in seen:
                seen.append(feature)
    return seen


def family_of(base_feature: str) -> str | None:
    """Return the family key for a base feature, or None if untaxonomized."""
    for family_key, members in FAMILIES.items():
        if base_feature in members:
            return family_key
    return None


def label_of(base_feature: str) -> str:
    """Return the human-readable label for a base feature."""
    for members in FAMILIES.values():
        if base_feature in members:
            return members[base_feature]
    return base_feature
