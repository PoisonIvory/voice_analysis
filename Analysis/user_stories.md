## Voice-Cycle Analysis User Story

As a researcher tracking my own biometrics, I want to analyze how my voice changes across my menstrual cycle by combining extracted voice features, Oura metrics, and Inito hormone data, so that I can present clear, evidence-based findings to a Northeastern professor on Wednesday.

### Acceptance Criteria

- Load and validate voice, Oura, and Inito datasets.
- Align all sources on calendar date and cycle context.
- Build and consume a one-time source-of-truth cycle calendar in `data/processed/cycle_calendar_daily.parquet`.
- Label each day with binary `phase_label` (`follicular` or `luteal`) using the last-14-days luteal rule.
- Label each day with `cycle_week` (`week_1`, `week_2`, ...) as a second analysis lens.
- Use hormone cycle day as a validation signal for agreement diagnostics.
- Quantify voice-feature differences across phases.
- Quantify voice-feature differences across cycle-week buckets.
- Generate presentation-ready visualizations and a concise findings summary.
