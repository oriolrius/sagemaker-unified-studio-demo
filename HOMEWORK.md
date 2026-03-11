# Homework: ML Pipeline Automation with SageMaker Pipelines

Automate the ML workflow using SageMaker Pipelines in SageMaker Unified Studio.

---

> **IMPORTANT: CLEANUP WHEN FINISHED**
>
> Pipeline executions create Processing Jobs and Training Jobs that incur costs.
>
> ```bash
> aws sagemaker delete-endpoint --endpoint-name machine-overheat-endpoint --region eu-west-1
> aws sagemaker delete-pipeline --pipeline-name machine-overheat-pipeline --region eu-west-1
> ```
>
> **Cost estimate: ~$2-3 for the entire homework**

---

## Why Does the Pipeline Take Longer Than Notebooks?

In the notebooks, training takes **seconds** because it runs locally in your JupyterLab kernel.

In SageMaker Pipelines, each step:
1. Spins up a NEW EC2 instance (ml.m5.large)
2. Pulls the Docker container image
3. Downloads data from S3
4. Runs your code (still seconds!)
5. Uploads results to S3
6. Shuts down the instance

**The actual training is still seconds.** The ~15-20 minutes is AWS infrastructure overhead (provisioning instances, transferring data). This is the tradeoff of managed, scalable pipelines vs. local execution.

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
    df = pd.read_csv('/opt/ml/processing/input/machines.csv')

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.dropna()

    df['temp_diff'] = df['temperature'] - df['room_temp']
    df['overheat'] = (df['temperature'] > 80).astype(int)

    train, test = train_test_split(df, test_size=0.2, random_state=42)

    os.makedirs('/opt/ml/processing/output/train', exist_ok=True)
    os.makedirs('/opt/ml/processing/output/test', exist_ok=True)

    train.to_csv('/opt/ml/processing/output/train/train.csv', index=False)
    test.to_csv('/opt/ml/processing/output/test/test.csv', index=False)

    print(f"Training samples: {len(train)}, Test samples: {len(test)}")
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
    train_df = pd.read_csv('/opt/ml/input/data/train/train.csv')

    X_train = train_df[['temperature', 'temp_diff']]
    y_train = train_df['overheat']

    model = LogisticRegression(random_state=42, max_iter=1000)
    model.fit(X_train, y_train)

    print(f"Training accuracy: {model.score(X_train, y_train):.4f}")

    os.makedirs('/opt/ml/model', exist_ok=True)
    joblib.dump(model, '/opt/ml/model/model.joblib')
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
    with tarfile.open('/opt/ml/processing/model/model.tar.gz', 'r:gz') as tar:
        tar.extractall('/opt/ml/processing/model/')

    model = joblib.load('/opt/ml/processing/model/model.joblib')

    test_df = pd.read_csv('/opt/ml/processing/test/test.csv')
    X_test = test_df[['temperature', 'temp_diff']]
    y_test = test_df['overheat']

    y_pred = model.predict(X_test)

    metrics = {
        "metrics": {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "precision": float(precision_score(y_test, y_pred)),
            "recall": float(recall_score(y_test, y_pred)),
            "f1": float(f1_score(y_test, y_pred))
        }
    }

    print(f"Metrics: {json.dumps(metrics, indent=2)}")

    os.makedirs('/opt/ml/processing/evaluation', exist_ok=True)
    with open('/opt/ml/processing/evaluation/evaluation.json', 'w') as f:
        json.dump(metrics, f)
```

---

## Step 5: Create Pipeline Notebook

Create `14_create_pipeline.ipynb`. The complete code is provided in the appendix below.

Key cells:
1. **Imports** - SageMaker Pipeline SDK
2. **Configuration** - Load bucket/region from `.env`
3. **ProcessingStep** - Data preprocessing
4. **TrainingStep** - Model training
5. **EvaluationStep** - Model evaluation with PropertyFile
6. **ConditionStep** - Register model only if accuracy ≥ 85%
7. **Pipeline creation and execution**

---

## Step 6: Run the Pipeline

1. Run all cells in the notebook
2. Go to **SageMaker Console → Pipelines** to monitor execution
3. View the pipeline DAG visualization
4. Wait for completion (~15-20 min due to infrastructure overhead)

---

## Step 7: Test Failure Scenario

Modify the condition threshold to 99%:

```python
condition = ConditionGreaterThanOrEqualTo(
    left=JsonGet(...),
    right=0.99,  # Model won't meet 99% accuracy
)
```

Re-run and observe:
- ConditionStep shows condition NOT met
- RegisterModel step is skipped

---

## Step 8: Restore and Verify

Change threshold back to `0.85` and confirm the pipeline works correctly.

---

## Deliverable: PDF Report

Submit a **single PDF document** named `homework_pipeline_YOURNAME.pdf` with the following chapters:

### Chapter 1: Pipeline Overview (1 page)

- Brief description of what your pipeline does
- Screenshot of the **Pipeline DAG** from SageMaker Console
- Explanation of each step's purpose

### Chapter 2: Scripts Implementation (2-3 pages)

- Screenshot of your `scripts/` folder in JupyterLab
- For each script (`preprocess.py`, `train.py`, `evaluate.py`):
  - Screenshot of the code
  - Brief explanation of what it does

### Chapter 3: Pipeline Notebook (2-3 pages)

- Screenshots of key cells in `14_create_pipeline.ipynb`:
  - Pipeline definition (steps)
  - Condition logic
  - Pipeline execution output
- Explanation of how steps are connected

### Chapter 4: Successful Execution (1-2 pages)

- Screenshot of **pipeline execution with all steps green** (threshold=0.85)
- Screenshot of the **registered model** in Model Registry
- Screenshot of **evaluation metrics** from CloudWatch logs or S3

### Chapter 5: Failed Execution (1 page)

- Screenshot of **pipeline execution with ConditionStep showing condition not met** (threshold=0.99)
- Brief explanation of why the model was NOT registered

### Chapter 6: Reflection (1 page)

Answer these questions:
1. What is the benefit of using SageMaker Pipelines vs. running notebooks manually?
2. Why does the pipeline take ~15-20 minutes when training in notebooks takes seconds?
3. How would you schedule this pipeline to run automatically every week?

---

## Grading Rubric

| Chapter | Points | Criteria |
|---------|--------|----------|
| **1. Pipeline Overview** | 15 | Clear DAG screenshot, correct step descriptions |
| **2. Scripts Implementation** | 20 | All 3 scripts shown with correct code, explanations demonstrate understanding |
| **3. Pipeline Notebook** | 20 | Key cells shown, correct pipeline definition, clear explanation of step connections |
| **4. Successful Execution** | 20 | Green pipeline screenshot, model registered, metrics visible |
| **5. Failed Execution** | 10 | Clear screenshot showing condition not met, correct explanation |
| **6. Reflection** | 15 | Thoughtful answers demonstrating understanding of pipelines vs notebooks, infrastructure overhead, scheduling concepts |

**Total: 100 points**

### Grade Scale

| Points | Grade |
|--------|-------|
| 90-100 | A |
| 80-89 | B |
| 70-79 | C |
| 60-69 | D |
| <60 | F |

---

## Troubleshooting

### "NoSuchBucket" error

Verify your `.env` file:

```python
from dotenv import load_dotenv
import os
load_dotenv()
print(os.getenv('BUCKET_NAME'))
```

### "Script not found" error

Check folder structure:

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
1. SageMaker Console → Pipelines → Your execution
2. Click failed step → "View logs"

---

## Summary

| Step | Action | Time |
|------|--------|------|
| 1-4 | Create scripts | 20 min |
| 5 | Create pipeline notebook | 30 min |
| 6 | Run pipeline (success) | 15-20 min |
| 7 | Run pipeline (failure test) | 15-20 min |
| 8 | Verify and document | 15 min |
| - | Write PDF report | 30-45 min |

**Total time: ~2-3 hours**

---

## Checklist

- [ ] Created `scripts/preprocess.py`
- [ ] Created `scripts/train.py`
- [ ] Created `scripts/evaluate.py`
- [ ] Created `14_create_pipeline.ipynb`
- [ ] Pipeline executed successfully (threshold=0.85)
- [ ] Model registered in Model Registry
- [ ] Pipeline failed as expected (threshold=0.99)
- [ ] PDF report with all 6 chapters
- [ ] **Cleaned up resources when finished**

---

## Appendix: Complete Pipeline Notebook Code

```python
# Cell 1: Imports
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

# Cell 2: Configuration
load_dotenv()
bucket = os.getenv('BUCKET_NAME')
region = os.getenv('REGION')
pipeline_session = PipelineSession()
role = sagemaker.get_execution_role()

# Cell 3: Processor
processor = SKLearnProcessor(
    framework_version="1.2-1",
    instance_type="ml.m5.large",
    instance_count=1,
    role=role,
    sagemaker_session=pipeline_session,
)

# Cell 4: Step 1 - Preprocessing
step_process = ProcessingStep(
    name="PreprocessData",
    step_args=processor.run(
        inputs=[ProcessingInput(source=f's3://{bucket}/data/raw/machines.csv',
                               destination='/opt/ml/processing/input')],
        outputs=[ProcessingOutput(output_name="train", source='/opt/ml/processing/output/train'),
                 ProcessingOutput(output_name="test", source='/opt/ml/processing/output/test')],
        code='scripts/preprocess.py',
    ),
)

# Cell 5: Step 2 - Training
estimator = SKLearn(
    entry_point='scripts/train.py',
    framework_version="1.2-1",
    instance_type="ml.m5.large",
    role=role,
    sagemaker_session=pipeline_session,
)

step_train = TrainingStep(
    name="TrainModel",
    step_args=estimator.fit(inputs={
        "train": TrainingInput(s3_data=step_process.properties.ProcessingOutputConfig.Outputs["train"].S3Output.S3Uri)
    }),
)

# Cell 6: Step 3 - Evaluation
eval_report = PropertyFile(name="EvalReport", output_name="evaluation", path="evaluation.json")

step_eval = ProcessingStep(
    name="EvaluateModel",
    step_args=processor.run(
        inputs=[
            ProcessingInput(source=step_train.properties.ModelArtifacts.S3ModelArtifacts,
                          destination="/opt/ml/processing/model"),
            ProcessingInput(source=step_process.properties.ProcessingOutputConfig.Outputs["test"].S3Output.S3Uri,
                          destination="/opt/ml/processing/test"),
        ],
        outputs=[ProcessingOutput(output_name="evaluation", source="/opt/ml/processing/evaluation")],
        code='scripts/evaluate.py',
    ),
    property_files=[eval_report],
)

# Cell 7: Step 4 - Conditional Registration
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

condition = ConditionGreaterThanOrEqualTo(
    left=JsonGet(step_name=step_eval.name, property_file=eval_report, json_path="metrics.accuracy"),
    right=0.85,
)

step_condition = ConditionStep(
    name="CheckAccuracy",
    conditions=[condition],
    if_steps=[step_register],
    else_steps=[],
)

# Cell 8: Create and Run Pipeline
pipeline = Pipeline(
    name="machine-overheat-pipeline",
    steps=[step_process, step_train, step_eval, step_condition],
    sagemaker_session=pipeline_session,
)

pipeline.upsert(role_arn=role)
execution = pipeline.start()
print(f"Execution ARN: {execution.arn}")

# Cell 9: Wait (optional)
execution.wait()
print(f"Status: {execution.describe()['PipelineExecutionStatus']}")
```
