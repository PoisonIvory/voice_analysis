# Voice-Cycle Analysis

Setup workspace for the voice-cycle analysis project. This stage validates source datasets and date overlap only.

## Quickstart

1. Create/activate a Python environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Run pipeline:
   - `python -m src.run_pipeline`

## Default Inputs

- Voice parquet: `/Users/ivyhamilton/Decibelle/SpeechFeatureExtraction/data/processed/voice_features_v3_recordings.parquet`
- Oura parquet: `data/raw/oura_daily_summaries.parquet`
- Inito CSV: `/Users/ivyhamilton/Downloads/Hormone Tracking - hormones_data.csv`

Override any path:

`python -m src.run_pipeline --voice-path /path/to/voice.parquet --oura-path /path/to/oura.parquet --inito-path /path/to/inito.csv`

## Current Behavior

- Loads and validates voice, Oura, and Inito inputs.
- Prints date windows for each source.
- Prints the three-way date overlap count.
- Does not generate analysis outputs yet.
