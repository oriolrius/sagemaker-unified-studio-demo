"""
Shared utilities for SageMaker Unified Studio workflow scripts.

Provides:
- Structured JSON logging for CloudWatch Logs Insights
- S3 credential fallback (IAM role → .env file)
"""

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv


def log_json(
    level: str,
    message: str,
    script_name: str | None = None,
    step: str | None = None,
    duration_ms: float | None = None,
    **extra: Any,
) -> None:
    """
    Log a structured JSON message to stdout for CloudWatch Logs Insights.

    Args:
        level: Log level (INFO, WARNING, ERROR)
        message: Human-readable log message
        script_name: Name of the calling script
        step: Current processing step
        duration_ms: Duration in milliseconds (if timing)
        **extra: Additional fields to include in the log entry

    Example:
        log_json("INFO", "Processing complete", script_name="clean_data.py", rows=1000)
    """
    log_entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level.upper(),
        "message": message,
    }

    # Add optional fields if provided
    if script_name:
        log_entry["script_name"] = script_name
    if step:
        log_entry["step"] = step
    if duration_ms is not None:
        log_entry["duration_ms"] = round(duration_ms, 2)

    # Add any extra fields
    if extra:
        log_entry["extra"] = extra

    print(json.dumps(log_entry), flush=True)


def get_bucket_name() -> str:
    """
    Get S3 bucket name from environment or .env file.

    Tries in order:
    1. BUCKET_NAME environment variable (set by SageMaker Processing Job)
    2. .env file in current directory or parent directories

    Returns:
        S3 bucket name

    Raises:
        ValueError: If bucket name not found in any location
    """
    # Try environment variable first (SageMaker Processing Job)
    bucket_name = os.environ.get("BUCKET_NAME")
    if bucket_name:
        return bucket_name

    # Fallback: Load from .env file
    load_dotenv()
    bucket_name = os.environ.get("BUCKET_NAME")
    if bucket_name:
        return bucket_name

    # Also try the shared .env location used by notebooks
    shared_env_path = "/home/sagemaker-user/shared/.env"
    if os.path.exists(shared_env_path):
        load_dotenv(shared_env_path)
        bucket_name = os.environ.get("BUCKET_NAME")
        if bucket_name:
            return bucket_name

    raise ValueError(
        "BUCKET_NAME not found. Set it via:\n"
        "  1. Environment variable: export BUCKET_NAME=your-bucket\n"
        "  2. .env file with BUCKET_NAME=your-bucket\n"
        "  3. /home/sagemaker-user/shared/.env (in SageMaker)"
    )


def validate_columns(df: Any, required_columns: list[str], context: str = "") -> None:
    """
    Validate that a DataFrame contains required columns.

    Args:
        df: pandas DataFrame to validate
        required_columns: List of column names that must exist
        context: Optional context for error message (e.g., filename)

    Raises:
        ValueError: If any required column is missing
    """
    missing = set(required_columns) - set(df.columns)
    if missing:
        ctx = f" in {context}" if context else ""
        raise ValueError(f"Missing required columns{ctx}: {sorted(missing)}")
