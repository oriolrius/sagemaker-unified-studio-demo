---
id: TASK-4
title: Create SageMaker Unified Studio Workflow
status: To Do
assignee: []
created_date: '2026-03-16 18:48'
labels:
  - workflow
  - airflow
  - browser
dependencies:
  - TASK-2
  - TASK-3
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Objective
Create an Apache Airflow workflow in SageMaker Unified Studio to orchestrate the ML pipeline.

## Context
SageMaker Unified Studio uses Amazon MWAA (Managed Workflows for Apache Airflow) for workflow orchestration. You can create workflows via:
- **Visual Workflow Builder** (low-code, browser-based)
- **Code Workflows** (Python Airflow DAGs)

## Option A: Visual Workflow Builder (Recommended for learning)

### Steps (Browser-based)
1. Open SageMaker Unified Studio > **Workflows**
2. Click **Create workflow** > **Visual workflow**
3. Add steps by dragging components:
   - **Step 1**: Python script - clean_data.py
   - **Step 2**: Python script - feature_engineering.py  
   - **Step 3**: Python script - train_model.py
4. Connect steps with arrows (Step 1 → Step 2 → Step 3)
5. Configure each step:
   - Script location: Point to scripts/ directory
   - Environment: Select Python 3.9+
   - Resources: 2 vCPU, 4GB memory minimum
6. Save workflow as "machine-overheat-pipeline"

## Option B: Code Workflow (Airflow DAG)

### File to Create: workflows/machine_overheat_dag.py

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.operators.sagemaker import SageMakerProcessingOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "ml-team",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "machine_overheat_pipeline",
    default_args=default_args,
    description="ML pipeline for machine overheat prediction",
    schedule_interval=None,  # Manual trigger
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["ml", "overheat"],
) as dag:
    
    clean_data = PythonOperator(
        task_id="clean_data",
        python_callable=lambda: exec(open("scripts/clean_data.py").read()),
    )
    
    feature_engineering = PythonOperator(
        task_id="feature_engineering",
        python_callable=lambda: exec(open("scripts/feature_engineering.py").read()),
    )
    
    train_model = PythonOperator(
        task_id="train_model",
        python_callable=lambda: exec(open("scripts/train_model.py").read()),
    )
    
    clean_data >> feature_engineering >> train_model
```

### Upload DAG
1. Go to **Workflows** > **Code workflows**
2. Upload the DAG file
3. Wait for Airflow to parse and register it

## Prerequisites
- Workflows require instance with **4GB+ memory and 4+ vCPUs**
- Scripts must be uploaded to project storage

## References
- Docs: https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/workflow-orchestration.html
- Blog: https://aws.amazon.com/blogs/big-data/use-apache-airflow-workflows-to-orchestrate-data-processing-on-amazon-sagemaker-unified-studio/
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Workflow created in SageMaker Unified Studio
- [ ] #2 All three steps (clean, features, train) connected in sequence
- [ ] #3 Workflow can be triggered manually
<!-- AC:END -->
