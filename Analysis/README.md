# Voice-Cycle Analysis

Setup workspace for the voice-cycle analysis project. This stage validates source datasets and date overlap only.

## Quickstart

1. Create/activate a Python environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Run pipeline:
   - `APPWRITE_API_KEY=xxx python -m src.run_pipeline`

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

- Source: Appwrite API (`oura_daily_summaries` collection)
- Auth:
  - `APPWRITE_API_KEY` is required
- Required Appwrite document date field:
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

## Default Inputs

- Voice parquet: `/Users/ivyhamilton/Decibelle/SpeechFeatureExtraction/data/processed/voice_features_v3_recordings.parquet`
- Oura: pulled from Appwrite `oura_daily_summaries` API collection
- Inito CSV: `/Users/ivyhamilton/Downloads/Hormone Tracking - hormones_data.csv`

Optional overrides:

`APPWRITE_API_KEY=xxx python -m src.run_pipeline --voice-path /path/to/voice.parquet --inito-path /path/to/inito.csv --oura-cache-path data/raw/oura_daily_summaries.parquet`

## Appwrite Environment Variables

- `APPWRITE_API_KEY` (required)
- `APPWRITE_USER_ID` (optional, default: `6928d5ab0018cac7ae42`)
- `APPWRITE_ENDPOINT` (optional, default: `https://sfo.cloud.appwrite.io/v1`)
- `APPWRITE_PROJECT_ID` (optional, default: `68ca57d1000cb6324eca`)
- `APPWRITE_DATABASE_ID` (optional, default: `period_tracker_db`)
- `APPWRITE_OURA_COLLECTION_ID` (optional, default: `oura_daily_summaries`)

## Current Behavior

- Loads and validates voice, Oura, and Inito inputs.
- Pulls Oura directly from Appwrite API.
- Optionally caches pulled Oura data to `data/raw/oura_daily_summaries.parquet`.
- Prints date windows for each source.
- Prints the three-way date overlap count.
- Does not generate analysis outputs yet.
