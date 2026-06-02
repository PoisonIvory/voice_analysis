# Voice Handoff Validation Report (Phase 1)

## Scope

- Validation scope is limited to file readability, one-user scope, and one-row-per-day contract.
- No aggregation-rule validation is performed in this phase.

## Inputs

- Canonical voice daily input: `/Users/ivyhamilton/Decibelle/SpeechFeatureExtraction/data/processed/voice_features_v4_daily.parquet`
- Supporting voice audit file: `/Users/ivyhamilton/Decibelle/SpeechFeatureExtraction/data/processed/voice_features_v4_audit.parquet`
- Supporting staging file (reference only): `/Users/ivyhamilton/Decibelle/SpeechFeatureExtraction/data/processed/voice_features_v4_recordings_staging.parquet`

## Results

- Rows: `59`
- Unique users: `1`
- User ID: `6928d5ab0018cac7ae42`
- Date range: `2025-09-25 to 2026-05-11`
- One-row-per-day contract: `pass` (`0` duplicate rows)
- Unique (userId, day) rows: `59`
- Complete days (`has_vowel && has_prosody`): `55`
- Vowel-only days: `3`
- Prosody-only days: `1`

## Diagnostics Columns Present

- `voice_recording_count`: `False`
- `voice_task_count`: `False`
- `voice_duration_sec_median`: `False`
- `vowel_recording_count`: `True`
- `prosody_recording_count`: `True`
