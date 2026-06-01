"""CLI tool to export an Oura Appwrite snapshot into local raw artifacts."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd

from .appwrite_oura import AppwriteOuraConfig, fetch_all_oura_documents


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} is required")
    return value


def _date_suffix(value: str | None) -> str:
    if value:
        return value
    return datetime.now().strftime("%Y%m%d")


def export_snapshot(output_dir: Path, snapshot_date: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    config = AppwriteOuraConfig(
        endpoint=os.getenv("APPWRITE_ENDPOINT", "https://sfo.cloud.appwrite.io/v1"),
        project_id=_require_env("APPWRITE_PROJECT_ID"),
        database_id=os.getenv("APPWRITE_DATABASE_ID", "period_tracker_db"),
        collection_id=os.getenv("APPWRITE_OURA_COLLECTION_ID", "oura_daily_summaries"),
        user_id=_require_env("APPWRITE_USER_ID"),
        api_key=_require_env("APPWRITE_API_KEY"),
    )

    documents = fetch_all_oura_documents(config)
    if not documents:
        raise ValueError("No Oura records returned from Appwrite")

    df = pd.DataFrame.from_records(documents)

    snapshot_file = output_dir / f"oura_daily_summaries_{snapshot_date}.parquet"
    latest_file = output_dir / "oura_daily_summaries.parquet"
    payload_file = output_dir / f"oura_daily_summaries_appwrite_result_{snapshot_date}_full.json"
    metadata_file = output_dir / f"oura_daily_summaries_{snapshot_date}.metadata.json"

    df.to_parquet(snapshot_file, index=False)
    df.to_parquet(latest_file, index=False)
    payload_file.write_text(json.dumps(documents, indent=2), encoding="utf-8")

    day_col = "day" if "day" in df.columns else "date" if "date" in df.columns else None
    day_min = None
    day_max = None
    if day_col is not None:
        series = pd.to_datetime(df[day_col], format="mixed", errors="coerce").dropna()
        if not series.empty:
            day_min = series.min().date().isoformat()
            day_max = series.max().date().isoformat()

    metadata = {
        "source": "appwrite_api",
        "table": config.collection_id,
        "exported_at_local": datetime.now().isoformat(),
        "row_count": int(len(df)),
        "columns_count": int(len(df.columns)),
        "day_min": day_min,
        "day_max": day_max,
        "snapshot_file": str(snapshot_file),
        "latest_file": str(latest_file),
        "source_payload_file": str(payload_file),
    }
    metadata_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print("Oura snapshot export complete.")
    print(f"- Rows: {len(df)}")
    print(f"- Columns: {len(df.columns)}")
    print(f"- Snapshot: {snapshot_file}")
    print(f"- Latest: {latest_file}")
    print(f"- Metadata: {metadata_file}")
    print(f"- Payload: {payload_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Oura snapshot from Appwrite to local parquet.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "data" / "raw",
        help="Destination directory for snapshot artifacts",
    )
    parser.add_argument(
        "--snapshot-date",
        type=str,
        default=None,
        help="Snapshot suffix in YYYYMMDD format (defaults to current date)",
    )
    args = parser.parse_args()

    export_snapshot(args.output_dir, _date_suffix(args.snapshot_date))


if __name__ == "__main__":
    main()
