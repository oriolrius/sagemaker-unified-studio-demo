---
id: TASK-3
title: Refactor training notebook 09 into MLflow-integrated script
status: To Do
assignee: []
created_date: '2026-03-16 18:48'
labels:
  - refactor
  - mlflow
  - training
dependencies:
  - TASK-1
  - TASK-2
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Objective
Convert 09_mlflow_tracking.ipynb into a standalone Python script that uses SageMaker Unified Studio managed MLflow.

## Context
In SageMaker Unified Studio, the MLFLOW_TRACKING_URI is automatically set. The script should NOT hardcode any tracking URI - it will be injected at runtime.

## File to Create

### scripts/train_model.py
Extract and adapt logic from 09_mlflow_tracking.ipynb:

```python
import argparse
import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-data", required=True, help="S3 path to features.parquet")
    parser.add_argument("--model-output", required=True, help="S3 path for model artifacts")
    parser.add_argument("--experiment-name", default="machine-overheat")
    parser.add_argument("--test-size", type=float, default=0.2)
    args = parser.parse_args()
    
    # MLflow tracking URI is auto-configured in Unified Studio
    # No need to call mlflow.set_tracking_uri()
    mlflow.set_experiment(args.experiment_name)
    
    # Load data, train, log metrics (same as notebook 09)
    ...
```

## Key Differences from Notebook
1. NO mlflow.set_tracking_uri() - it is auto-injected
2. Parameterized via argparse
3. S3 paths for input/output
4. Experiment name as parameter
5. Model saved to S3, also logged to MLflow

## Validation
- [ ] Script runs in SageMaker Unified Studio JupyterLab
- [ ] Experiment appears in MLflow UI (Build > MLflow)
- [ ] Metrics (accuracy, precision, recall, f1) logged correctly
- [ ] Model artifact registered in MLflow
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 train_model.py uses managed MLflow (no hardcoded tracking URI)
- [ ] #2 Script logs params, metrics, and model to MLflow
- [ ] #3 Experiment visible in Unified Studio MLflow UI
<!-- AC:END -->
