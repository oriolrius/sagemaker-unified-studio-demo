---
id: TASK-1
title: Configure MLflow App in SageMaker Unified Studio
status: Done
assignee:
  - '@claude'
created_date: '2026-03-16 18:48'
updated_date: '2026-03-17 08:51'
labels:
  - setup
  - mlflow
  - browser
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Objective
Create and configure MLflow App for experiment tracking in SageMaker Unified Studio.

## Context
SageMaker Unified Studio has native MLflow integration. The MLFLOW_TRACKING_URI environment variable is automatically injected into JupyterLab sessions when an MLflow App is configured.

## Steps (Browser-based)
1. Open SageMaker Unified Studio console
2. Navigate to your project
3. Go to **Build** > **MLflow**
4. Click **Create MLflow App** (takes ~2 minutes to provision)
5. Once created, the MLflow UI will be accessible from the Studio interface
6. Verify: Open a JupyterLab session and run `echo $MLFLOW_TRACKING_URI` - it should show the managed tracking server URI

## Validation
- [ ] MLflow App shows status "Running" in Unified Studio
- [ ] MLFLOW_TRACKING_URI environment variable is set in JupyterLab
- [ ] Can access MLflow UI from Build > MLflow menu

## References
- AWS Blog: https://aws.amazon.com/blogs/aws/accelerate-ai-development-using-amazon-sagemaker-ai-with-serverless-mlflow/
- Docs: https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/sagemaker-experiments.xml.html
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 MLflow App is running in Unified Studio
- [x] #2 MLflow tracking URI (ARN) is configured in training script and DAG
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Navigate to SageMaker Studio MLflow page\n2. Create MLflow App named 'machine-overheat-mlflow'\n3. Wait for provisioning to complete\n4. Launch JupyterLab space to verify connectivity\n5. Test MLflow tracking URI from JupyterLab terminal\n6. Update training script with correct tracking URI
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- MLflow App 'machine-overheat-mlflow' created successfully (v3.4.0)\n- ARN: arn:aws:sagemaker:eu-west-1:658203403846:mlflow-app/app-IN74ELWDTMBI\n- S3 storage: s3://sagemaker-eu-west-1-658203403846\n- IAM Role: arn:aws:iam::658203403846:role/service-role/AmazonSageMaker-ExecutionRole-20260317T072872\n- MLFLOW_TRACKING_URI is NOT auto-injected as env var in SageMaker Studio AI (different from Unified Studio)\n- However, MLflow tracking works using the ARN as tracking URI with sagemaker-mlflow plugin\n- Verified: mlflow.set_tracking_uri('arn:aws:sagemaker:eu-west-1:658203403846:mlflow-app/app-IN74ELWDTMBI') connects successfully\n- Default experiment visible, confirming full connectivity
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Created and configured MLflow App 'machine-overheat-mlflow' (v3.4.0) in SageMaker Studio AI.\n\nKey findings:\n- MLflow App ARN: arn:aws:sagemaker:eu-west-1:658203403846:mlflow-app/app-IN74ELWDTMBI\n- In SageMaker Studio AI, MLFLOW_TRACKING_URI is NOT auto-injected as an env var (unlike Unified Studio). The ARN must be passed explicitly to scripts.\n- The sagemaker-mlflow plugin allows using the ARN directly as a tracking URI.\n\nChanges:\n- Updated scripts/train_model.py: added --tracking-uri CLI argument that accepts MLflow App ARN\n- Updated workflows/machine_overheat_dag.py: added MLFLOW_TRACKING_URI config (from Airflow Variable, env var, or hardcoded ARN fallback) and passes it to train_model.py\n\nVerification:\n- MLflow App running and accessible from Studio MLflow page\n- Confirmed connectivity from JupyterLab terminal: mlflow.search_experiments() returns ['Default']\n- Screenshots saved: mlflow-app-created.png, mlflow-tracking-test.png
<!-- SECTION:FINAL_SUMMARY:END -->
