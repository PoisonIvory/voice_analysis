# Voice-Cycle Analysis

Analysis pipeline for triangulating voice features, Oura biometrics, and Inito hormones to study cycle-linked voice changes.

## Quickstart

1. Create/activate a Python environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Run pipeline:
   - `python -m src.run_pipeline`

## Default Inputs

- Voice parquet: `/Users/ivyhamilton/Decibelle/SpeechFeatureExtraction/data/processed/voice_features_v3_recordings.parquet`
- Oura CSV: `/Users/ivyhamilton/Decibelle/PeriodTracker/oura_full_2026-01-17.csv`
- Inito CSV: `/Users/ivyhamilton/Downloads/Hormone Tracking - hormones_data.csv`

Override any path:

`python -m src.run_pipeline --voice-path /path/to/voice.parquet --oura-path /path/to/oura.csv --inito-path /path/to/inito.csv`

## Outputs

- `data/processed/aligned_daily.parquet`
- `data/processed/aligned_daily_cycle_window.csv`
- `data/processed/phase_summary.csv`
- `data/processed/phase_kruskal.csv`
- `data/processed/hormone_correlations.csv`
- `outputs/figures/*.png`
- `outputs/presentation_summary.md`
