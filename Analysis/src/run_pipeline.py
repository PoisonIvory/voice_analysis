from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .config import default_paths
from .load_data import load_inito, load_oura_from_parquet, load_voice_features


def _date_window(df: pd.DataFrame) -> str:
    if df.empty or "date" not in df.columns:
        return "n/a to n/a (0 rows)"
    min_date = df["date"].min()
    max_date = df["date"].max()
    return f"{min_date.date() if pd.notna(min_date) else 'n/a'} to {max_date.date() if pd.notna(max_date) else 'n/a'} ({len(df)} rows)"


def _setup_report(voice: pd.DataFrame, oura: pd.DataFrame, inito: pd.DataFrame) -> str:
    overlap_dates = set(voice["date"].dropna()) & set(oura["date"].dropna()) & set(inito["date"].dropna())
    return (
        "Setup validation complete.\n"
        f"- Voice date window: {_date_window(voice)}\n"
        f"- Oura date window: {_date_window(oura)}\n"
        f"- Inito date window: {_date_window(inito)}\n"
        f"- Three-way date overlap: {len(overlap_dates)} days\n"
    )


def run(voice_path: Path, inito_path: Path, oura_path: Path) -> None:
    voice = load_voice_features(voice_path)
    oura = load_oura_from_parquet(oura_path)
    inito = load_inito(inito_path)
    print(_setup_report(voice, oura, inito))


def main() -> None:
    defaults = default_paths()
    parser = argparse.ArgumentParser(description="Run setup validation for voice-cycle analysis.")
    parser.add_argument("--voice-path", type=Path, default=defaults.voice_parquet)
    parser.add_argument("--inito-path", type=Path, default=defaults.inito_csv)
    parser.add_argument(
        "--oura-path",
        type=Path,
        default=defaults.oura_parquet,
        help="Local Oura parquet snapshot path",
    )
    args = parser.parse_args()

    run(args.voice_path, args.inito_path, args.oura_path)


if __name__ == "__main__":
    main()
