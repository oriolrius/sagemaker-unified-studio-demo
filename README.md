# SageMaker Unified Studio Demo: Machine Overheat Prediction

An end-to-end machine learning project demonstrating the complete ML lifecycle using **AWS SageMaker Unified Studio**. This project predicts whether factory machines will overheat based on temperature sensor data.

> **Important**: This uses **SageMaker Unified Studio** (the unified data and AI development environment), not SageMaker Studio Classic. SageMaker Unified Studio integrates data governance (DataZone), analytics, and ML in a single platform with IAM Identity Center authentication.

## Project Overview

### The Problem

A factory monitors machines with temperature sensors that record data every minute:
- `machine_id` - Unique machine identifier
- `temperature` - Current machine temperature (°C)
- `room_temperature` - Ambient room temperature (°C)
- `timestamp` - When the reading was taken

**Goal**: Predict if a machine will overheat in the next minute (temperature > 80°C)

### Why This Example?

This use case is intentionally simple for educational purposes:
- **Easy to understand** - Clear business problem with intuitive features
- **Transparent transformations** - Students see exactly how features are created
- **Simple model** - Logistic regression is interpretable
- **Complete ML lifecycle** - Covers all 10 steps from data ingestion to deployment
- **Real-world applicable** - Pattern applies to IoT monitoring, predictive maintenance

### Example Dataset

| timestamp | machine_id | temperature | room_temp |
|-----------|------------|-------------|-----------|
| 10:00     | M1         | 60          | 25        |
| 10:01     | M1         | 62          | 25        |
| 10:02     | M1         | 85          | 25        |
| 10:03     | M1         | 70          | 25        |

The model learns that when `temperature > 80`, the machine is overheating.

## Architecture

This project demonstrates **10 key SageMaker Unified Studio components**:

1. **Data Catalog** - Discover and access data across the organization
2. **Notebooks** - Interactive data exploration with JupyterLab
3. **Data Processing** - ETL for cleaning and transformation
4. **Feature Engineering** - Creating `temperature_difference` feature
5. **Training Jobs** - Logistic regression model training
6. **MLflow** - Experiment tracking and reproducibility
7. **Model Registry** - Versioned model storage
8. **Model Validation** - Pre-deployment testing
9. **Inference Endpoints** - REST API for predictions
10. **Workflows** - End-to-end pipeline orchestration

### ML Pipeline Flow

```
Synthetic Data Generation
         ↓
    S3 Upload (machines.csv)
         ↓
  Data Catalog Registration
         ↓
  Data Exploration (Notebook)
         ↓
   Data Cleaning (Remove nulls, parse timestamps)
         ↓
Feature Engineering (temp_diff = temperature - room_temp)
         ↓
  Training Job (Logistic Regression)
         ↓
   MLflow Logging (Metrics, parameters)
         ↓
  Model Registry (Version 1)
         ↓
   Validation (Test accuracy)
         ↓
Endpoint Deployment (REST API)
         ↓
  Inference (Real-time predictions)
```

## Project Structure

```
sagemaker-unified-studio-demo/
├── cloudformation/
│   └── project-resources.yaml         # S3 bucket, IAM roles (domain created via console)
├── docs/
│   ├── setup.md                       # Detailed deployment instructions
│   ├── student-guide.md               # Step-by-step walkthrough
│   ├── architecture.md                # Technical architecture details
│   └── env-setup.md                   # Environment configuration guide
├── notebooks/
│   ├── 01_explore_data.ipynb          # Step 2: Data exploration
│   ├── 02_clean_data.ipynb            # Step 3: Data cleaning
│   ├── 03_feature_engineering.ipynb   # Step 4: Feature creation
│   ├── 04_train_model.ipynb           # Step 5: Model training
│   ├── 05_mlflow_tracking.ipynb       # Step 6: Experiment tracking
│   ├── 06_model_registry.ipynb        # Step 7: Register model
│   ├── 07_validate_model.ipynb        # Step 8: Validation
│   └── 08_deploy_endpoint.ipynb       # Step 9: Deployment
├── scripts/
│   ├── generate_data.py               # Generate synthetic machines.csv
│   ├── upload_to_s3.py                # Upload data to S3
│   ├── create_project.py              # Create Unified Studio project via API
│   └── create_pipeline.py             # Step 10: Workflow orchestration
├── data/
│   └── .gitkeep                       # Generated data goes here
├── inference.py                       # SageMaker inference script
├── pyproject.toml                     # Python dependencies (uv)
├── .python-version                    # Python 3.11
├── deploy.sh                          # Automated deployment script
└── README.md                          # This file
```

## Quick Start

### Prerequisites

- AWS CLI configured with appropriate credentials
- [uv](https://docs.astral.sh/uv/) for Python dependency management
- **AWS IAM Identity Center** configured (required for SageMaker Unified Studio)
- IAM permissions for DataZone, S3, IAM role creation
- Python 3.11+

### 1. Create SageMaker Unified Studio Domain (Manual - One Time)

SageMaker Unified Studio domains must be created via the AWS Console:

1. Navigate to https://console.aws.amazon.com/datazone (region: **eu-west-1**)
2. Choose **Create a Unified Studio domain** → **Quick setup**
3. Create or select a VPC (or use "Create new VPC")
4. Review default settings (domain name, roles, encryption)
5. Create or select an **IAM Identity Center user** (SSO required)
6. Choose **Create domain**

**Estimated time**: 10-15 minutes

> **Why manual?** SageMaker Unified Studio has limited CloudFormation support as of 2026. AWS recommends console-based domain creation with IAM Identity Center authentication. IAM roles cannot log in to Unified Studio.

### 2. Generate Synthetic Data

```bash
cd /home/oriol/esade/sagemaker-unified-studio-demo
uv sync
uv run python scripts/generate_data.py
```

This creates `data/machines.csv` with 10,000 synthetic temperature readings.

### 3. Deploy Project Infrastructure

```bash
./deploy.sh
```

This script:
- Creates S3 bucket for data storage
- Uploads `machines.csv` to S3
- Creates IAM roles for project execution
- Outputs bucket name and role ARNs

**Estimated time**: 2-3 minutes

### 4. Access SageMaker Unified Studio

1. Navigate to https://console.aws.amazon.com/datazone (region: **eu-west-1**)
2. Sign in with your **IAM Identity Center user** (not IAM role)
3. Select your domain
4. Create a new project using the **ML Development** blueprint
5. Upload notebooks from the `notebooks/` directory
6. Upload `inference.py` to the project root

### 5. Configure Environment

Create `.env` file with your CloudFormation outputs. See [docs/env-setup.md](docs/env-setup.md) for details.

### 6. Follow Student Guide

Open [docs/student-guide.md](docs/student-guide.md) and work through each notebook step-by-step.

## What Students Will Learn

### Technical Skills

- **Data Engineering**: S3 integration, pandas data cleaning, feature engineering
- **ML Training**: Scikit-learn logistic regression, train/test splits
- **MLOps**: Experiment tracking, model versioning, validation workflows
- **Deployment**: SageMaker endpoints, REST API inference
- **Automation**: SageMaker Pipelines for reproducible ML workflows
- **Data Governance**: DataZone catalog, data discovery, access control

### Conceptual Understanding

- Why feature engineering matters (`temp_diff` improves predictions)
- How to create labels from raw data (`overheat = temperature > 80`)
- The importance of validation before deployment
- Model registry for version control and governance
- End-to-end ML lifecycle from data to production API
- Data governance and cataloging in unified environments

## Key Features

### Simple Feature Engineering

Students create one intuitive feature:

```python
df["temp_diff"] = df["temperature"] - df["room_temp"]
```

**Why this works**: Machines normally run hotter than ambient temperature. A large difference indicates potential overheating.

### Transparent Label Creation

The target variable is explicitly derived:

```python
df["overheat"] = df["temperature"] > 80
```

Students see exactly how the label is created from the business rule.

### Interpretable Model

Logistic regression allows students to understand:
- Feature coefficients (which features matter most)
- Probability outputs (confidence in predictions)
- Decision boundaries (when does the model predict overheating?)

### Real-World Inference

The deployed endpoint accepts real-time requests:

```bash
curl -X POST https://<endpoint-url>/invocations \
  -H "Content-Type: application/json" \
  -d '{"temperature": 78, "room_temp": 25}'
```

Response:
```json
{
  "overheat_probability": 0.76,
  "prediction": "likely_overheat"
}
```

## Cost Estimation

**Development environment** (per student, per hour):
- SageMaker Unified Studio project: ~$0.05/hour (compute resources)
- S3 storage: <$0.01/month (small dataset)
- Training job: ~$0.10 (ml.m5.large, 5 minutes)
- Endpoint: ~$0.05/hour (ml.t2.medium)
- DataZone domain: ~$0.50/hour (when active)

**Estimated cost for 3-hour class**: ~$2-3 per student

**Remember to delete projects and domain after class to avoid ongoing charges.**

## Cleanup

```bash
# 1. Delete endpoint (if deployed)
aws sagemaker delete-endpoint --endpoint-name machine-overheat-endpoint --region eu-west-1

# 2. Delete project resources (S3, IAM roles)
aws cloudformation delete-stack \
  --stack-name sagemaker-overheat-project \
  --region eu-west-1

# 3. Delete SageMaker Unified Studio domain (via console)
# Navigate to https://console.aws.amazon.com/datazone
# Select domain → Actions → Delete domain
```

## Documentation

- **[Setup Guide](docs/setup.md)** - Detailed deployment instructions
- **[Student Guide](docs/student-guide.md)** - Step-by-step notebook walkthrough
- **[Architecture](docs/architecture.md)** - Technical implementation details
- **[Environment Setup](docs/env-setup.md)** - Configure .env file

## Troubleshooting

### Cannot access Unified Studio

**Issue**: "You don't have permission to access this domain"

**Solution**: Ensure you're signed in with an **IAM Identity Center user**, not an IAM role. Only SSO users can access SageMaker Unified Studio.

### Domain creation fails

**Issue**: "No VPC configured for SageMaker Unified Studio"

**Solution**: Create a VPC using the Quick setup option, or configure an existing VPC with proper subnets and security groups.

### Endpoint deployment fails

Check execution role permissions:
```bash
aws cloudformation describe-stacks \
  --stack-name sagemaker-overheat-project \
  --query 'Stacks[0].Outputs[?OutputKey==`ExecutionRoleArn`].OutputValue' \
  --output text \
  --region eu-west-1
```

## License

MIT License - Free for educational use

## Contributing

This is an educational project. Suggestions for improvements welcome via issues or pull requests.

## Next Steps

After completing this demo, students can:
1. Modify the overheat threshold (try 75°C or 85°C)
2. Add more features (time of day, machine age, maintenance history)
3. Try different models (Random Forest, XGBoost)
4. Implement A/B testing with multiple model versions
5. Add monitoring and alerting for model drift
6. Explore DataZone catalog features for data governance

---

**Ready to start?** → [Setup Guide](docs/setup.md)
