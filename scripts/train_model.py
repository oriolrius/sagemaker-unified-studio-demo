#!/usr/bin/env python3
"""
Train machine overheat prediction model with MLflow tracking.

Loads feature dataset, trains a LogisticRegression model, logs experiment
metrics to MLflow, and saves the model artifact.

In SageMaker Unified Studio, MLFLOW_TRACKING_URI is automatically injected.
Do NOT hardcode tracking URI - it is auto-configured at runtime.

Usage:
    python train_model.py --input-path s3://bucket/data/features/features.parquet \
                          --model-output s3://bucket/models/model.joblib \
                          --experiment-name machine-overheat
"""

import argparse
import sys
import time
import traceback

import joblib
import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

from utils import get_bucket_name, log_json, validate_columns

SCRIPT_NAME = "train_model.py"
REQUIRED_COLUMNS = ["temperature", "temp_diff", "overheat"]
FEATURE_COLUMNS = ["temperature", "temp_diff"]
TARGET_COLUMN = "overheat"
ACCURACY_THRESHOLD = 0.85


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Train machine overheat prediction model with MLflow tracking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # With explicit paths
    python train_model.py --input-path s3://bucket/features/features.parquet \\
                          --model-output s3://bucket/models/model.joblib

    # Using default bucket from environment
    python train_model.py --experiment-name my-experiment

Note:
    In SageMaker Unified Studio, MLFLOW_TRACKING_URI is automatically set.
    Experiments will appear in Build > MLflow in the Studio UI.
        """,
    )
    parser.add_argument(
        "--input-path",
        type=str,
        help="S3 URI for input features Parquet (default: s3://{BUCKET_NAME}/data/features/features.parquet)",
    )
    parser.add_argument(
        "--model-output",
        type=str,
        help="S3 URI for output model file (default: s3://{BUCKET_NAME}/models/model.joblib)",
    )
    parser.add_argument(
        "--experiment-name",
        type=str,
        default="machine-overheat",
        help="MLflow experiment name (default: machine-overheat)",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Test split ratio (default: 0.2)",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random state for reproducibility (default: 42)",
    )
    return parser.parse_args()


def main() -> int:
    """
    Main entry point for model training.

    Returns:
        0 on success, 1 on failure
    """
    start_time = time.time()
    args = parse_args()

    try:
        # Resolve paths - only fetch bucket name if paths not explicitly provided
        if args.input_path and args.model_output:
            input_path = args.input_path
            model_output = args.model_output
        else:
            bucket_name = get_bucket_name()
            input_path = (
                args.input_path or f"s3://{bucket_name}/data/features/features.parquet"
            )
            model_output = args.model_output or f"s3://{bucket_name}/models/model.joblib"

        log_json(
            "INFO",
            "Starting model training",
            script_name=SCRIPT_NAME,
            step="init",
            input_path=input_path,
            model_output=model_output,
            experiment_name=args.experiment_name,
        )

        # Set MLflow experiment
        # NOTE: Do NOT call mlflow.set_tracking_uri() - it's auto-injected in Unified Studio
        mlflow.set_experiment(args.experiment_name)

        log_json(
            "INFO",
            f"MLflow experiment set: {args.experiment_name}",
            script_name=SCRIPT_NAME,
            step="mlflow",
        )

        # Load feature data
        log_json("INFO", "Loading feature data", script_name=SCRIPT_NAME, step="load")
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

        # Prepare features and target
        X = df[FEATURE_COLUMNS]
        y = df[TARGET_COLUMN]

        # Split data with stratification
        log_json(
            "INFO",
            f"Splitting data (test_size={args.test_size})",
            script_name=SCRIPT_NAME,
            step="split",
        )
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=args.test_size, random_state=args.random_state, stratify=y
        )

        log_json(
            "INFO",
            f"Train: {len(X_train):,} rows, Test: {len(X_test):,} rows",
            script_name=SCRIPT_NAME,
            step="split",
            train_rows=len(X_train),
            test_rows=len(X_test),
        )

        # Train model with MLflow tracking
        with mlflow.start_run(run_name="logistic_regression_v1"):
            # Log parameters
            mlflow.log_param("model_type", "LogisticRegression")
            mlflow.log_param("test_size", args.test_size)
            mlflow.log_param("random_state", args.random_state)
            mlflow.log_param("features", FEATURE_COLUMNS)
            mlflow.log_param("target", TARGET_COLUMN)

            log_json(
                "INFO",
                "Training LogisticRegression model",
                script_name=SCRIPT_NAME,
                step="train",
            )

            # Train model
            model = LogisticRegression(random_state=args.random_state, max_iter=1000)
            model.fit(X_train, y_train)

            # Make predictions
            y_pred = model.predict(X_test)

            # Calculate metrics
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred)
            recall = recall_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)

            # Log metrics to MLflow
            mlflow.log_metric("accuracy", accuracy)
            mlflow.log_metric("precision", precision)
            mlflow.log_metric("recall", recall)
            mlflow.log_metric("f1_score", f1)

            log_json(
                "INFO",
                f"Model trained - Accuracy: {accuracy:.3f}",
                script_name=SCRIPT_NAME,
                step="train",
                accuracy=round(accuracy, 4),
                precision=round(precision, 4),
                recall=round(recall, 4),
                f1_score=round(f1, 4),
            )

            # Warn if accuracy below threshold
            if accuracy < ACCURACY_THRESHOLD:
                log_json(
                    "WARNING",
                    f"Accuracy {accuracy:.3f} is below threshold {ACCURACY_THRESHOLD}",
                    script_name=SCRIPT_NAME,
                    step="validate",
                    accuracy=round(accuracy, 4),
                    threshold=ACCURACY_THRESHOLD,
                )

            # Log model to MLflow
            log_json(
                "INFO",
                "Logging model to MLflow",
                script_name=SCRIPT_NAME,
                step="mlflow",
            )
            mlflow.sklearn.log_model(model, "model")

        # Save model
        log_json(
            "INFO",
            "Saving model",
            script_name=SCRIPT_NAME,
            step="save",
            model_output=model_output,
        )

        if model_output.startswith("s3://"):
            # For S3, save locally first then upload
            import s3fs
            local_model_path = "/tmp/model.joblib"
            joblib.dump(model, local_model_path)
            fs = s3fs.S3FileSystem()
            fs.put(local_model_path, model_output)
        else:
            # Local file path
            import os
            os.makedirs(os.path.dirname(model_output), exist_ok=True)
            joblib.dump(model, model_output)

        duration_ms = (time.time() - start_time) * 1000
        log_json(
            "INFO",
            "Model training complete",
            script_name=SCRIPT_NAME,
            step="complete",
            duration_ms=duration_ms,
            accuracy=round(accuracy, 4),
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            model_output=model_output,
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
