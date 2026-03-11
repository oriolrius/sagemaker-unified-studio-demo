# Machine Overheating Prediction - Use Case

## Business Problem

In industrial environments, **machine overheating** is a critical issue that can lead to:

- Equipment damage and costly repairs
- Unplanned downtime affecting production
- Safety hazards for workers
- Reduced equipment lifespan

Traditional approaches rely on **reactive maintenance** (fixing machines after they fail) or **scheduled maintenance** (fixed intervals regardless of actual condition). Both approaches are inefficient and costly.

## Solution: Predictive Maintenance with ML

This project implements a **predictive maintenance** solution using machine learning to:

1. **Predict overheating before it occurs** - Alert operators when a machine is likely to overheat
2. **Enable proactive intervention** - Allow maintenance teams to act before failures happen
3. **Optimize maintenance schedules** - Service machines based on actual condition, not arbitrary schedules

## The Prediction Task

**Input**: Real-time sensor readings

- `temperature`: Current machine temperature (°C)
- `room_temp`: Ambient room temperature (°C)

**Output**: Binary classification

- `0` = Normal operation (no action needed)
- `1` = Overheating risk (requires attention)

**Threshold**: A machine is considered overheating when `temperature > 80°C`

## Why This Approach Works

The model uses two key features:

1. **Absolute temperature** - Direct indicator of machine state
2. **Temperature difference** (`temp_diff = temperature - room_temp`) - More robust indicator that accounts for environmental conditions

A machine running at 75°C in a 20°C room (diff = 55°C) is in a different state than one at 75°C in a 30°C room (diff = 45°C). The temperature difference captures the machine's actual heat generation.

## ML Pipeline Steps Explained

### Phase 1: Setup (Notebooks 01-04)

| Step                             | Purpose                                     | Why It Matters                                                          |
| -------------------------------- | ------------------------------------------- | ----------------------------------------------------------------------- |
| **01 - Setup Environment** | Create configuration file with AWS settings | Ensures all notebooks use consistent bucket/region settings             |
| **02 - Create S3 Bucket**  | Provision cloud storage                     | Centralized data lake for raw data, processed data, and models          |
| **03 - Generate Data**     | Create synthetic sensor readings            | Simulates 30 days of data from 5 machines (~216K readings)              |
| **04 - Upload to S3**      | Move data to cloud                          | Makes data accessible for distributed processing and team collaboration |

### Phase 2: Data Preparation (Notebooks 05-07)

| Step                               | Purpose                                     | Why It Matters                                                             |
| ---------------------------------- | ------------------------------------------- | -------------------------------------------------------------------------- |
| **05 - Explore Data**        | Understand data distributions and patterns  | Identifies data quality issues, class imbalance, and feature relationships |
| **06 - Clean Data**          | Handle missing values, fix types            | Ensures model receives consistent, valid inputs                            |
| **07 - Feature Engineering** | Create `temp_diff` and `overheat` label | Transforms raw data into predictive features; defines the target variable  |

### Phase 3: Model Development (Notebooks 08-11)

| Step                           | Purpose                                     | Why It Matters                                                                   |
| ------------------------------ | ------------------------------------------- | -------------------------------------------------------------------------------- |
| **08 - Train Model**     | Fit Logistic Regression on training data    | Creates the predictive model; evaluates accuracy, precision, recall              |
| **09 - MLflow Tracking** | Log experiments with parameters and metrics | Enables reproducibility; tracks model versions; facilitates comparison           |
| **10 - Model Registry**  | Register model for governance               | Version control for models; approval workflow; lineage tracking                  |
| **11 - Validate Model**  | Verify model meets quality thresholds       | Gate before deployment; ensures >85% accuracy; checks for degenerate predictions |

### Phase 4: Deployment (Notebooks 12-13)

| Step                           | Purpose                          | Why It Matters                                                        |
| ------------------------------ | -------------------------------- | --------------------------------------------------------------------- |
| **12 - Deploy Endpoint** | Create real-time inference API   | Makes model accessible for production systems; handles scaling        |
| **13 - Test Endpoint**   | Validate deployed model behavior | Confirms API works correctly; tests edge cases; documents integration |

## Model Performance

- **Accuracy**: ~90-95%
- **Algorithm**: Logistic Regression (simple, interpretable, fast)
- **Features**: `temperature`, `temp_diff`
- **Training data**: 80% of dataset (~173K samples)
- **Test data**: 20% of dataset (~43K samples)

## Production Integration

Once deployed, the model can be integrated into:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Sensors   │────▶│  API Call   │────▶│   Action    │
│  (IoT/PLC)  │     │  (Endpoint) │     │  (Alert)    │
└─────────────┘     └─────────────┘     └─────────────┘
     │                    │                    │
     │                    │                    │
  temperature         prediction            dashboard
  room_temp           probability           notification
                                            work order
```

**Example API call**:

```python
response = endpoint.predict({
    'temperature': 82,
    'room_temp': 25
})
# Returns: {'prediction': 1, 'probability': 0.97}
```

## Business Value

| Metric                       | Impact                                               |
| ---------------------------- | ---------------------------------------------------- |
| **Downtime reduction** | Prevent unplanned outages by acting before failures  |
| **Maintenance cost**   | Reduce unnecessary scheduled maintenance             |
| **Equipment lifespan** | Prevent damage from overheating events               |
| **Safety**             | Reduce risk of heat-related incidents                |
| **Efficiency**         | Optimize technician time with targeted interventions |

## Educational Purpose

This project is designed for **students** learning AWS SageMaker Unified Studio. It demonstrates:

1. **End-to-end ML lifecycle** - From raw data to production API
2. **AWS SageMaker components** - Notebooks, MLflow, Model Registry, Endpoints
3. **MLOps best practices** - Experiment tracking, model versioning, validation gates
4. **Real-world patterns** - Feature engineering, binary classification, API deployment

## Limitations & Future Improvements

**Current limitations**:

- Synthetic data (not real sensor readings)
- Single model type (Logistic Regression)
- Binary classification only (overheat yes/no)
- No time-series features (trends, seasonality)

**Potential improvements**:

- Add time-series features (rolling averages, rate of change)
- Implement anomaly detection for unusual patterns
- Multi-class prediction (normal, warning, critical)
- Ensemble models for improved accuracy
- Real-time streaming with Kinesis
- Automated retraining pipeline
