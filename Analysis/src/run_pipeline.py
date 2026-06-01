from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .align_sources import aggregate_voice_daily, align_daily_data
from .analyze import write_analysis_outputs
from .config import default_paths
from .detect_phases import assign_cycle_phase, cycle_window
from .load_data import load_inito, load_oura, load_voice_features
from .visualize import plot_hormone_voice_heatmap, plot_phase_boxplots, plot_time_series


def _summary_text(df: pd.DataFrame) -> str:
    min_date = df["date"].min()
    max_date = df["date"].max()
    phase_counts = df["cycle_phase"].value_counts(dropna=False).to_dict()
    return (
        "# Presentation Summary\n\n"
        "## Objective\n"
        "Assess whether voice features vary across menstrual cycle phases using voice recordings, Oura metrics, and Inito hormones.\n\n"
        "## Data Window\n"
        f"- Earliest aligned date: {min_date.date() if pd.notna(min_date) else 'n/a'}\n"
        f"- Latest aligned date: {max_date.date() if pd.notna(max_date) else 'n/a'}\n"
        f"- Aligned days: {len(df)}\n\n"
        "## Cycle Phase Coverage\n"
        + "\n".join([f"- {k}: {v} days" for k, v in phase_counts.items()])
        + "\n\n## Deliverables\n"
        "- `outputs/figures/time_series_voice_hormones.png`\n"
        "- `outputs/figures/phase_boxplot.png`\n"
        "- `outputs/figures/hormone_voice_heatmap.png`\n"
        "- `data/processed/phase_summary.csv`\n"
        "- `data/processed/phase_kruskal.csv`\n"
        "- `data/processed/hormone_correlations.csv`\n"
    )


def run(voice_path: Path, oura_path: Path, inito_path: Path, root: Path) -> None:
    voice = load_voice_features(voice_path)
    oura = load_oura(oura_path)
    inito = load_inito(inito_path)

    voice_daily = aggregate_voice_daily(voice)
    aligned = align_daily_data(voice_daily, oura, inito)
    phased = assign_cycle_phase(aligned)
    analysis_df = cycle_window(phased)

    processed_dir = root / "data" / "processed"
    figures_dir = root / "outputs" / "figures"
    processed_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    phased.to_parquet(processed_dir / "aligned_daily.parquet", index=False)
    analysis_df.to_csv(processed_dir / "aligned_daily_cycle_window.csv", index=False)
    write_analysis_outputs(analysis_df, processed_dir)

    plot_time_series(analysis_df, figures_dir / "time_series_voice_hormones.png")
    plot_phase_boxplots(analysis_df, figures_dir / "phase_boxplot.png")
    plot_hormone_voice_heatmap(analysis_df, figures_dir / "hormone_voice_heatmap.png")

    summary = _summary_text(analysis_df)
    (root / "outputs" / "presentation_summary.md").write_text(summary, encoding="utf-8")


def main() -> None:
    defaults = default_paths()
    parser = argparse.ArgumentParser(description="Run voice-cycle analysis pipeline.")
    parser.add_argument("--voice-path", type=Path, default=defaults.voice_parquet)
    parser.add_argument("--oura-path", type=Path, default=defaults.oura_csv)
    parser.add_argument("--inito-path", type=Path, default=defaults.inito_csv)
    parser.add_argument("--root", type=Path, default=defaults.root)
    args = parser.parse_args()

    run(args.voice_path, args.oura_path, args.inito_path, args.root)
    print("Pipeline complete.")


if __name__ == "__main__":
    main()
