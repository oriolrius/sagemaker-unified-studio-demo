#!/usr/bin/env python3
"""
Create ML features from cleaned machine temperature data.

Loads cleaned Parquet data, creates engineered features (temp_diff, overheat),
and saves the feature dataset for model training.

Usage:
    python feature_engineering.py --input-path s3://bucket/data/processed/clean_machines.parquet \
                                  --output-path s3://bucket/data/features/features.parquet
"""

import argparse
import sys
import time
import traceback

import pandas as pd

from utils import get_bucket_name, log_json, validate_columns

SCRIPT_NAME = "feature_engineering.py"
REQUIRED_COLUMNS = ["temperature", "room_temp"]
OVERHEAT_THRESHOLD = 80.0  # Temperature above which machine is overheating


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Create ML features from cleaned temperature data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # With explicit paths
    python feature_engineering.py --input-path s3://bucket/processed/clean.parquet \\
                                  --output-path s3://bucket/features/features.parquet

    # Using default bucket from environment
    python feature_engineering.py
        """,
    )
    parser.add_argument(
        "--input-path",
        type=str,
        help="S3 URI for input Parquet file (default: s3://{BUCKET_NAME}/data/processed/clean_machines.parquet)",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        help="S3 URI for output Parquet file (default: s3://{BUCKET_NAME}/data/features/features.parquet)",
    )
    return parser.parse_args()


def main() -> int:
    """
    Main entry point for feature engineering.

    Returns:
        0 on success, 1 on failure
    """
    start_time = time.time()
    args = parse_args()

    try:
        # Resolve S3 paths
        bucket_name = get_bucket_name()
        input_path = (
            args.input_path
            or f"s3://{bucket_name}/data/processed/clean_machines.parquet"
        )
        output_path = (
            args.output_path or f"s3://{bucket_name}/data/features/features.parquet"
        )

        log_json(
            "INFO",
            "Starting feature engineering",
            script_name=SCRIPT_NAME,
            step="init",
            input_path=input_path,
            output_path=output_path,
        )

        # Load cleaned data
        log_json("INFO", "Loading cleaned data", script_name=SCRIPT_NAME, step="load")
        df = pd.read_parquet(input_path)
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

        # Create temp_diff feature: temperature difference from room
        log_json(
            "INFO",
            "Creating temp_diff feature",
            script_name=SCRIPT_NAME,
            step="feature",
        )
        df["temp_diff"] = df["temperature"] - df["room_temp"]

        mean_temp_diff = df["temp_diff"].mean()
        log_json(
            "INFO",
            f"temp_diff created (mean: {mean_temp_diff:.2f}°C)",
            script_name=SCRIPT_NAME,
            step="feature",
            mean_temp_diff=round(mean_temp_diff, 2),
        )

        # Create overheat target variable
        log_json(
            "INFO",
            "Creating overheat target",
            script_name=SCRIPT_NAME,
            step="feature",
            threshold=OVERHEAT_THRESHOLD,
        )
        df["overheat"] = (df["temperature"] > OVERHEAT_THRESHOLD).astype(int)

        overheat_count = df["overheat"].sum()
        overheat_pct = (overheat_count / input_rows) * 100

        log_json(
            "INFO",
            f"overheat created ({overheat_count:,} samples, {overheat_pct:.2f}%)",
            script_name=SCRIPT_NAME,
            step="feature",
            overheat_count=int(overheat_count),
            overheat_pct=round(overheat_pct, 2),
        )

        # Select final columns for feature dataset
        feature_columns = ["temperature", "temp_diff", "overheat"]
        df_final = df[feature_columns]

        # Save to Parquet (overwrites if exists)
        log_json(
            "INFO",
            "Saving feature dataset",
            script_name=SCRIPT_NAME,
            step="save",
            output_path=output_path,
            columns=feature_columns,
        )
        df_final.to_parquet(output_path, index=False)

        duration_ms = (time.time() - start_time) * 1000
        log_json(
            "INFO",
            "Feature engineering complete",
            script_name=SCRIPT_NAME,
            step="complete",
            duration_ms=duration_ms,
            input_rows=input_rows,
            output_rows=len(df_final),
            mean_temp_diff=round(mean_temp_diff, 2),
            overheat_pct=round(overheat_pct, 2),
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
