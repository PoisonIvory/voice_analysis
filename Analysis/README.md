# Voice-Cycle Analysis

Setup workspace for the voice-cycle analysis project. This stage validates source datasets and date overlap only.

## Current Readiness

- Status: proceed to analysis using the local Oura snapshot.
- Snapshot audit date: `2026-06-01`
- Verified snapshot metrics:
  - `304` rows
  - `126` columns
  - Date range: `2025-12-18` to `2026-06-01`
  - Non-null `temperatureDeviation`: `283` rows
- Snapshot files:
  - `data/raw/oura_daily_summaries_20260601.parquet` (immutable)
  - `data/raw/oura_daily_summaries.parquet` (latest convenience copy)
  - `data/raw/oura_daily_summaries_20260601.metadata.json` (provenance)
  - `data/raw/oura_daily_summaries_appwrite_result_20260601_full.json` (raw traceability payload)

## Quickstart

1. Create/activate a Python environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Run pipeline (local snapshot, no Appwrite dependency):
   - `python -m src.run_pipeline`

## Data Requirements

This setup pipeline expects three data sources.

### 1) Voice data (required)

- Source: local parquet file
- Default path: `/Users/ivyhamilton/Decibelle/SpeechFeatureExtraction/data/processed/voice_features_v3_recordings.parquet`
- Required columns:
  - `recordedDate`
  - `taskType`
  - `qc_opensmile_egemaps_success`
- Expected feature shape:
  - Voice feature columns are `egemaps_` prefixed (88 eGeMAPS features in the extraction output)

### 2) Hormone data (required)

- Source: local CSV export
- Default path: `/Users/ivyhamilton/Downloads/Hormone Tracking - hormones_data.csv`
- Required columns:
  - `Date`
  - `Cycle Day`
- Parsed hormone fields:
  - `E3G`, `PdG`, `FSH`, `LH` (when present)

### 3) Oura data (required)

- Source: local parquet snapshot
- Required date field:
  - `day` or `date`
- Pipeline keeps normalized Oura fields when available:
  - `temperatureDeviation`, `temperatureTrendDeviation`, `averageHrv`, `restingHeartRate`, `sleepScore`, `readinessScore`, `activityScore`, `tags`

## Data Gaps and Missing Days

Not every source has data for every calendar day. This is expected.

- Voice can be missing on non-recording days.
- Oura can be missing for sync/device gaps.
- Hormone values can be intermittent (not measured daily).

Recommended handling strategy:

- Use date as the primary join key and keep source-specific missing values as null (do not backfill by default).
- Prefer pairwise complete data per analysis question (for example, voice-hormone correlations only on days where both are present).
- Apply interpolation only for visualization trends, never for primary statistics unless explicitly documented.
- Report coverage before analysis (days per source, overlap days, and per-feature sample size `n`).
- Treat sparse phase windows as exploratory and annotate low-sample results clearly.

## Voice Data Cleaning Rules

Voice data is cleaned before any cross-source alignment:

- Keep only rows where `qc_opensmile_egemaps_success` is true.
- Drop unreadable or clipped recordings when QC columns are present.
- Keep recordings with duration in `[1, 120]` seconds.
- Remove rows where `egemaps_F0semitoneFrom27.5Hz_sma3nz_amean == 0` for `taskType` in `{vowel, prosody}`.
- Aggregate multiple recordings from the same day to one daily row using median values for voice features.
- Track per-day recording volume using `voice_recording_count` and `voice_task_count`.

## Default Inputs

- Voice parquet: `/Users/ivyhamilton/Decibelle/SpeechFeatureExtraction/data/processed/voice_features_v3_recordings.parquet`
- Oura local snapshot: `data/raw/oura_daily_summaries_20260601.parquet`
- Inito CSV: `/Users/ivyhamilton/Downloads/Hormone Tracking - hormones_data.csv`

Optional overrides:

`python -m src.run_pipeline --voice-path /path/to/voice.parquet --inito-path /path/to/inito.csv --oura-path data/raw/oura_daily_summaries_20260601.parquet`

## Current Behavior

- Loads and validates voice, Oura, and Inito inputs.
- Applies voice-focused QC filtering and daily aggregation.
- Loads Oura directly from local parquet snapshot.
- Prints date windows for each source.
- Prints the three-way date overlap count.
- Does not generate analysis outputs yet.
