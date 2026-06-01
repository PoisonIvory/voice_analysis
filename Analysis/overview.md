# Analysis Project Handoff

This document describes the input data and context the new analysis project will need to consume from SpeechFeatureExtraction.

## Scientific Question

> Does voice change along the menstrual cycle?

The analysis project will explore relationships between speech acoustic features and cycle phase/day using data from the Decibelle app.

## Input Files

The extraction pipeline produces two parquet files:

| File | Purpose |
|------|---------|
| `voice_features_v3_recordings.parquet` | One row per successfully extracted recording with metadata and features |
| `voice_features_v3_audit.parquet` | Full manifest including skipped/failed rows for transparency |

Oura data is available as a local immutable snapshot for reproducible analysis:

| File | Purpose |
|------|---------|
| `data/raw/oura_daily_summaries_20260601.parquet` | Pinned one-time snapshot exported from Appwrite MCP |
| `data/raw/oura_daily_summaries.parquet` | Latest convenience copy mirroring the pinned snapshot |
| `data/raw/oura_daily_summaries_20260601.metadata.json` | Snapshot provenance and validation metadata |
| `data/raw/oura_daily_summaries_appwrite_result_20260601_full.json` | Raw MCP payload for traceability |

Snapshot validation (`2026-06-01`):

- Row count: `165`
- Unique days: `165`
- Columns: `126`
- Date range: `2025-12-18` to `2026-06-01`
- Non-null `temperatureDeviation`: `151`

Cycle context is now prepared as a processed source-of-truth table:

| File | Purpose |
|------|---------|
| `data/processed/cycle_calendar_daily.parquet` | One row per day with canonical `cycle_day`, binary `phase_label`, and `cycle_week` buckets |

MVP cycle anchors used to generate `cycle_calendar_daily.parquet`:

- `2025-12-18`
- `2026-01-14`
- `2026-02-12`
- `2026-03-09`
- `2026-04-11`
- `2026-05-11`

MVP cycle rules:

- `phase_label = luteal` for the last 14 days before the next cycle start
- `phase_label = follicular` otherwise
- `cycle_week` is binned by 7-day windows (`week_1`, `week_2`, ...)
- Hormone `cycle_day` is used as validation, not as source-of-truth override

## Recordings Parquet Schema

### Identification and Metadata

| Column | Type | Description |
|--------|------|-------------|
| `recordingId` | string | Unique identifier (same as Appwrite storage file ID) |
| `storageFileId` | string | Appwrite storage file ID |
| `voiceRecordingId` | string | Appwrite voice_recordings document ID (may be null) |
| `userId` | string | User identifier |
| `taskType` | string | Recording task: `vowel` or `prosody` |
| `recordedAt` | string (ISO8601) | Recording timestamp |
| `recordedDate` | string (YYYY-MM-DD) | Recording date (for daily aggregation) |
| `bucketId` | string | Appwrite storage bucket (always `audio`) |
| `filename` | string | Original filename |

### Lineage and Reproducibility

| Column | Type | Description |
|--------|------|-------------|
| `extractorVersion` | string | Pipeline version (e.g., `v3.1-opensmile-egemaps`) |
| `extractionTimestamp` | string (ISO8601) | When extraction ran |
| `audioHash` | string | SHA256 of the processed WAV file |
| `featureSet` | string | `opensmile.FeatureSet.eGeMAPSv02` |
| `featureLevel` | string | `opensmile.FeatureLevel.Functionals` |
| `libraryName` | string | `opensmile` |
| `libraryVersion` | string | opensmile package version |
| `opensmileConfigName` | string | Config name from opensmile |
| `opensmileConfigFile` | string | Config filename |
| `opensmileSamplingRateHz` | int | 16000 |
| `opensmileResampleEnabled` | bool | True |
| `opensmileChannels` | int | 0 (first channel) |
| `opensmileMixdownEnabled` | bool | False |

### Quality Control Fields

| Column | Type | Description |
|--------|------|-------------|
| `qc_audio_readable` | bool | WAV file successfully read |
| `qc_sample_rate_hz` | int | Original sample rate |
| `qc_channel_count` | int | Number of audio channels |
| `qc_sample_width_bytes` | int | Bytes per sample |
| `qc_duration_sec` | float | Recording duration in seconds |
| `qc_clipping_detected` | bool | Audio clipping detected |
| `qc_warning_codes` | list[string] | Warning flags (see below) |
| `qc_opensmile_egemaps_success` | bool | Feature extraction succeeded |
| `qc_feature_count_egemaps` | int | Features extracted (should be 88) |
| `qc_feature_count_egemaps_expected` | int | Expected feature count (88) |

### QC Warning Codes

| Code | Meaning |
|------|---------|
| `metadata_missing` | No voice_recordings document found |
| `required_metadata_missing` | Missing userId or recordedAt |
| `task_unknown` | Could not determine task type |
| `task_disagreement` | Filename and metadata task types differ |
| `out_of_scope_task` | Task is not vowel or prosody |
| `clipping` | Audio clipping detected |
| `short_duration` | Recording under 1 second |
| `non_mono_audio` | Multi-channel audio |
| `audio_unreadable` | WAV file could not be read |

### Pipeline Status

| Column | Type | Description |
|--------|------|-------------|
| `pipelineStatus` | string | `completed` for recordings parquet |
| `metadataPresent` | bool | voice_recordings document exists |
| `metadataComplete` | bool | All required metadata present |
| `inScope` | bool | Task is vowel or prosody |

### eGeMAPSv02 Features (88 columns)

All feature columns are prefixed with `egemaps_`. These are functional-level statistics computed over the entire recording.

#### Frequency Features
- `egemaps_F0semitoneFrom27.5Hz_sma3nz_amean` - Mean fundamental frequency (semitones)
- `egemaps_F0semitoneFrom27.5Hz_sma3nz_stddevNorm` - F0 standard deviation
- `egemaps_F0semitoneFrom27.5Hz_sma3nz_percentile20.0` - F0 20th percentile
- `egemaps_F0semitoneFrom27.5Hz_sma3nz_percentile50.0` - F0 median
- `egemaps_F0semitoneFrom27.5Hz_sma3nz_percentile80.0` - F0 80th percentile
- `egemaps_F0semitoneFrom27.5Hz_sma3nz_pctlrange0-2` - F0 range (20th-80th percentile)
- `egemaps_F0semitoneFrom27.5Hz_sma3nz_meanRisingSlope` - Mean rising F0 slope
- `egemaps_F0semitoneFrom27.5Hz_sma3nz_stddevRisingSlope` - Rising slope std dev
- `egemaps_F0semitoneFrom27.5Hz_sma3nz_meanFallingSlope` - Mean falling F0 slope
- `egemaps_F0semitoneFrom27.5Hz_sma3nz_stddevFallingSlope` - Falling slope std dev

#### Formant Features (F1, F2, F3)
- `egemaps_F1frequency_sma3nz_amean` - Mean first formant frequency
- `egemaps_F1frequency_sma3nz_stddevNorm` - F1 normalized std dev
- `egemaps_F1bandwidth_sma3nz_amean` - Mean F1 bandwidth
- `egemaps_F1bandwidth_sma3nz_stddevNorm` - F1 bandwidth std dev
- (Similar columns for F2 and F3)

#### Energy/Amplitude Features
- `egemaps_loudness_sma3_amean` - Mean loudness
- `egemaps_loudness_sma3_stddevNorm` - Loudness std dev
- `egemaps_loudness_sma3_percentile20.0` - Loudness 20th percentile
- `egemaps_loudness_sma3_percentile50.0` - Loudness median
- `egemaps_loudness_sma3_percentile80.0` - Loudness 80th percentile
- `egemaps_loudness_sma3_pctlrange0-2` - Loudness range
- `egemaps_loudness_sma3_meanRisingSlope` - Rising loudness slope
- `egemaps_loudness_sma3_meanFallingSlope` - Falling loudness slope

#### Spectral Features
- `egemaps_spectralFlux_sma3_amean` - Mean spectral flux
- `egemaps_spectralFlux_sma3_stddevNorm` - Spectral flux std dev
- `egemaps_alphaRatioV_sma3nz_amean` - Alpha ratio (voiced)
- `egemaps_hammarbergIndexV_sma3nz_amean` - Hammarberg index (voiced)
- `egemaps_slopeV0-500_sma3nz_amean` - Spectral slope 0-500Hz
- `egemaps_slopeV500-1500_sma3nz_amean` - Spectral slope 500-1500Hz

#### Voice Quality Features
- `egemaps_jitterLocal_sma3nz_amean` - Mean jitter (pitch perturbation)
- `egemaps_jitterLocal_sma3nz_stddevNorm` - Jitter std dev
- `egemaps_shimmerLocaldB_sma3nz_amean` - Mean shimmer (amplitude perturbation)
- `egemaps_shimmerLocaldB_sma3nz_stddevNorm` - Shimmer std dev
- `egemaps_HNRdBACF_sma3nz_amean` - Harmonics-to-noise ratio
- `egemaps_HNRdBACF_sma3nz_stddevNorm` - HNR std dev

#### Temporal Features
- `egemaps_equivalentSoundLevel_dBp` - Equivalent sound level
- `egemaps_MeanVoicedSegmentLengthSec` - Mean voiced segment duration
- `egemaps_StddevVoicedSegmentLengthSec` - Voiced segment std dev
- `egemaps_MeanUnvoicedSegmentLength` - Mean unvoiced segment duration
- `egemaps_StddevUnvoicedSegmentLength` - Unvoiced segment std dev
- `egemaps_VoicedSegmentsPerSec` - Speaking rate proxy

## Audit Parquet Schema

Same columns as recordings parquet plus:

| Column | Type | Description |
|--------|------|-------------|
| `pipelineStatus` | string | `pending`, `completed`, `skipped`, or `failed` |
| `skipReason` | string | `out_of_scope_task`, `metadata_error`, or null |
| `qc_failure_stage` | string | Pipeline stage where failure occurred |
| `qc_failure_reason` | string | Error message |

## Task Types

| Task | Description | Analysis Use |
|------|-------------|--------------|
| `vowel` | Sustained vowel phonation | Voice quality, F0, formants |
| `prosody` | Read or spontaneous speech | Intonation, rhythm, speaking rate |

## Suggested Analysis Approaches

### 1. Data Preparation
- Load recordings parquet with pandas/polars
- Generate cycle calendar once: `python -m src.data_collection.export_cycle_calendar --oura-path data/raw/oura_daily_summaries_20260601.parquet --output-path data/processed/cycle_calendar_daily.parquet`
- Load cycle context from `data/processed/cycle_calendar_daily.parquet`
- Filter to single user if needed
- Join voice + Oura + hormones to canonical cycle fields by date
- Use two analysis lenses: binary phase (`follicular`/`luteal`) and `cycle_week`

### 2. Feature Selection
- Start with interpretable features: F0, jitter, shimmer, HNR
- Consider task-specific analyses (vowel vs prosody)
- Use QC flags to filter questionable recordings

### 3. Analysis Dimensions
- **Within-cycle**: Compare features across cycle phases
- **Within-day**: If multiple recordings per day
- **Longitudinal**: Track changes over multiple cycles
- **Task comparison**: vowel vs prosody patterns

### 4. Statistical Considerations
- Repeated measures (multiple recordings per person per day)
- Missing data patterns (not all days have recordings)
- Multiple comparisons (88 features)
- Effect sizes vs statistical significance

### 5. Visualization Ideas
- Time series of key features across cycle
- Feature distributions by cycle phase
- Correlation heatmaps within feature groups
- Individual vs group-level patterns

## Dependencies for Analysis Project

```
pandas>=2.0
polars  # optional, for faster parquet reads
pyarrow  # parquet support
matplotlib
seaborn
scipy  # statistical tests
statsmodels  # mixed effects models
scikit-learn  # dimensionality reduction, clustering
```

## File Locations

The extraction pipeline writes to:
```
data/processed/voice_features_v3_recordings.parquet
data/processed/voice_features_v3_audit.parquet
```

The analysis project should read these files (copy or reference by path).

## Open Questions for Next Iteration

1. Should cycle anchors continue to be fixed manual dates, or be auto-extracted from Oura tags each refresh?
2. Should `phase_label` remain binary in analysis outputs, or should we add ovulatory windows in a follow-up iteration?
3. What is the expected sample size per phase and per cycle-week bucket after filtering to voice-available dates?
4. Should analysis be user-specific only, or is group-level aggregation planned later?
5. What is considered a meaningful effect size for voice features?
