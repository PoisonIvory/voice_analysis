# Voice-Cycle Analysis

Setup workspace for the voice-cycle analysis project. This stage validates source datasets, builds a source-of-truth cycle calendar, and reports cycle coverage diagnostics.

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
3. Run setup validation (local snapshot, no Appwrite dependency):
   - `python -m src.analysis.run_setup_validation`

## Code Organization

- `src/analysis/`: analysis-only paths used in the one-time study run.
- `src/data_collection/`: one-off snapshot refresh tooling.

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

`python -m src.analysis.run_setup_validation --voice-path /path/to/voice.parquet --inito-path /path/to/inito.csv --oura-path data/raw/oura_daily_summaries_20260601.parquet --cycle-calendar-out data/processed/cycle_calendar_daily.parquet`

## Cycle Tracking MVP

The pipeline creates `data/processed/cycle_calendar_daily.parquet` as the single source of truth for cycle-aligned analysis.

MVP cycle starts are anchored to Oura period episodes:

- `2025-12-18`
- `2026-01-14`
- `2026-02-12`
- `2026-03-09`
- `2026-04-11`
- `2026-05-11`

Derived fields:

- `cycle_day` = days since cycle start + 1
- `phase_label`:
  - `luteal` when `days_to_next_start` is `1-14`
  - `follicular` otherwise
- `cycle_week`:
  - days `1-7` = `week_1`
  - days `8-14` = `week_2`
  - days `15-21` = `week_3`
  - days `22-28` = `week_4`
  - days `29-35` = `week_5` (and so on for longer cycles)

When hormone data overlaps, the calendar keeps comparison-only diagnostics:

- `hormone_cycle_day`
- `cycle_day_delta_vs_hormone`

Downstream analysis should use `cycle_day`, `phase_label`, and `cycle_week` from this source-of-truth calendar.

## Refresh Oura Snapshot (Only When Needed)

Use data-collection tooling only when you want a new local snapshot:

`python -m src.data_collection.export_oura_snapshot --snapshot-date 20260601`

Required environment variables for refresh:

- `APPWRITE_API_KEY`
- `APPWRITE_PROJECT_ID`
- `APPWRITE_USER_ID`

Optional environment variables:

- `APPWRITE_ENDPOINT` (default: `https://sfo.cloud.appwrite.io/v1`)
- `APPWRITE_DATABASE_ID` (default: `period_tracker_db`)
- `APPWRITE_OURA_COLLECTION_ID` (default: `oura_daily_summaries`)

## Current Behavior

- Loads and validates voice, Oura, and Inito inputs.
- Applies voice-focused QC filtering and daily aggregation.
- Loads Oura directly from local parquet snapshot.
- Builds `cycle_calendar_daily` as source of truth with:
  - `cycle_day`
  - binary `phase_label` (`follicular`/`luteal`)
  - `cycle_week` buckets (`week_1`, `week_2`, ...)
- Computes hormone agreement diagnostics on overlap dates.
- Prints date windows, overlap counts, phase/week distributions, and agreement summary.
- Writes `data/processed/cycle_calendar_daily.parquet`.
