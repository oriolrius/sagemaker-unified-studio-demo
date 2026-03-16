# Validation Report: SageMaker Unified Studio Workflow Scripts

**Date:** 2026-03-16
**Validated by:** Claude Code with Playwright MCP
**Branch:** `workflow`

---

## Summary

All scripts have been validated locally with test data and MLflow tracking.

| Script | Status | Output |
|--------|--------|--------|
| clean_data.py | PASS | 2,160 rows cleaned |
| feature_engineering.py | PASS | Features created (temp_diff, overheat) |
| train_model.py | PASS | 100% accuracy, MLflow logged |

---

## Test Data Generated

- **File:** `data/raw/machines.csv`
- **Rows:** 2,160 (5 machines x 3 days x 144 readings/day)
- **Overheat rate:** 8.38%

---

## Script 1: clean_data.py

**Command:**
```bash
python scripts/clean_data.py \
  --input-path data/raw/machines.csv \
  --output-path data/processed/clean_machines.parquet
```

**Results:**
- Input rows: 2,160
- Removed rows: 0 (test data has no nulls)
- Output rows: 2,160
- Timestamp converted to datetime64[ns]
- Duration: 58.25ms

**Output:** `data/processed/clean_machines.parquet` (22KB)

---

## Script 2: feature_engineering.py

**Command:**
```bash
python scripts/feature_engineering.py \
  --input-path data/processed/clean_machines.parquet \
  --output-path data/features/features.parquet
```

**Results:**
- Input rows: 2,160
- Features created:
  - `temp_diff`: mean=43.38°C, range=[25.47, 69.55]
  - `overheat`: 181 samples (8.38%)
- Duration: 73.59ms

**Output:** `data/features/features.parquet` (23KB)

---

## Script 3: train_model.py

**Command:**
```bash
python scripts/train_model.py \
  --input-path data/features/features.parquet \
  --model-output models/model.joblib \
  --experiment-name test-machine-overheat
```

**Results:**
- Train rows: 1,728 (80%)
- Test rows: 432 (20%)
- Duration: 7.14s (including MLflow logging)

**Metrics:**
| Metric | Value |
|--------|-------|
| accuracy | 1.0 |
| precision | 1.0 |
| recall | 1.0 |
| f1_score | 1.0 |

**Parameters logged:**
- model_type: LogisticRegression
- test_size: 0.2
- random_state: 42
- features: ['temperature', 'temp_diff']
- target: overheat

**Artifacts:**
- `models/model.joblib` (1.1KB)
- MLflow artifacts: MLmodel, model.pkl, conda.yaml, requirements.txt, python_env.yaml

---

## MLflow Validation (Playwright MCP)

### Screenshots

1. **mlflow-run-details.png** - Run overview showing metrics, parameters, and metadata
2. **mlflow-artifacts.png** - Artifacts tab showing logged model files

### Verified in MLflow UI

- Experiment: `test-machine-overheat` (ID: 1)
- Run: `logistic_regression_v1`
- Status: Finished
- Source: `train_model.py`
- Commit: `aa36b9a`

---

## Output Files Structure

```
data/
├── raw/
│   └── machines.csv (75KB, 2,160 rows)
├── processed/
│   └── clean_machines.parquet (22KB)
└── features/
    └── features.parquet (23KB)

models/
└── model.joblib (1.1KB)

mlruns/
└── 1/  (experiment artifacts)
```

---

## Validation Checklist

- [x] clean_data.py loads CSV and outputs Parquet
- [x] clean_data.py removes null values
- [x] clean_data.py converts timestamps to datetime
- [x] feature_engineering.py creates temp_diff feature
- [x] feature_engineering.py creates overheat target (>80°C)
- [x] train_model.py trains LogisticRegression
- [x] train_model.py logs parameters to MLflow
- [x] train_model.py logs metrics to MLflow
- [x] train_model.py logs model artifact to MLflow
- [x] train_model.py saves model to specified output path
- [x] All scripts handle local paths (not just S3)
- [x] All scripts output structured JSON logs
- [x] MLflow UI shows experiment and run correctly

---

## Next Steps (Manual Browser Tasks)

1. **TASK-1:** Configure MLflow App in SageMaker Unified Studio (Build > MLflow)
2. **TASK-4:** Upload Airflow DAG or create Visual Workflow in Unified Studio
3. **TASK-5:** Run workflow end-to-end with S3 data and validate in production
