# Architecture Guide: Technical Implementation Details

This document explains the technical architecture and implementation details of the machine overheat prediction demo.

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         AWS Cloud                            │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │           SageMaker Unified Studio                  │    │
│  │                                                     │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────┐ │    │
│  │  │  JupyterLab  │  │   MLflow     │  │  Model  │ │    │
│  │  │  Notebooks   │  │  Tracking    │  │ Registry│ │    │
│  │  └──────────────┘  └──────────────┘  └─────────┘ │    │
│  │                                                     │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────┐ │    │
│  │  │  Training    │  │  Processing  │  │Pipeline │ │    │
│  │  │    Jobs      │  │     Jobs     │  │ Executor│ │    │
│  │  └──────────────┘  └──────────────┘  └─────────┘ │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                 │
│                           ▼                                 │
│  ┌────────────────────────────────────────────────────┐    │
│  │                  S3 Data Lake                       │    │
│  │                                                     │    │
│  │  /data/raw/          /data/processed/              │    │
│  │  machines.csv        clean_machines.parquet        │    │
│  │                                                     │    │
│  │  /data/features/     /models/                      │    │
│  │  features.parquet    model.pkl                     │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                 │
│                           ▼                                 │
│  ┌────────────────────────────────────────────────────┐    │
│  │            SageMaker Inference Endpoint             │    │
│  │                                                     │    │
│  │  ┌──────────────────────────────────────────────┐ │    │
│  │  │  REST API (ml.t2.medium)                     │ │    │
│  │  │  POST /invocations                           │ │    │
│  │  │  {"temperature": 78, "room_temp": 25}        │ │    │
│  │  │  → {"prediction": 0, "probability": 0.34}    │ │    │
│  │  └──────────────────────────────────────────────┘ │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Infrastructure Components

### 1. SageMaker Domain

**Resource**: `AWS::SageMaker::Domain`

The domain is the top-level container for all SageMaker Studio resources.

**Key configurations**:
- **VPC Mode**: `VpcOnly` for network isolation
- **Auth Mode**: `IAM` for AWS credential-based access
- **Default execution role**: Attached to all jobs

**CloudFormation snippet**:
```yaml
SageMakerDomain:
  Type: AWS::SageMaker::Domain
  Properties:
    DomainName: !Ref DomainName
    AuthMode: IAM
    DefaultUserSettings:
      ExecutionRole: !GetAtt SageMakerExecutionRole.Arn
      JupyterServerAppSettings:
        DefaultResourceSpec:
          InstanceType: ml.t3.medium
          SageMakerImageArn: !Sub 'arn:aws:sagemaker:${AWS::Region}:${AWS::AccountId}:image/datascience-1.0'
    VpcId: !Ref VPC
    SubnetIds:
      - !Ref PrivateSubnet1
      - !Ref PrivateSubnet2
```

### 2. User Profile

**Resource**: `AWS::SageMaker::UserProfile`

Each student gets a user profile with isolated resources.

**Key configurations**:
- **Execution role**: Permissions for S3, training, endpoints
- **Storage**: EFS volume for persistent notebooks
- **Instance types**: Configurable compute resources

**CloudFormation snippet**:
```yaml
UserProfile:
  Type: AWS::SageMaker::UserProfile
  Properties:
    DomainId: !GetAtt SageMakerDomain.DomainId
    UserProfileName: !Ref UserProfileName
    UserSettings:
      ExecutionRole: !GetAtt SageMakerExecutionRole.Arn
```

### 3. S3 Data Bucket

**Resource**: `AWS::S3::Bucket`

Centralized data lake for all ML artifacts.

**Directory structure**:
```
s3://sagemaker-overheat-demo-xxx/
├── data/
│   ├── raw/
│   │   └── machines.csv                 # Original data
│   ├── processed/
│   │   └── clean_machines.parquet       # Cleaned data
│   └── features/
│       ├── features.parquet             # Training features
│       ├── test_features.parquet        # Test features
│       └── test_labels.parquet          # Test labels
├── models/
│   └── logistic_regression/
│       ├── model.pkl                    # Trained model
│       └── metadata.json                # Model metadata
├── mlflow/
│   └── experiments/
│       └── machine-overheat/            # MLflow artifacts
└── pipelines/
    └── machine-overheat-pipeline/       # Pipeline definitions
```

**Key configurations**:
- **Versioning**: Enabled for data lineage
- **Encryption**: SSE-S3 for data at rest
- **Lifecycle policies**: Archive old data to Glacier

**CloudFormation snippet**:
```yaml
DataBucket:
  Type: AWS::S3::Bucket
  Properties:
    BucketName: !Sub 'sagemaker-overheat-demo-${AWS::AccountId}'
    VersioningConfiguration:
      Status: Enabled
    BucketEncryption:
      ServerSideEncryptionConfiguration:
        - ServerSideEncryptionByDefault:
            SSEAlgorithm: AES256
    PublicAccessBlockConfiguration:
      BlockPublicAcls: true
      BlockPublicPolicy: true
      IgnorePublicAcls: true
      RestrictPublicBuckets: true
```

### 4. IAM Execution Role

**Resource**: `AWS::IAM::Role`

Grants SageMaker jobs permissions to access AWS resources.

**Permissions**:
- **S3**: Read/write to data bucket
- **SageMaker**: Create training jobs, endpoints, models
- **CloudWatch**: Write logs
- **ECR**: Pull container images

**CloudFormation snippet**:
```yaml
SageMakerExecutionRole:
  Type: AWS::IAM::Role
  Properties:
    AssumeRolePolicyDocument:
      Version: '2012-10-17'
      Statement:
        - Effect: Allow
          Principal:
            Service:
              - sagemaker.amazonaws.com
          Action: 'sts:AssumeRole'
    ManagedPolicyArns:
      - arn:aws:iam::aws:policy/AmazonSageMakerFullAccess
    Policies:
      - PolicyName: S3Access
        PolicyDocument:
          Version: '2012-10-17'
          Statement:
            - Effect: Allow
              Action:
                - 's3:GetObject'
                - 's3:PutObject'
                - 's3:DeleteObject'
                - 's3:ListBucket'
              Resource:
                - !Sub '${DataBucket.Arn}/*'
                - !GetAtt DataBucket.Arn
```

## ML Workflow Architecture

### Data Flow

```
1. Data Ingestion
   ├── Local: scripts/generate_data.py
   ├── Output: data/machines.csv
   └── Upload: aws s3 cp → s3://bucket/data/raw/

2. Data Exploration
   ├── Notebook: 01_explore_data.ipynb
   ├── Read: pd.read_csv('s3://bucket/data/raw/machines.csv')
   └── Output: EDA visualizations

3. Data Cleaning
   ├── Notebook: 02_clean_data.ipynb
   ├── Operations: dropna(), to_datetime(), sort_values()
   └── Output: s3://bucket/data/processed/clean_machines.parquet

4. Feature Engineering
   ├── Notebook: 03_feature_engineering.ipynb
   ├── Transform: temp_diff = temperature - room_temp
   ├── Label: overheat = temperature > 80
   └── Output: s3://bucket/data/features/features.parquet

5. Model Training
   ├── Notebook: 04_train_model.ipynb
   ├── Algorithm: LogisticRegression()
   ├── Evaluation: accuracy_score()
   └── Output: s3://bucket/models/logistic_regression/model.pkl

6. Experiment Tracking
   ├── Notebook: 05_mlflow_tracking.ipynb
   ├── MLflow: log_param(), log_metric(), log_model()
   └── Storage: s3://bucket/mlflow/experiments/

7. Model Registry
   ├── Notebook: 06_model_registry.ipynb
   ├── Register: sklearn_model.register()
   └── Storage: SageMaker Model Registry

8. Model Validation
   ├── Notebook: 07_validate_model.ipynb
   ├── Checks: accuracy > 0.85, no data leakage
   └── Output: Validation report

9. Endpoint Deployment
   ├── Notebook: 08_deploy_endpoint.ipynb
   ├── Deploy: sklearn_model.deploy()
   └── Endpoint: machine-overheat-endpoint (ml.t2.medium)

10. Pipeline Orchestration
    ├── Script: scripts/create_pipeline.py
    ├── Pipeline: SageMaker Pipelines
    └── Automation: Steps 3-9 automated
```

## Model Architecture

### Logistic Regression

**Why this model?**
- **Interpretable**: Students can understand coefficients
- **Fast**: Trains in seconds
- **Effective**: 90-95% accuracy for this problem
- **Probabilistic**: Outputs confidence scores

**Mathematical formulation**:

```
P(overheat = 1) = 1 / (1 + e^-(β₀ + β₁·temperature + β₂·temp_diff))

where:
  β₀ = intercept
  β₁ = coefficient for temperature
  β₂ = coefficient for temp_diff
```

**Feature importance**:

Typical learned coefficients:
```
β₀ (intercept):     -15.2
β₁ (temperature):    0.18
β₂ (temp_diff):      0.12
```

**Interpretation**:
- Higher temperature → higher overheat probability
- Higher temp_diff → higher overheat probability
- Both features contribute to the prediction

### Training Configuration

```python
from sklearn.linear_model import LogisticRegression

model = LogisticRegression(
    random_state=42,        # Reproducibility
    max_iter=1000,          # Convergence
    solver='lbfgs',         # Optimization algorithm
    class_weight='balanced' # Handle class imbalance
)
```

### Evaluation Metrics

**Primary metric**: Accuracy
```
Accuracy = (TP + TN) / (TP + TN + FP + FN)
```

**Additional metrics**:
- **Precision**: Of predicted overheats, how many were correct?
- **Recall**: Of actual overheats, how many did we catch?
- **F1-score**: Harmonic mean of precision and recall

**Confusion matrix**:
```
                Predicted
                No    Yes
Actual  No    [1800   20]
        Yes   [ 15   165]
```

## Inference Architecture

### Endpoint Configuration

**Instance type**: `ml.t2.medium`
- 2 vCPUs
- 4 GB RAM
- $0.05/hour

**Scaling**:
- Initial instances: 1
- Auto-scaling: Disabled (demo purposes)
- Production: Enable auto-scaling based on invocations/minute

### Inference Pipeline

```
1. Client Request
   POST /invocations
   Content-Type: application/json
   {
     "temperature": 78,
     "room_temp": 25
   }

2. Input Processing (input_fn)
   ├── Parse JSON
   ├── Calculate temp_diff = 78 - 25 = 53
   └── Create feature array: [[78, 53]]

3. Prediction (predict_fn)
   ├── Load model from /opt/ml/model/
   ├── model.predict([[78, 53]]) → 0
   └── model.predict_proba([[78, 53]]) → [0.66, 0.34]

4. Output Formatting (output_fn)
   └── Return JSON:
       {
         "prediction": 0,
         "probability": 0.34
       }

5. Client Response
   HTTP 200 OK
   Content-Type: application/json
```

### Inference Script Structure

**File**: `inference.py`

```python
# Model loading (called once at startup)
def model_fn(model_dir):
    """Load pickled model from S3"""
    return joblib.load(f"{model_dir}/model.pkl")

# Input parsing (called per request)
def input_fn(request_body, content_type):
    """Parse JSON and create feature array"""
    data = json.loads(request_body)
    temp = data['temperature']
    room_temp = data['room_temp']
    temp_diff = temp - room_temp
    return np.array([[temp, temp_diff]])

# Prediction (called per request)
def predict_fn(input_data, model):
    """Run inference"""
    prediction = model.predict(input_data)[0]
    probability = model.predict_proba(input_data)[0][1]
    return {'prediction': int(prediction), 'probability': float(probability)}

# Output formatting (called per request)
def output_fn(prediction, accept):
    """Format response"""
    return json.dumps(prediction), accept
```

## Pipeline Architecture

### SageMaker Pipelines

**Purpose**: Automate the entire ML workflow for reproducibility and production deployment.

**Pipeline definition**:

```python
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ProcessingStep, TrainingStep
from sagemaker.workflow.conditions import ConditionGreaterThanOrEqualTo
from sagemaker.workflow.condition_step import ConditionStep

# Step 1: Data processing
processing_step = ProcessingStep(
    name="DataProcessing",
    processor=sklearn_processor,
    code="scripts/preprocess.py",
    inputs=[
        ProcessingInput(source=s3_raw_data, destination="/opt/ml/processing/input")
    ],
    outputs=[
        ProcessingOutput(source="/opt/ml/processing/output", destination=s3_processed_data)
    ]
)

# Step 2: Model training
training_step = TrainingStep(
    name="TrainModel",
    estimator=sklearn_estimator,
    inputs={
        "train": TrainingInput(s3_data=s3_processed_data)
    }
)

# Step 3: Model evaluation
evaluation_step = ProcessingStep(
    name="EvaluateModel",
    processor=sklearn_processor,
    code="scripts/evaluate.py",
    inputs=[
        ProcessingInput(source=training_step.properties.ModelArtifacts.S3ModelArtifacts)
    ],
    outputs=[
        ProcessingOutput(source="/opt/ml/processing/evaluation", destination=s3_evaluation)
    ]
)

# Step 4: Conditional model registration
condition = ConditionGreaterThanOrEqualTo(
    left=JsonGet(step=evaluation_step, property_file="evaluation.json", json_path="accuracy"),
    right=0.85
)

register_step = ConditionStep(
    name="CheckAccuracy",
    conditions=[condition],
    if_steps=[
        RegisterModel(
            name="RegisterModel",
            model_data=training_step.properties.ModelArtifacts.S3ModelArtifacts,
            model_package_group_name="machine-overheat-models"
        )
    ],
    else_steps=[]
)

# Create pipeline
pipeline = Pipeline(
    name="machine-overheat-pipeline",
    steps=[processing_step, training_step, evaluation_step, register_step]
)
```

### Pipeline Execution

```bash
# Create/update pipeline
pipeline.upsert(role_arn=execution_role)

# Start execution
execution = pipeline.start()

# Monitor progress
execution.wait()

# View results
execution.list_steps()
```

## Cost Optimization

### Development Environment

**Notebook instances**:
- Use `ml.t3.medium` ($0.05/hour) for development
- Stop instances when not in use
- Use lifecycle configurations to auto-stop

**Training jobs**:
- Use `ml.m5.large` ($0.115/hour) for small datasets
- Spot instances: 70% cost savings
- Training time: ~5 minutes = $0.01 per run

**Endpoints**:
- Use `ml.t2.medium` ($0.05/hour) for demos
- Delete endpoints after class
- Use serverless inference for low-traffic production

### Production Environment

**Recommendations**:
- **Auto-scaling**: Scale endpoints based on traffic
- **Batch transform**: For offline predictions (cheaper than endpoints)
- **Model monitoring**: Detect drift early to avoid retraining costs
- **Data lifecycle**: Archive old data to S3 Glacier

## Security Considerations

### Network Isolation

**VPC configuration**:
- SageMaker domain in private subnets
- No direct internet access
- VPC endpoints for S3, SageMaker API

### Data Encryption

**At rest**:
- S3: SSE-S3 encryption
- EFS: Encrypted volumes for notebooks
- Model artifacts: Encrypted in S3

**In transit**:
- HTTPS for all API calls
- TLS 1.2+ for endpoint invocations

### Access Control

**IAM policies**:
- Least privilege principle
- Separate roles for students, instructors, production
- Resource-based policies on S3 buckets

**SageMaker Studio**:
- IAM authentication
- User profiles for isolation
- Execution roles scoped to specific resources

## Monitoring and Logging

### CloudWatch Logs

**Log groups**:
- `/aws/sagemaker/TrainingJobs` - Training job logs
- `/aws/sagemaker/Endpoints/<endpoint-name>` - Inference logs
- `/aws/sagemaker/ProcessingJobs` - Processing job logs

**Useful queries**:

```bash
# View training logs
aws logs tail /aws/sagemaker/TrainingJobs --follow

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/sagemaker/Endpoints/machine-overheat-endpoint \
  --filter-pattern "ERROR"
```

### CloudWatch Metrics

**Key metrics**:
- `ModelLatency` - Inference response time
- `Invocations` - Number of predictions
- `ModelSetupTime` - Cold start time
- `CPUUtilization` - Instance utilization

**Alarms**:

```yaml
HighLatencyAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    MetricName: ModelLatency
    Namespace: AWS/SageMaker
    Statistic: Average
    Period: 300
    EvaluationPeriods: 2
    Threshold: 1000  # 1 second
    ComparisonOperator: GreaterThanThreshold
```

## Scalability

### Horizontal Scaling

**Endpoints**:
- Add more instances for higher throughput
- Auto-scaling based on `InvocationsPerInstance`

**Training**:
- Distributed training for large datasets
- Multiple training jobs in parallel

### Vertical Scaling

**Instance types**:
- Start with `ml.t3.medium` for development
- Scale to `ml.m5.xlarge` for production
- Use GPU instances (`ml.p3.2xlarge`) for deep learning

## Extensibility

### Adding New Features

1. Modify `03_feature_engineering.ipynb`
2. Update `inference.py` to calculate new features
3. Retrain model with new feature set
4. Register new model version
5. Deploy to new endpoint for A/B testing

### Adding New Models

1. Create new training notebook (e.g., `04b_train_random_forest.ipynb`)
2. Train alternative model
3. Register in model registry with different name
4. Deploy to separate endpoint
5. Compare performance metrics

### Multi-Model Endpoints

Deploy multiple models to a single endpoint:

```python
from sagemaker.multidatamodel import MultiDataModel

mdm = MultiDataModel(
    name="multi-model-endpoint",
    model_data_prefix=f"s3://{bucket}/models/",
    role=execution_role
)

mdm.deploy(
    initial_instance_count=1,
    instance_type='ml.m5.large'
)

# Invoke specific model
response = mdm.predict(
    data={"temperature": 78, "room_temp": 25},
    target_model="logistic_regression/model.tar.gz"
)
```

## References

- [SageMaker Developer Guide](https://docs.aws.amazon.com/sagemaker/latest/dg/)
- [SageMaker Python SDK](https://sagemaker.readthedocs.io/)
- [SageMaker Pipelines](https://docs.aws.amazon.com/sagemaker/latest/dg/pipelines.html)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
