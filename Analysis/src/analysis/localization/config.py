"""Paths, output dirs, and the mechanism feature sets for driver localization.

Feature sets express the two dissociation axes:

1. Source-vs-filter:  MOVED (cover + timbre)  vs  SPARED (vocal-tract geometry).
2. Peripheral-vs-central:  PERIPHERAL cover quality (tissue) vs CENTRAL pitch /
   timing control (auditory-motor regulation, the allopregnanolone pathway).

Base names omit the task prefix; resolve with `feature_taxonomy.with_task`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..config import default_paths

# --- Vocal-tract geometry: the SPARED channel (built-in informative null) ---
GEOMETRY: dict[str, str] = {
    "egemaps_F1frequency_sma3nz_amean": "F1 (mouth openness)",
    "egemaps_F2frequency_sma3nz_amean": "F2 (tongue front-back)",
    "egemaps_F3frequency_sma3nz_amean": "F3 (fine tract shape)",
}

# --- Vocal-tract damping: a secondary geometry-side family ---
GEOMETRY_DAMPING: dict[str, str] = {
    "egemaps_F1bandwidth_sma3nz_amean": "F1 bandwidth (resonance damping)",
    "egemaps_F2bandwidth_sma3nz_amean": "F2 bandwidth (resonance damping)",
    "egemaps_F3bandwidth_sma3nz_amean": "F3 bandwidth (resonance damping)",
}

# --- Source pitch level: fold mass/tension ---
SOURCE_PITCH: dict[str, str] = {
    "egemaps_F0semitoneFrom27.5Hz_sma3nz_amean": "Pitch (F0 mean)",
    "egemaps_F0semitoneFrom27.5Hz_sma3nz_percentile50.0": "Pitch (F0 median)",
}

# --- Peripheral cover quality: the MOVED tissue channel ---
PERIPHERAL_COVER: dict[str, str] = {
    "egemaps_HNRdBACF_sma3nz_amean": "Clarity (HNR)",
    "egemaps_jitterLocal_sma3nz_amean": "Jitter",
    "egemaps_shimmerLocaldB_sma3nz_amean": "Shimmer",
    "egemaps_alphaRatioV_sma3nz_amean": "Alpha ratio (spectral tilt)",
    "egemaps_hammarbergIndexV_sma3nz_amean": "Hammarberg index (spectral tilt)",
    "egemaps_slopeV0-500_sma3nz_amean": "Spectral slope 0-500 Hz",
    "egemaps_slopeV500-1500_sma3nz_amean": "Spectral slope 500-1500 Hz",
    "egemaps_logRelF0-H1-H2_sma3nz_amean": "Open quotient (H1-H2)",
    "egemaps_logRelF0-H1-A3_sma3nz_amean": "Source tilt (H1-A3)",
}

# --- Timbre / tone colour: spectral envelope (mostly peripheral coloring) ---
TIMBRE: dict[str, str] = {
    "egemaps_mfcc1V_sma3nz_amean": "Timbre MFCC1 (brightness)",
    "egemaps_mfcc2V_sma3nz_amean": "Timbre MFCC2 (low-vs-mid colour)",
    "egemaps_mfcc3V_sma3nz_amean": "Timbre MFCC3",
    "egemaps_mfcc4V_sma3nz_amean": "Timbre MFCC4",
}

# --- Central pitch / timing control: auditory-motor regulation ---
CENTRAL_CONTROL: dict[str, str] = {
    "egemaps_F0semitoneFrom27.5Hz_sma3nz_stddevNorm": "Pitch variability (F0 SD)",
    "egemaps_F0semitoneFrom27.5Hz_sma3nz_pctlrange0-2": "Pitch range",
    "egemaps_F0semitoneFrom27.5Hz_sma3nz_meanRisingSlope": "Pitch rising slope",
    "egemaps_F0semitoneFrom27.5Hz_sma3nz_meanFallingSlope": "Pitch falling slope",
    "egemaps_F0semitoneFrom27.5Hz_sma3nz_stddevRisingSlope": "Pitch rising-slope SD",
    "egemaps_F0semitoneFrom27.5Hz_sma3nz_stddevFallingSlope": "Pitch falling-slope SD",
    "egemaps_VoicedSegmentsPerSec": "Speaking-rate proxy",
    "egemaps_MeanVoicedSegmentLengthSec": "Mean voiced-segment length",
    "egemaps_StddevVoicedSegmentLengthSec": "Voiced-segment length SD",
}

# Families used on the localization map (label -> members), in display order.
FAMILIES: dict[str, dict[str, str]] = {
    "peripheral_cover": PERIPHERAL_COVER,
    "timbre": TIMBRE,
    "source_pitch": SOURCE_PITCH,
    "central_control": CENTRAL_CONTROL,
    "geometry_damping": GEOMETRY_DAMPING,
    "geometry": GEOMETRY,
}

FAMILY_LABELS: dict[str, str] = {
    "peripheral_cover": "Cover quality (mucosa/closure)",
    "timbre": "Timbre (tone colour)",
    "source_pitch": "Pitch level",
    "central_control": "Pitch/timing control",
    "geometry_damping": "Resonance damping",
    "geometry": "Vocal-tract geometry (SPARED)",
}

# The two channels of the headline source-vs-filter dissociation.
MOVED_CHANNEL = {**PERIPHERAL_COVER, **TIMBRE}
SPARED_CHANNEL = dict(GEOMETRY)

# A-priori mechanism-privileged moved set (the luteal cover/timbre signal the
# prior confirmatory studies flagged), used for a focused dissociation test so
# the contrast is not diluted by noisier perturbation features.
FOCUSED_MOVED = {
    "egemaps_logRelF0-H1-H2_sma3nz_amean": "Open quotient (H1-H2)",
    "egemaps_HNRdBACF_sma3nz_amean": "Clarity (HNR)",
    "egemaps_hammarbergIndexV_sma3nz_amean": "Hammarberg (spectral tilt)",
    "egemaps_logRelF0-H1-A3_sma3nz_amean": "Source tilt (H1-A3)",
    "egemaps_mfcc2V_sma3nz_amean": "Timbre (MFCC2)",
}

# Peripheral vs central split for the second dissociation axis (Thread 2).
PERIPHERAL_SET = {**PERIPHERAL_COVER, **TIMBRE}
CENTRAL_SET = dict(CENTRAL_CONTROL)

# Cycles with enough days in BOTH phases to anchor a within-cycle contrast.
BALANCED_CYCLE_STARTS = ("2026-01-14", "2026-02-12")

# Hormone-specific directional predictions (for the write-up + checks).
# sign: +1 means feature is predicted to rise with the named hormone/state.
HORMONE_PREDICTIONS = {
    "egemaps_HNRdBACF_sma3nz_amean": ("E3G", +1, "thin watery mucus -> cleaner closure near ovulation"),
    "egemaps_logRelF0-H1-H2_sma3nz_amean": ("PdG", +1, "luteal edema/dehydration -> more open quotient"),
    "egemaps_mfcc2V_sma3nz_amean": ("PdG", +1, "luteal tissue/mucus -> timbre shift"),
}

PRIMARY_TASK = "prosody"  # connected speech: richest, where pitch control lives
SECONDARY_TASK = "vowel"  # sustained phonation: cleanest source window


@dataclass(frozen=True)
class LocalizationPaths:
    analysis_table: Path
    hubert_phase_contrasts: Path
    tables_dir: Path
    figures_dir: Path


def localization_paths() -> LocalizationPaths:
    base = default_paths()
    out = base.outputs_dir / "localization"
    return LocalizationPaths(
        analysis_table=base.processed_dir / "analysis_daily.parquet",
        hubert_phase_contrasts=base.outputs_dir / "hubert" / "tables" / "phase_contrasts.csv",
        tables_dir=out / "tables",
        figures_dir=out / "figures",
    )
