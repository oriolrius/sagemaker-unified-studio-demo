# SageMaker Unified Studio - Machine Overheat ML Pipeline

End-to-end ML pipeline for predicting machine overheating, built and orchestrated entirely within **Amazon SageMaker Unified Studio**. The pipeline runs as a workflow that cleans data, engineers features, trains a model, and logs experiment traces to the Unified Studio MLflow App.

## Architecture

```
SageMaker Unified Studio
├── Workflows (MWAA/Airflow)
│   └── machine_overheat_pipeline
│       ├── clean_data          → 06_clean_data.ipynb
│       ├── feature_engineering → 07_feature_engineering.ipynb
│       └── train_model         → 09_mlflow_tracking.ipynb  ──→  MLflow App
│
├── MLflow App (machine-overheat-mlflow)
│   └── Experiment: machine-overheat
│       └── Run: logistic_regression_v1 (metrics, params, model artifact)
│
├── Files (shared project storage)
│   └── Notebooks
│
└── JupyterLab (interactive development)
```

Each workflow task uses `SageMakerNotebookOperator`, which provisions an `ml.m6i.xlarge` instance, runs the notebook via papermill, and terminates. Total pipeline time: ~12 minutes (3 tasks x ~3 min provisioning + execution).

## Quick Start

### Step 1. Create the MLflow App (in SageMaker AI Studio)

> **Important:** You cannot create an MLflow App from Unified Studio. It must be created in **SageMaker AI Studio** (the classic Studio IDE) first, then connected to your Unified Studio project.

1. Open **SageMaker AI Studio** (from the AWS Console: SageMaker > Domains > your domain > Open Studio)
2. Click **MLflow** in the left sidebar
3. Click **"Create MLflow App"**

![SageMaker Studio MLflow page](assets/sagemaker-studio-mlflow-create.png)

4. Fill in the creation form:
   - **Name**: e.g., `machine-overheat-mlflow` (letters, numbers, dashes only)
   - **Advanced settings** (expand to configure):
     - **IAM role**: Select your SageMaker execution role (pre-populated with domain default)
     - **Artifact storage location (S3 URI)**: e.g., `s3://sagemaker-eu-west-1-658203403846`

![Create MLflow App dialog with advanced settings](assets/sagemaker-studio-mlflow-create-advanced.png)

5. Click **Create** and wait ~5 minutes for the app to reach "Created" status
6. Copy the **MLflow App ARN** (format: `arn:aws:sagemaker:REGION:ACCOUNT:mlflow-app/APP_ID`)

### Step 2. Connect MLflow to your Unified Studio project

1. Open your project in SageMaker Unified Studio
2. Go to **MLflow** in the left sidebar (under AI/ML)

![Unified Studio MLflow page](assets/unified-studio-mlflow-page.png)

3. Click **"Connect Tracking Server"** (green button, top-right)
4. Fill in:
   - **Connection name**: e.g., `machine-overheat-mlflow`
   - **MLflow Tracking Server ARN**: paste the ARN from Step 1

![Connect Tracking Server panel](assets/unified-studio-connect-tracking-server-panel.png)

5. Click **"Connect to server"**
6. The server appears in the table with status "On". Click **"Open MLflow"** to verify.

![Connected MLflow server details](assets/unified-studio-mlflow-connection-details.png)

### Step 3. Upload notebooks

Go to **Files** in the left sidebar and upload:

- `06_clean_data.ipynb` — data cleaning
- `07_feature_engineering.ipynb` — feature creation
- `09_mlflow_tracking.ipynb` — model training with MLflow tracking

### Step 4. Create the workflow

Go to **Workflows** in the left sidebar, click **Create workflow**, and define three tasks in sequence:

```
clean_data → feature_engineering → train_model
```

Switch to **Code view** and set the YAML. Replace the `mlflow_tracking_uri` value with your own MLflow App ARN:

```yaml
machine_overheat_pipeline:
  dag_id: machine_overheat_pipeline
  tasks:
    clean_data:
      operator: >-
        airflow.providers.amazon.aws.operators.sagemaker_unified_studio.SageMakerNotebookOperator
      input_config:
        input_params: {}
        input_path: 06_clean_data.ipynb
      compute: {}
      output_config:
        output_formats:
          - NOTEBOOK
    feature_engineering:
      dependencies:
        - clean_data
      operator: >-
        airflow.providers.amazon.aws.operators.sagemaker_unified_studio.SageMakerNotebookOperator
      input_config:
        input_params: {}
        input_path: 07_feature_engineering.ipynb
      compute: {}
      output_config:
        output_formats:
          - NOTEBOOK
    train_model:
      dependencies:
        - feature_engineering
      operator: >-
        airflow.providers.amazon.aws.operators.sagemaker_unified_studio.SageMakerNotebookOperator
      input_config:
        input_params:
          mlflow_tracking_uri: "arn:aws:sagemaker:eu-west-1:658203403846:mlflow-app/app-IN74ELWDTMBI"
        input_path: 09_mlflow_tracking.ipynb
      compute: {}
      output_config:
        output_formats:
          - NOTEBOOK
  description: >-
    ML pipeline for machine overheat prediction: clean_data ->
    feature_engineering -> train_model with MLflow tracking
```

Click **Apply**, then **Save**.

### Step 5. Run and verify

1. Click **Run** on the workflow page
2. Monitor progress in the **Runs** tab (~12 min total)
3. Go to **MLflow > Open MLflow** to see the logged experiment with metrics, parameters, and model artifact

## MLflow Integration: How It Works

### The Problem

`MLFLOW_TRACKING_URI` is **not auto-injected** into the `SageMakerNotebookOperator` execution environment. Without explicit configuration, MLflow defaults to local file storage (`mlruns/`), and traces are lost when the compute instance terminates.

### The Solution

The MLflow App ARN is passed as a **papermill parameter** from the workflow YAML into the notebook.

**Workflow YAML** passes the ARN:
```yaml
input_params:
  mlflow_tracking_uri: "arn:aws:sagemaker:eu-west-1:658203403846:mlflow-app/app-IN74ELWDTMBI"
```

**Notebook** receives it via a cell tagged `parameters` (papermill convention):
```python
# Parameters (injected by workflow via papermill)
mlflow_tracking_uri = "arn:aws:sagemaker:eu-west-1:658203403846:mlflow-app/app-IN74ELWDTMBI"
```

Then uses it before any MLflow operation:
```python
mlflow.set_tracking_uri(mlflow_tracking_uri)
mlflow.set_experiment("machine-overheat")
```

### The sagemaker-mlflow Plugin Version Issue

The `SageMakerNotebookOperator` execution environment ships with `sagemaker-mlflow==0.1.x`, which only supports classic `mlflow-tracking-server` ARNs. Unified Studio MLflow Apps use the `mlflow-app` ARN format, which requires `sagemaker-mlflow>=0.2.0`.

| Plugin Version | `mlflow-tracking-server` ARN | `mlflow-app` ARN |
|---|---|---|
| 0.1.x (pre-installed) | Supported | **Not supported** (404 error) |
| **0.2.0+** | Supported | **Supported** |

The notebook must upgrade the plugin **before** importing mlflow:

```python
import subprocess, sys
subprocess.run(
    [sys.executable, "-m", "pip", "install", "sagemaker-mlflow>=0.2.0", "--quiet", "--upgrade"],
    capture_output=True, text=True
)
```

Without this, you get:
```
MlflowException: API request to endpoint /api/2.0/mlflow/experiments/get-by-name
failed with error code 404 != 200. Response body: 'Tracking server could not be found'
```

## Notebooks

### Pipeline Notebooks (used by the workflow)

| Notebook | Purpose | Input | Output |
|---|---|---|---|
| `06_clean_data.ipynb` | Remove nulls, convert types | `s3://bucket/data/raw/machines.csv` | `s3://bucket/data/processed/clean_machines.parquet` |
| `07_feature_engineering.ipynb` | Create `temp_diff`, `overheat` label | `s3://bucket/data/processed/clean_machines.parquet` | `s3://bucket/data/features/features.parquet` |
| `09_mlflow_tracking.ipynb` | Train LogisticRegression, log to MLflow | `s3://bucket/data/features/features.parquet` | MLflow run + `s3://bucket/models/` |

### Setup & Exploration Notebooks (run manually in JupyterLab)

| Notebook | Purpose |
|---|---|
| `01_setup_env.ipynb` | Create `.env` with `BUCKET_NAME` and `REGION` |
| `02_create_s3_bucket.ipynb` | Create S3 bucket |
| `03_generate_data.ipynb` | Generate 216,000 synthetic temperature readings |
| `04_upload_to_s3.ipynb` | Upload `machines.csv` to S3 |
| `05_explore_data.ipynb` | Exploratory data analysis |
| `08_train_model.ipynb` | Basic training (no MLflow) |
| `10_model_registry.ipynb` | Register model version |
| `11_validate_model.ipynb` | Accuracy validation (>85% threshold) |

### Deployment Notebooks (optional)

| Notebook | Purpose |
|---|---|
| `12_deploy_endpoint.ipynb` | Create SageMaker real-time inference endpoint |
| `13_test_endpoint.ipynb` | Test endpoint with various scenarios |

## Data Schema

**Input**: `machines.csv` (216,000 rows, 5 machines)

| Column | Type | Description |
|---|---|---|
| `timestamp` | datetime | Reading timestamp |
| `machine_id` | string | Machine ID (M1-M5) |
| `temperature` | float | Machine temperature (55-95 C) |
| `room_temp` | float | Ambient temperature (~25 C) |

**Engineered Features**:
- `temp_diff`: `temperature - room_temp`
- `overheat`: `1` if `temperature > 80`, else `0`

## Model

- **Algorithm**: Logistic Regression (scikit-learn)
- **Features**: `temperature`, `temp_diff`
- **Target**: `overheat` (binary classification)
- **Accuracy**: 100% on this dataset (clear threshold boundary)

## S3 Structure

```
s3://{bucket}/
├── data/
│   ├── raw/machines.csv
│   ├── processed/clean_machines.parquet
│   └── features/features.parquet
└── models/
    └── model.joblib
```

Workflow output notebooks are stored at:
```
s3://amazon-sagemaker-{account}-{region}-{project_id}/shared/workflows/output/
```

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| MLflow 404 "Tracking server could not be found" | `sagemaker-mlflow` plugin 0.1.x doesn't support `mlflow-app` ARN | Add `pip install sagemaker-mlflow>=0.2.0` cell before `import mlflow` |
| Notebook can't read S3 data | `BUCKET_NAME` env var not set in operator context | Use hardcoded fallback: `os.getenv('BUCKET_NAME', 'your-bucket')` |
| IAM AccessDeniedException on MLflow | Missing `CreatePresignedMlflowAppUrl` permission | Add `sagemaker:CreatePresignedMlflowAppUrl` to execution role |
| Can't create MLflow App in Unified Studio | Creation is only available in SageMaker AI Studio | Open SageMaker AI Studio > MLflow > Create MLflow App |

## Unified Studio Components Used

| Component | Usage |
|---|---|
| JupyterLab | Interactive notebook development |
| Workflows | Orchestrated ML pipeline (3 tasks) |
| MLflow | Experiment tracking (metrics, params, model artifacts) |
| Files | Shared project notebook storage |

## Cleanup

```bash
# Delete MLflow App
aws sagemaker delete-mlflow-app --arn "arn:aws:sagemaker:eu-west-1:658203403846:mlflow-app/app-IN74ELWDTMBI"

# Delete endpoint (if deployed)
aws sagemaker delete-endpoint --endpoint-name machine-overheat-endpoint --region eu-west-1

# Empty and delete S3 bucket
aws s3 rm s3://$BUCKET --recursive --region eu-west-1
```
