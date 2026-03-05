# SageMaker Unified Studio Demo

Educational ML project demonstrating machine overheat prediction using AWS SageMaker Unified Studio.

## Project Overview

- **Purpose**: Educational demo for ESADE students to learn end-to-end ML workflows
- **Problem**: Predict if factory machines will overheat (temperature > 80°C)
- **Model**: Logistic regression with `temperature_difference` feature
- **Platform**: AWS SageMaker Unified Studio (requires IAM Identity Center, not IAM roles)

## Tech Stack

- **Python**: 3.11
- **Package Manager**: uv
- **ML**: scikit-learn, pandas, numpy
- **AWS**: SageMaker, S3, CloudFormation, DataZone
- **Experiment Tracking**: MLflow
- **Region**: eu-west-1

## Project Structure

```
cloudformation/    # AWS infrastructure (S3 bucket, IAM roles)
data/              # Generated synthetic data (machines.csv)
docs/              # Setup guide, student guide, architecture
notebooks/         # Jupyter notebooks for each ML lifecycle step (01-08)
scripts/           # Python scripts for data generation, upload, pipeline
```

## Quick Commands

```bash
# Install dependencies
uv sync

# Generate synthetic data
uv run python scripts/generate_data.py

# Deploy infrastructure (S3, IAM roles)
./deploy.sh

# Upload data to S3
uv run python scripts/upload_to_s3.py
```

## Notebooks (ML Lifecycle)

1. `01_explore_data.ipynb` - Data exploration
2. `02_clean_data.ipynb` - Data cleaning
3. `03_feature_engineering.ipynb` - Feature creation (temp_diff)
4. `04_train_model.ipynb` - Model training
5. `05_mlflow_tracking.ipynb` - Experiment tracking
6. `06_model_registry.ipynb` - Model versioning
7. `07_validate_model.ipynb` - Pre-deployment validation
8. `08_deploy_endpoint.ipynb` - REST API deployment

## Key Patterns

### Feature Engineering
```python
df["temp_diff"] = df["temperature"] - df["room_temp"]
df["overheat"] = df["temperature"] > 80
```

### Data Schema (machines.csv)
- `timestamp` - Reading timestamp
- `machine_id` - Machine identifier (M1-M5)
- `temperature` - Machine temperature (°C)
- `room_temp` - Ambient temperature (°C)

## CloudFormation Stack

Stack name: `sagemaker-overheat-project`

Resources:
- S3 bucket: `sagemaker-unified-overheat-demo-{account-id}`
- IAM role: `SageMakerExecutionRole-overheat-demo`

## Cleanup

```bash
# Delete SageMaker endpoint
aws sagemaker delete-endpoint --endpoint-name machine-overheat-endpoint --region eu-west-1

# Delete CloudFormation stack
aws cloudformation delete-stack --stack-name sagemaker-overheat-project --region eu-west-1

# Delete Unified Studio domain via AWS Console
```

## Notes

- SageMaker Unified Studio domains must be created via AWS Console (limited CloudFormation support)
- Requires IAM Identity Center authentication (SSO), not IAM roles
- Estimated cost: ~$2-3 per student for a 3-hour session
