# PRD: SageMaker Unified Studio Workflow Scripts

## Introduction

Refactor Jupyter notebooks into standalone Python scripts and create an Apache Airflow DAG for SageMaker Unified Studio Workflow orchestration. This covers:
- Data processing scripts (from notebooks 06, 07)
- Training script with MLflow integration (from notebook 09)
- Airflow DAG for pipeline orchestration

## Goals

- Create `scripts/clean_data.py` replicating notebook 06 logic
- Create `scripts/feature_engineering.py` replicating notebook 07 logic
- Create `scripts/train_model.py` with MLflow integration (notebook 09)
- Create `workflows/machine_overheat_dag.py` Airflow DAG
- Scripts work in SageMaker Processing Jobs (containerized)
- Support IAM role credentials with .env fallback
- Output structured JSON logs for CloudWatch
- Scripts are idempotent (overwrite existing outputs)

## User Stories

### Phase 1: Infrastructure (US-001 to US-003)

#### US-001: Create scripts directory structure
**Description:** As a developer, I need a proper directory structure.

**Acceptance Criteria:**
- [ ] Create `scripts/` directory
- [ ] Create `scripts/__init__.py`
- [ ] Create `scripts/utils.py` placeholder

---

#### US-002: Implement structured JSON logging utility
**Description:** As an operator, I want structured JSON logs for CloudWatch.

**Acceptance Criteria:**
- [ ] Create `log_json()` in `scripts/utils.py`
- [ ] Format: `{"timestamp": "ISO8601", "level": "INFO|ERROR", "message": "...", "extra": {}}`
- [ ] Support script_name, step, duration_ms fields
- [ ] Output to stdout

---

#### US-003: Implement S3 credential fallback utility
**Description:** As a developer, I want scripts to work in SageMaker and locally.

**Acceptance Criteria:**
- [ ] Create `get_bucket_name()` in `scripts/utils.py`
- [ ] Try `os.environ.get('BUCKET_NAME')` first
- [ ] Fallback to `.env` file via python-dotenv
- [ ] Raise ValueError if not found

---

### Phase 2: Data Processing Scripts (US-004 to US-006)

#### US-004: Create clean_data.py script
**Description:** Standalone script to clean raw machine data.

**Acceptance Criteria:**
- [ ] argparse: `--input-path`, `--output-path`
- [ ] Load CSV, dropna on temperature/room_temp
- [ ] Convert timestamp to datetime, sort
- [ ] Save as Parquet
- [ ] Log rows processed, exit 0/1

**Source:** `06_clean_data.ipynb`

---

#### US-005: Create feature_engineering.py script
**Description:** Standalone script to create ML features.

**Acceptance Criteria:**
- [ ] argparse: `--input-path`, `--output-path`
- [ ] Load Parquet
- [ ] Create `temp_diff = temperature - room_temp`
- [ ] Create `overheat = 1 if temperature > 80 else 0`
- [ ] Select columns, save as Parquet
- [ ] Log stats, exit 0/1

**Source:** `07_feature_engineering.ipynb`

---

#### US-006: Add error handling to data scripts
**Description:** Clear error messages for debugging.

**Acceptance Criteria:**
- [ ] try/except in clean_data.py and feature_engineering.py
- [ ] Log errors with traceback
- [ ] Validate columns exist
- [ ] Exit 1 on failure

---

### Phase 3: Training Script (US-007 to US-009)

#### US-007: Create requirements.txt
**Description:** Document dependencies.

**Acceptance Criteria:**
- [ ] Create `scripts/requirements.txt`
- [ ] pandas>=2.0.0, pyarrow>=12.0.0, boto3>=1.28.0
- [ ] python-dotenv>=1.0.0, s3fs>=2023.6.0
- [ ] scikit-learn>=1.3.0, mlflow>=2.8.0

---

#### US-008: Create train_model.py with MLflow
**Description:** Training script with experiment tracking.

**Acceptance Criteria:**
- [ ] argparse: `--input-path`, `--model-output`, `--experiment-name`, `--test-size`
- [ ] NO mlflow.set_tracking_uri() (auto-injected in Unified Studio)
- [ ] mlflow.set_experiment(experiment_name)
- [ ] Load features, train_test_split with stratify
- [ ] Train LogisticRegression
- [ ] Log params: model_type, test_size, random_state
- [ ] Log metrics: accuracy, precision, recall, f1_score
- [ ] mlflow.sklearn.log_model()
- [ ] Save model with joblib
- [ ] Exit 0/1

**Source:** `09_mlflow_tracking.ipynb`

---

#### US-009: Add error handling to train_model.py
**Description:** Error handling for training.

**Acceptance Criteria:**
- [ ] try/except, log errors with traceback
- [ ] Validate input columns
- [ ] Warn if accuracy < 85%
- [ ] Exit 1 on failure

---

### Phase 4: Airflow DAG (US-010 to US-012)

#### US-010: Create workflows directory
**Description:** Directory structure for DAGs.

**Acceptance Criteria:**
- [ ] Create `workflows/` directory
- [ ] Create `workflows/__init__.py`

---

#### US-011: Create Airflow DAG
**Description:** DAG to orchestrate ML pipeline.

**Acceptance Criteria:**
- [ ] Create `workflows/machine_overheat_dag.py`
- [ ] DAG: `machine_overheat_pipeline`, schedule=None, catchup=False
- [ ] Tasks: clean_data → feature_engineering → train_model
- [ ] Use subprocess.run() to execute scripts
- [ ] Set task dependencies

---

#### US-012: Add DAG configuration
**Description:** Configurable S3 paths.

**Acceptance Criteria:**
- [ ] Define S3_BUCKET variable (env or Airflow Variable)
- [ ] Define path variables: RAW_DATA, CLEAN_DATA, FEATURES, MODEL
- [ ] Pass paths to script arguments
- [ ] Document configuration

---

## Non-Goals (Browser Tasks - Not in Ralph)

These tasks require manual browser interaction in AWS Console:
- **TASK-1:** Configure MLflow App in Unified Studio
- **TASK-4 (partial):** Visual Workflow Builder setup
- **TASK-5:** Validate end-to-end execution

## Technical Considerations

- **Environment:** Python 3.9+, SageMaker sklearn container
- **MLflow:** MLFLOW_TRACKING_URI auto-injected in Unified Studio
- **S3:** pandas reads S3 URIs directly via s3fs
- **Airflow:** Amazon MWAA in Unified Studio

## Source Notebooks

### 06_clean_data.ipynb
```python
df = pd.read_csv(s3_path)
df_clean = df.dropna(subset=['temperature', 'room_temp'])
df_clean['timestamp'] = pd.to_datetime(df_clean['timestamp'])
df_clean = df_clean.sort_values('timestamp').reset_index(drop=True)
df_clean.to_parquet(output_path, index=False)
```

### 07_feature_engineering.ipynb
```python
df = pd.read_parquet(s3_path)
df['temp_diff'] = df['temperature'] - df['room_temp']
df['overheat'] = (df['temperature'] > 80).astype(int)
df_final = df[['temperature', 'temp_diff', 'overheat']]
df_final.to_parquet(output_path, index=False)
```

### 09_mlflow_tracking.ipynb
```python
mlflow.set_experiment("machine-overheat")
X = df[['temperature', 'temp_diff']]
y = df['overheat']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y)

with mlflow.start_run():
    mlflow.log_param("model_type", "LogisticRegression")
    model = LogisticRegression(random_state=42, max_iter=1000)
    model.fit(X_train, y_train)
    mlflow.log_metric("accuracy", accuracy_score(y_test, model.predict(X_test)))
    mlflow.sklearn.log_model(model, "model")
```
