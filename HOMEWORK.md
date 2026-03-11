# Homework: ML Pipeline Automation with SageMaker Pipelines

Automate the ML workflow using SageMaker Pipelines in SageMaker Unified Studio.

---

> **IMPORTANT: CLEANUP WHEN FINISHED**
>
> Pipeline executions create Processing Jobs and Training Jobs that incur costs.
>
> ```bash
> # Delete the endpoint if you deployed one
> aws sagemaker delete-endpoint --endpoint-name machine-overheat-endpoint --region eu-west-1
>
> # Delete pipeline (optional - pipelines don't incur cost when idle)
> aws sagemaker delete-pipeline --pipeline-name machine-overheat-pipeline --region eu-west-1
> ```
>
> **Cost estimate: ~$2-3 per pipeline execution**

---

## Prerequisites

- Completed notebooks 01-13 from the ML demo
- Working `.env` file in JupyterLab with `BUCKET_NAME` and `REGION`
- Data uploaded to `s3://{bucket}/data/raw/machines.csv`

---

## Pipeline Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Preprocess  │────▶│   Train     │────▶│  Evaluate   │────▶│  Accuracy   │
│    Data     │     │   Model     │     │   Model     │     │   > 85%?    │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                   │
                                                          YES: Register Model
                                                          NO: Stop Pipeline
```

---

## Step 1: Create Scripts Directory

In JupyterLab, create a `scripts/` folder:

```
File → New Folder → Name it "scripts"
```

---

## Step 2: Create Preprocessing Script

Create `scripts/preprocess.py`:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
import os

if __name__ == "__main__":
    # Read input data
    df = pd.read_csv('/opt/ml/processing/input/machines.csv')

    # Clean data
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.dropna()

    # Feature engineering
    df['temp_diff'] = df['temperature'] - df['room_temp']
    df['overheat'] = (df['temperature'] > 80).astype(int)

    # Train/test split
    train, test = train_test_split(df, test_size=0.2, random_state=42)

    # Create output directories
    os.makedirs('/opt/ml/processing/output/train', exist_ok=True)
    os.makedirs('/opt/ml/processing/output/test', exist_ok=True)

    # Save outputs
    train.to_csv('/opt/ml/processing/output/train/train.csv', index=False)
    test.to_csv('/opt/ml/processing/output/test/test.csv', index=False)

    print(f"Training samples: {len(train)}")
    print(f"Test samples: {len(test)}")
```

---

## Step 3: Create Training Script

Create `scripts/train.py`:

```python
import pandas as pd
import joblib
import os
from sklearn.linear_model import LogisticRegression

if __name__ == "__main__":
    # Read training data
    train_df = pd.read_csv('/opt/ml/input/data/train/train.csv')

    X_train = train_df[['temperature', 'temp_diff']]
    y_train = train_df['overheat']

    # Train model
    model = LogisticRegression(random_state=42, max_iter=1000)
    model.fit(X_train, y_train)

    # Print training accuracy
    train_accuracy = model.score(X_train, y_train)
    print(f"Training accuracy: {train_accuracy:.4f}")

    # Save model
    os.makedirs('/opt/ml/model', exist_ok=True)
    joblib.dump(model, '/opt/ml/model/model.joblib')
    print("Model saved to /opt/ml/model/model.joblib")
```

---

## Step 4: Create Evaluation Script

Create `scripts/evaluate.py`:

```python
import pandas as pd
import joblib
import json
import tarfile
import os
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

if __name__ == "__main__":
    # Extract model from tar.gz
    model_tar_path = '/opt/ml/processing/model/model.tar.gz'
    with tarfile.open(model_tar_path, 'r:gz') as tar:
        tar.extractall('/opt/ml/processing/model/')

    # Load model
    model = joblib.load('/opt/ml/processing/model/model.joblib')

    # Load test data
    test_df = pd.read_csv('/opt/ml/processing/test/test.csv')
    X_test = test_df[['temperature', 'temp_diff']]
    y_test = test_df['overheat']

    # Evaluate
    y_pred = model.predict(X_test)

    metrics = {
        "metrics": {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "precision": float(precision_score(y_test, y_pred)),
            "recall": float(recall_score(y_test, y_pred)),
            "f1": float(f1_score(y_test, y_pred))
        }
    }

    print(f"Evaluation metrics: {json.dumps(metrics, indent=2)}")

    # Save evaluation report
    os.makedirs('/opt/ml/processing/evaluation', exist_ok=True)
    with open('/opt/ml/processing/evaluation/evaluation.json', 'w') as f:
        json.dump(metrics, f)

    print("Evaluation saved to evaluation.json")
```

---

## Step 5: Create Pipeline Notebook

Create `14_create_pipeline.ipynb` with the following cells:

### Cell 1: Imports

```python
import sagemaker
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ProcessingStep, TrainingStep
from sagemaker.workflow.properties import PropertyFile
from sagemaker.workflow.conditions import ConditionGreaterThanOrEqualTo
from sagemaker.workflow.condition_step import ConditionStep
from sagemaker.workflow.functions import JsonGet
from sagemaker.workflow.model_step import ModelStep
from sagemaker.sklearn.processing import SKLearnProcessor
from sagemaker.sklearn.estimator import SKLearn
from sagemaker.processing import ProcessingInput, ProcessingOutput
from sagemaker.inputs import TrainingInput
from sagemaker.workflow.pipeline_context import PipelineSession
from sagemaker.model import Model
from dotenv import load_dotenv
import os

print("Imports successful")
```

### Cell 2: Configuration

```python
load_dotenv()
bucket = os.getenv('BUCKET_NAME')
region = os.getenv('REGION')

pipeline_session = PipelineSession()
role = sagemaker.get_execution_role()

print(f"Bucket: {bucket}")
print(f"Region: {region}")
```

### Cell 3: Define Processor

```python
processor = SKLearnProcessor(
    framework_version="1.2-1",
    instance_type="ml.m5.large",
    instance_count=1,
    role=role,
    sagemaker_session=pipeline_session,
)
```

### Cell 4: Step 1 - Preprocessing

```python
step_process = ProcessingStep(
    name="PreprocessData",
    step_args=processor.run(
        inputs=[
            ProcessingInput(
                source=f's3://{bucket}/data/raw/machines.csv',
                destination='/opt/ml/processing/input'
            )
        ],
        outputs=[
            ProcessingOutput(output_name="train", source='/opt/ml/processing/output/train'),
            ProcessingOutput(output_name="test", source='/opt/ml/processing/output/test'),
        ],
        code='scripts/preprocess.py',
    ),
)

print("Step 1 (Preprocess) defined")
```

### Cell 5: Step 2 - Training

```python
estimator = SKLearn(
    entry_point='scripts/train.py',
    framework_version="1.2-1",
    instance_type="ml.m5.large",
    role=role,
    sagemaker_session=pipeline_session,
)

step_train = TrainingStep(
    name="TrainModel",
    step_args=estimator.fit(
        inputs={
            "train": TrainingInput(
                s3_data=step_process.properties.ProcessingOutputConfig.Outputs["train"].S3Output.S3Uri
            )
        }
    ),
)

print("Step 2 (Train) defined")
```

### Cell 6: Step 3 - Evaluation

```python
eval_report = PropertyFile(
    name="EvalReport",
    output_name="evaluation",
    path="evaluation.json"
)

step_eval = ProcessingStep(
    name="EvaluateModel",
    step_args=processor.run(
        inputs=[
            ProcessingInput(
                source=step_train.properties.ModelArtifacts.S3ModelArtifacts,
                destination="/opt/ml/processing/model"
            ),
            ProcessingInput(
                source=step_process.properties.ProcessingOutputConfig.Outputs["test"].S3Output.S3Uri,
                destination="/opt/ml/processing/test"
            ),
        ],
        outputs=[
            ProcessingOutput(output_name="evaluation", source="/opt/ml/processing/evaluation")
        ],
        code='scripts/evaluate.py',
    ),
    property_files=[eval_report],
)

print("Step 3 (Evaluate) defined")
```

### Cell 7: Step 4 - Conditional Registration

```python
model = Model(
    image_uri=estimator.image_uri,
    model_data=step_train.properties.ModelArtifacts.S3ModelArtifacts,
    sagemaker_session=pipeline_session,
    role=role,
)

step_register = ModelStep(
    name="RegisterModel",
    step_args=model.register(
        content_types=["application/json"],
        response_types=["application/json"],
        inference_instances=["ml.t2.medium"],
        model_package_group_name="overheat-model-group",
        approval_status="PendingManualApproval",
    ),
)

# Condition: Register only if accuracy >= 0.85
condition = ConditionGreaterThanOrEqualTo(
    left=JsonGet(
        step_name=step_eval.name,
        property_file=eval_report,
        json_path="metrics.accuracy"
    ),
    right=0.85,
)

step_condition = ConditionStep(
    name="CheckAccuracy",
    conditions=[condition],
    if_steps=[step_register],
    else_steps=[],
)

print("Step 4 (Condition + Register) defined")
```

### Cell 8: Create Pipeline

```python
pipeline = Pipeline(
    name="machine-overheat-pipeline",
    steps=[step_process, step_train, step_eval, step_condition],
    sagemaker_session=pipeline_session,
)

print("Pipeline created with 4 steps")
```

### Cell 9: Upload Pipeline

```python
pipeline.upsert(role_arn=role)
print("Pipeline uploaded to SageMaker")
```

### Cell 10: Start Execution

```python
execution = pipeline.start()
print(f"Pipeline execution started!")
print(f"Execution ARN: {execution.arn}")
```

### Cell 11: Wait for Completion (Optional)

```python
execution.wait()
print(f"Status: {execution.describe()['PipelineExecutionStatus']}")
```

---

## Step 6: Run the Pipeline (~15-20 min)

1. Run all cells in the notebook
2. Go to SageMaker Console → Pipelines to monitor execution
3. View the pipeline DAG visualization
4. Check each step's logs in CloudWatch

---

## Step 7: Test Failure Scenario

Modify Cell 7 to use a 99% threshold (model won't meet this):

```python
condition = ConditionGreaterThanOrEqualTo(
    left=JsonGet(
        step_name=step_eval.name,
        property_file=eval_report,
        json_path="metrics.accuracy"
    ),
    right=0.99,  # Changed from 0.85 to 0.99
)
```

Re-run the pipeline and observe:
- The ConditionStep should show the condition was NOT met
- The RegisterModel step should be skipped
- Screenshot this for your submission

---

## Step 8: Restore and Re-run

Change the threshold back to `0.85` and run the pipeline again to confirm it works correctly.

---

## Deliverables

Submit the following:

| File | Description |
|------|-------------|
| `scripts/preprocess.py` | Data preprocessing script |
| `scripts/train.py` | Model training script |
| `scripts/evaluate.py` | Model evaluation script |
| `14_create_pipeline.ipynb` | Pipeline notebook |
| `screenshot_pipeline_dag.png` | Pipeline DAG visualization |
| `screenshot_success.png` | Successful execution (threshold=0.85) |
| `screenshot_failed.png` | Failed condition (threshold=0.99) |

---

## Cost Reference

| Resource | Cost |
|----------|------|
| Processing Job (ml.m5.large) | ~$0.10/hour |
| Training Job (ml.m5.large) | ~$0.10/hour |
| Pipeline execution (~20 min) | ~$0.50-1.00 |

**Total homework cost: ~$2-3** (if you run the pipeline 2-3 times)

---

## Troubleshooting

### "NoSuchBucket" error

Verify your `.env` file has the correct bucket name:

```python
import os
from dotenv import load_dotenv
load_dotenv()
print(os.getenv('BUCKET_NAME'))
```

### "Script not found" error

Make sure scripts are in the correct location:

```
/shared/
├── scripts/
│   ├── preprocess.py
│   ├── train.py
│   └── evaluate.py
└── 14_create_pipeline.ipynb
```

### Pipeline step fails

Check CloudWatch logs:

1. Go to SageMaker Console → Pipelines
2. Click on your execution
3. Click on the failed step
4. Click "View logs" to see CloudWatch output

### "Role does not have permission" error

The execution role needs permissions for:
- S3 read/write
- SageMaker CreateProcessingJob
- SageMaker CreateTrainingJob
- SageMaker CreateModel

Ask your instructor if you see permission errors.

---

## Summary

| Step | Action | Time |
|------|--------|------|
| 1 | Create scripts directory | 1 min |
| 2 | Create preprocess.py | 5 min |
| 3 | Create train.py | 5 min |
| 4 | Create evaluate.py | 5 min |
| 5 | Create pipeline notebook | 30 min |
| 6 | Run pipeline | 15-20 min |
| 7 | Test failure scenario | 15-20 min |
| 8 | Restore and verify | 15-20 min |

**Total time: ~2-3 hours** (plus time for debugging)

---

## Checklist

- [ ] Created `scripts/preprocess.py`
- [ ] Created `scripts/train.py`
- [ ] Created `scripts/evaluate.py`
- [ ] Created `14_create_pipeline.ipynb`
- [ ] Pipeline executed successfully (threshold=0.85)
- [ ] Pipeline failed as expected (threshold=0.99)
- [ ] Took screenshots of pipeline DAG
- [ ] Took screenshots of success/failure states
- [ ] **Cleaned up resources when finished**
