"""
Machine Overheat Prediction ML Pipeline - Apache Airflow DAG

This DAG orchestrates the end-to-end ML pipeline for machine overheat prediction:
1. clean_data: Load raw CSV, remove nulls, convert timestamps, save as Parquet
2. feature_engineering: Create temp_diff and overheat features
3. train_model: Train LogisticRegression with MLflow experiment tracking

Usage in SageMaker Unified Studio:
1. Upload this file to Workflows > Code workflows
2. Configure S3_BUCKET in Airflow Variables or environment
3. Trigger manually or set a schedule

The DAG uses subprocess to execute the standalone Python scripts, ensuring
each step is isolated and can be monitored independently.
"""

import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator

# =============================================================================
# Configuration
# =============================================================================
# Get S3 bucket from Airflow Variables or environment variable
# In SageMaker Unified Studio, set this in Admin > Variables
# Or export BUCKET_NAME in your environment

try:
    S3_BUCKET = Variable.get("S3_BUCKET")
except Exception:
    S3_BUCKET = os.environ.get("BUCKET_NAME", "your-bucket-name-here")

# S3 paths for pipeline data
RAW_DATA_PATH = f"s3://{S3_BUCKET}/data/raw/machines.csv"
CLEAN_DATA_PATH = f"s3://{S3_BUCKET}/data/processed/clean_machines.parquet"
FEATURES_PATH = f"s3://{S3_BUCKET}/data/features/features.parquet"
MODEL_PATH = f"s3://{S3_BUCKET}/models/model.joblib"

# Path to scripts directory (relative to DAG file)
# In SageMaker Unified Studio, scripts should be in the same project
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"

# MLflow experiment name
EXPERIMENT_NAME = "machine-overheat"

# MLflow tracking URI (SageMaker MLflow App ARN)
# Set via Airflow Variable 'MLFLOW_TRACKING_URI' or environment variable
try:
    MLFLOW_TRACKING_URI = Variable.get("MLFLOW_TRACKING_URI")
except Exception:
    MLFLOW_TRACKING_URI = os.environ.get(
        "MLFLOW_TRACKING_URI",
        "arn:aws:sagemaker:eu-west-1:658203403846:mlflow-app/app-IN74ELWDTMBI",
    )


# =============================================================================
# DAG Default Arguments
# =============================================================================
default_args = {
    "owner": "ml-team",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


# =============================================================================
# Helper Functions
# =============================================================================
def run_script(script_name: str, args: list[str]) -> None:
    """
    Execute a Python script from the scripts directory.

    Args:
        script_name: Name of the script file (e.g., 'clean_data.py')
        args: List of command line arguments to pass to the script

    Raises:
        subprocess.CalledProcessError: If script exits with non-zero code
    """
    script_path = SCRIPTS_DIR / script_name

    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    cmd = [sys.executable, str(script_path)] + args

    print(f"Executing: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        capture_output=False,  # Let output flow to Airflow logs
        check=True,  # Raise exception on non-zero exit
        env={**os.environ, "BUCKET_NAME": S3_BUCKET},
    )

    print(f"Script {script_name} completed with return code: {result.returncode}")


def task_clean_data() -> None:
    """Task: Clean raw machine data."""
    run_script(
        "clean_data.py",
        [
            "--input-path",
            RAW_DATA_PATH,
            "--output-path",
            CLEAN_DATA_PATH,
        ],
    )


def task_feature_engineering() -> None:
    """Task: Create ML features from cleaned data."""
    run_script(
        "feature_engineering.py",
        [
            "--input-path",
            CLEAN_DATA_PATH,
            "--output-path",
            FEATURES_PATH,
        ],
    )


def task_train_model() -> None:
    """Task: Train model with MLflow tracking."""
    run_script(
        "train_model.py",
        [
            "--input-path",
            FEATURES_PATH,
            "--model-output",
            MODEL_PATH,
            "--experiment-name",
            EXPERIMENT_NAME,
            "--tracking-uri",
            MLFLOW_TRACKING_URI,
        ],
    )


# =============================================================================
# DAG Definition
# =============================================================================
with DAG(
    dag_id="machine_overheat_pipeline",
    default_args=default_args,
    description="ML pipeline for machine overheat prediction with MLflow tracking",
    schedule_interval=None,  # Manual trigger only; set to '@daily' for scheduled runs
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["ml", "overheat", "sagemaker"],
    doc_md=__doc__,
) as dag:
    # Task 1: Clean raw data
    clean_data = PythonOperator(
        task_id="clean_data",
        python_callable=task_clean_data,
        doc_md="Load raw CSV, remove nulls, convert timestamps, save as Parquet",
    )

    # Task 2: Feature engineering
    feature_engineering = PythonOperator(
        task_id="feature_engineering",
        python_callable=task_feature_engineering,
        doc_md="Create temp_diff and overheat features from cleaned data",
    )

    # Task 3: Train model with MLflow
    train_model = PythonOperator(
        task_id="train_model",
        python_callable=task_train_model,
        doc_md="Train LogisticRegression model and log to MLflow",
    )

    # Define task dependencies
    # clean_data -> feature_engineering -> train_model
    clean_data >> feature_engineering >> train_model
