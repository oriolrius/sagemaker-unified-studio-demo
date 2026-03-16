#!/usr/bin/env python3
"""
Clean raw machine temperature data.

Loads CSV from S3, removes missing values, converts timestamps,
and saves as Parquet for efficient downstream processing.

Usage:
    python clean_data.py --input-path s3://bucket/data/raw/machines.csv \
                         --output-path s3://bucket/data/processed/clean_machines.parquet
"""

import argparse
import sys
import time
import traceback

import pandas as pd

from utils import get_bucket_name, log_json, validate_columns

SCRIPT_NAME = "clean_data.py"
REQUIRED_COLUMNS = ["machine_id", "timestamp", "temperature", "room_temp"]


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Clean raw machine temperature data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # With explicit paths
    python clean_data.py --input-path s3://bucket/raw/machines.csv \\
                         --output-path s3://bucket/processed/clean.parquet

    # Using default bucket from environment
    python clean_data.py
        """,
    )
    parser.add_argument(
        "--input-path",
        type=str,
        help="S3 URI for input CSV file (default: s3://{BUCKET_NAME}/data/raw/machines.csv)",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        help="S3 URI for output Parquet file (default: s3://{BUCKET_NAME}/data/processed/clean_machines.parquet)",
    )
    return parser.parse_args()


def main() -> int:
    """
    Main entry point for data cleaning.

    Returns:
        0 on success, 1 on failure
    """
    start_time = time.time()
    args = parse_args()

    try:
        # Resolve S3 paths
        bucket_name = get_bucket_name()
        input_path = args.input_path or f"s3://{bucket_name}/data/raw/machines.csv"
        output_path = (
            args.output_path
            or f"s3://{bucket_name}/data/processed/clean_machines.parquet"
        )

        log_json(
            "INFO",
            "Starting data cleaning",
            script_name=SCRIPT_NAME,
            step="init",
            input_path=input_path,
            output_path=output_path,
        )

        # Load raw data
        log_json("INFO", "Loading raw data", script_name=SCRIPT_NAME, step="load")
        df = pd.read_csv(input_path)
        input_rows = len(df)

        log_json(
            "INFO",
            f"Loaded {input_rows:,} rows",
            script_name=SCRIPT_NAME,
            step="load",
            input_rows=input_rows,
        )

        # Validate required columns
        validate_columns(df, REQUIRED_COLUMNS, context=input_path)

        # Remove rows with missing temperature values
        log_json(
            "INFO", "Removing missing values", script_name=SCRIPT_NAME, step="clean"
        )
        df_clean = df.dropna(subset=["temperature", "room_temp"])
        removed_rows = input_rows - len(df_clean)

        log_json(
            "INFO",
            f"Removed {removed_rows:,} rows with missing values",
            script_name=SCRIPT_NAME,
            step="clean",
            removed_rows=removed_rows,
        )

        # Convert timestamp to datetime
        log_json(
            "INFO", "Converting timestamps", script_name=SCRIPT_NAME, step="transform"
        )
        df_clean["timestamp"] = pd.to_datetime(df_clean["timestamp"])

        # Sort by timestamp
        df_clean = df_clean.sort_values("timestamp").reset_index(drop=True)
        output_rows = len(df_clean)

        # Save to Parquet (overwrites if exists)
        log_json(
            "INFO",
            "Saving cleaned data",
            script_name=SCRIPT_NAME,
            step="save",
            output_path=output_path,
        )
        df_clean.to_parquet(output_path, index=False)

        duration_ms = (time.time() - start_time) * 1000
        log_json(
            "INFO",
            "Data cleaning complete",
            script_name=SCRIPT_NAME,
            step="complete",
            duration_ms=duration_ms,
            input_rows=input_rows,
            removed_rows=removed_rows,
            output_rows=output_rows,
        )

        return 0

    except FileNotFoundError as e:
        log_json(
            "ERROR",
            f"Input file not found: {e}",
            script_name=SCRIPT_NAME,
            step="error",
            error_type="FileNotFoundError",
        )
        return 1

    except ValueError as e:
        log_json(
            "ERROR",
            str(e),
            script_name=SCRIPT_NAME,
            step="error",
            error_type="ValueError",
        )
        return 1

    except Exception as e:
        log_json(
            "ERROR",
            f"Unexpected error: {e}",
            script_name=SCRIPT_NAME,
            step="error",
            error_type=type(e).__name__,
            traceback=traceback.format_exc(),
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
