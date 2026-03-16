---
id: TASK-2
title: Refactor data processing notebooks into Python scripts
status: To Do
assignee: []
created_date: '2026-03-16 18:48'
labels:
  - refactor
  - scripts
dependencies:
  - TASK-1
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Objective
Convert notebooks 06_clean_data.ipynb and 07_feature_engineering.ipynb into standalone Python scripts for workflow orchestration.

## Context
SageMaker Unified Studio Workflows use Apache Airflow to orchestrate steps. Each step needs to be a Python script that can be executed independently.

## Files to Create

### scripts/clean_data.py
Extract logic from 06_clean_data.ipynb:
- Load raw CSV from S3
- Remove rows with missing temperature/room_temp
- Convert timestamp to datetime
- Sort by timestamp
- Save to S3 as Parquet

### scripts/feature_engineering.py
Extract logic from 07_feature_engineering.ipynb:
- Load cleaned Parquet from S3
- Create temp_diff = temperature - room_temp
- Create overheat = 1 if temperature > 80 else 0
- Save features to S3 as Parquet

## Script Requirements
- Accept S3 paths as arguments (argparse)
- Use boto3/pandas for S3 operations
- Include proper error handling
- Log progress to stdout
- Exit with appropriate codes (0 success, 1 failure)

## Validation
- [ ] scripts/clean_data.py runs standalone with: python scripts/clean_data.py --input s3://bucket/raw --output s3://bucket/processed
- [ ] scripts/feature_engineering.py runs standalone
- [ ] Output files match notebook outputs
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 clean_data.py accepts S3 input/output arguments
- [ ] #2 feature_engineering.py accepts S3 input/output arguments
- [ ] #3 Scripts produce identical output to notebooks
<!-- AC:END -->
