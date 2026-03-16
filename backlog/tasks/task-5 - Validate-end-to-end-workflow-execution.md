---
id: TASK-5
title: Validate end-to-end workflow execution
status: To Do
assignee: []
created_date: '2026-03-16 18:49'
labels:
  - validation
  - testing
  - browser
dependencies:
  - TASK-4
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Objective
Validate that the complete workflow executes successfully and produces correct outputs.

## Validation Steps (Browser-based)

### 1. Trigger Workflow
1. Go to **Workflows** in Unified Studio
2. Select "machine-overheat-pipeline"
3. Click **Run** (or **Trigger DAG** for code workflows)
4. Monitor execution in the workflow UI

### 2. Verify Each Step

#### Step 1: Data Cleaning
- [ ] Check S3: `s3://{bucket}/data/processed/clean_machines.parquet` exists
- [ ] Verify row count matches expected (~216K rows)
- [ ] No null values in temperature/room_temp columns

#### Step 2: Feature Engineering
- [ ] Check S3: `s3://{bucket}/data/features/features.parquet` exists
- [ ] Verify new columns: temp_diff, overheat
- [ ] overheat column has binary values (0/1)

#### Step 3: Model Training
- [ ] Check MLflow UI: New run in "machine-overheat" experiment
- [ ] Metrics logged: accuracy, precision, recall, f1_score
- [ ] Model artifact saved in MLflow
- [ ] Accuracy >= 85% threshold

### 3. Check Workflow Status
- [ ] All steps show green checkmark (success)
- [ ] No failed or skipped steps
- [ ] Execution time reasonable (< 10 minutes total)

### 4. Verify MLflow Integration
1. Go to **Build** > **MLflow**
2. Open the MLflow UI
3. Navigate to "machine-overheat" experiment
4. Verify:
   - [ ] Run parameters logged (model_type, test_size, random_state)
   - [ ] Metrics logged with correct values
   - [ ] Model artifact available for download

## Troubleshooting
- If step fails: Check Airflow logs in workflow details
- If MLflow empty: Verify MLFLOW_TRACKING_URI is set
- If S3 errors: Check IAM permissions on execution role

## Success Criteria
- Workflow completes with all steps successful
- MLflow shows experiment with metrics
- Model accuracy >= 85%
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Workflow executes all 3 steps without errors
- [ ] #2 MLflow experiment shows logged run with metrics
- [ ] #3 Model accuracy meets 85% threshold
- [ ] #4 Output files exist in correct S3 locations
<!-- AC:END -->
