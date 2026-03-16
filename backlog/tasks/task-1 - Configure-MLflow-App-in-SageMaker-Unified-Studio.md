---
id: TASK-1
title: Configure MLflow App in SageMaker Unified Studio
status: To Do
assignee: []
created_date: '2026-03-16 18:48'
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
- [ ] #1 MLflow App is running in Unified Studio
- [ ] #2 MLFLOW_TRACKING_URI is auto-configured in JupyterLab
<!-- AC:END -->
