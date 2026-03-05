# SageMaker Unified Studio Demo

Educational ML project for ESADE students demonstrating end-to-end machine learning workflows using AWS SageMaker Unified Studio.

## Project Context

- **Purpose**: Teach ML lifecycle from data ingestion to production deployment
- **Problem**: Predict machine overheating (temperature > 80°C) from sensor data
- **Audience**: ESADE students learning MLOps and AWS SageMaker
- **Platform**: SageMaker Unified Studio (NOT Studio Classic) - requires IAM Identity Center (SSO)

## Tech Stack

| Component | Technology |
|-----------|------------|
| Python | 3.11 |
| Package Manager | uv |
| ML Framework | scikit-learn (LogisticRegression) |
| Data Processing | pandas, numpy |
| Visualization | matplotlib, seaborn |
| Experiment Tracking | MLflow |
| Model Serving | SageMaker Endpoints |
| Infrastructure | CloudFormation |
| AWS Services | SageMaker, S3, DataZone, IAM |
| Region | eu-west-1 |

## Project Structure

```
sagemaker-unified-studio-demo/
├── CLAUDE.md                    # This file
├── README.md                    # Project overview for users
├── .gitignore                   # Git ignore rules
├── .python-version              # Python 3.11
├── pyproject.toml               # Dependencies (includes python-dotenv)
├── deploy.sh                    # Automated deployment script
├── inference.py                 # SageMaker endpoint inference handler
│
├── cloudformation/
│   └── project-resources.yaml   # S3 bucket + IAM execution role
│
├── data/
│   └── .gitkeep                 # Generated machines.csv goes here
│
├── docs/
│   ├── architecture.md          # Technical architecture (20KB, comprehensive)
│   ├── setup.md                 # Deployment guide with IAM Identity Center
│   ├── student-guide.md         # 10-step ML lifecycle walkthrough
│   ├── env-setup.md             # .env configuration instructions
│   ├── CLAUDE.md                # Duplicate (can be removed)
│   ├── COMPLETE.md              # Outdated status file (can be removed)
│   └── PROJECT_STATUS.md        # Outdated status file (can be removed)
│
├── notebooks/                   # 8 Jupyter notebooks for ML lifecycle
│   ├── 01_explore_data.ipynb
│   ├── 02_clean_data.ipynb
│   ├── 03_feature_engineering.ipynb
│   ├── 04_train_model.ipynb
│   ├── 05_mlflow_tracking.ipynb
│   ├── 06_model_registry.ipynb
│   ├── 07_validate_model.ipynb
│   └── 08_deploy_endpoint.ipynb
│
└── scripts/
    ├── generate_data.py         # Generate synthetic machines.csv
    ├── upload_to_s3.py          # Upload data to S3
    └── create_pipeline.py       # SageMaker Pipeline orchestration
```

## Data Schema

**File**: `data/machines.csv` (generated, ~10,000 rows)

| Column | Type | Description |
|--------|------|-------------|
| `timestamp` | datetime | Reading timestamp |
| `machine_id` | string | Machine identifier (M1-M5) |
| `temperature` | float | Machine temperature (55-95°C) |
| `room_temp` | float | Ambient temperature (~25°C) |

**Generated features**:
- `temp_diff = temperature - room_temp`
- `overheat = temperature > 80` (target label)

## ML Lifecycle (10 Steps)

| Step | Notebook/Script | SageMaker Component |
|------|-----------------|---------------------|
| 1 | Data uploaded via `deploy.sh` | S3 + Data Catalog |
| 2 | `01_explore_data.ipynb` | Notebooks (JupyterLab) |
| 3 | `02_clean_data.ipynb` | Data Processing |
| 4 | `03_feature_engineering.ipynb` | Feature Engineering |
| 5 | `04_train_model.ipynb` | Training Jobs |
| 6 | `05_mlflow_tracking.ipynb` | MLflow |
| 7 | `06_model_registry.ipynb` | Model Registry |
| 8 | `07_validate_model.ipynb` | Model Validation |
| 9 | `08_deploy_endpoint.ipynb` | Inference Endpoints |
| 10 | `scripts/create_pipeline.py` | SageMaker Pipelines |

## Quick Commands

```bash
# Install dependencies
uv sync

# Generate synthetic data (creates data/machines.csv)
uv run python scripts/generate_data.py

# Deploy infrastructure and upload data
./deploy.sh

# Upload data to S3 (if running separately)
uv run python scripts/upload_to_s3.py

# Create SageMaker Pipeline
uv run python scripts/create_pipeline.py
```

## AWS Resources

**CloudFormation Stack**: `sagemaker-overheat-project`

| Resource | Name Pattern |
|----------|--------------|
| S3 Bucket | `sagemaker-unified-overheat-demo-{account-id}` |
| IAM Role | `SageMakerExecutionRole-overheat-demo` |
| Endpoint | `machine-overheat-endpoint` |
| Pipeline | `machine-overheat-pipeline` |

**S3 Structure**:
```
s3://{bucket}/
├── data/raw/machines.csv
├── data/processed/clean_machines.parquet
├── data/features/features.parquet
├── data/features/test_features.parquet
├── data/features/test_labels.parquet
└── models/logistic_regression/model.pkl
```

## Environment Configuration

Notebooks use `python-dotenv` to load configuration. Create `.env` file:

```bash
BUCKET_NAME=sagemaker-unified-overheat-demo-123456789012
EXECUTION_ROLE=arn:aws:iam::123456789012:role/SageMakerExecutionRole-overheat-demo
REGION=eu-west-1
```

See `docs/env-setup.md` for automatic generation from CloudFormation outputs.

## Key Code Patterns

### Feature Engineering
```python
df['temp_diff'] = df['temperature'] - df['room_temp']
df['overheat'] = (df['temperature'] > 80).astype(int)
```

### Model Training
```python
from sklearn.linear_model import LogisticRegression
model = LogisticRegression(random_state=42, max_iter=1000)
model.fit(X_train, y_train)
```

### Inference Handler (`inference.py`)
```python
def input_fn(request_body, content_type):
    data = json.loads(request_body)
    temp_diff = data['temperature'] - data['room_temp']
    return np.array([[data['temperature'], temp_diff]])

def predict_fn(input_data, model):
    prediction = model.predict(input_data)[0]
    probability = model.predict_proba(input_data)[0][1]
    return {'prediction': int(prediction), 'probability': float(probability)}
```

## Important Notes

### SageMaker Unified Studio vs Studio Classic
- This project uses **Unified Studio** (integrated with DataZone)
- Requires **IAM Identity Center** (SSO) authentication
- Domain must be created **manually via AWS Console** (limited CloudFormation support)
- Access via: https://console.aws.amazon.com/datazone

### Cost Estimation
- Domain: ~$0.50/hour (DataZone)
- Notebooks: ~$0.05/hour (ml.t3.medium)
- Training: ~$0.10 per run (ml.m5.large, 5 min)
- Endpoint: ~$0.05/hour (ml.t2.medium)
- **Total**: ~$2-3 per student for 3-hour session

### Cleanup Commands
```bash
# Delete endpoint
aws sagemaker delete-endpoint --endpoint-name machine-overheat-endpoint --region eu-west-1

# Empty and delete S3 bucket
aws s3 rm s3://$BUCKET --recursive --region eu-west-1

# Delete CloudFormation stack
aws cloudformation delete-stack --stack-name sagemaker-overheat-project --region eu-west-1

# Delete domain via AWS Console (10-15 min)
```

## Files to Clean Up

The following files in `docs/` are outdated scaffolding and can be removed:
- `docs/CLAUDE.md` - Duplicate of root CLAUDE.md
- `docs/COMPLETE.md` - Outdated completion status
- `docs/PROJECT_STATUS.md` - Outdated (says notebooks "TO BE CREATED" but they exist)

## Documentation Map

| Need | File |
|------|------|
| Project overview | `README.md` |
| Deployment steps | `docs/setup.md` |
| Student walkthrough | `docs/student-guide.md` |
| Technical architecture | `docs/architecture.md` |
| Environment setup | `docs/env-setup.md` |
