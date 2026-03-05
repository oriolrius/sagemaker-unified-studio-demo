# Setup Guide: Deploying SageMaker Unified Studio

This guide walks through deploying the complete infrastructure for the machine overheat prediction demo.

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] AWS CLI installed and configured
- [ ] AWS credentials with appropriate permissions
- [ ] Python 3.11+ installed
- [ ] [uv](https://docs.astral.sh/uv/) installed
- [ ] AWS Organizations enabled (for IAM Identity Center)

### Verify AWS CLI

```bash
aws --version
# Should show: aws-cli/2.x.x or higher

aws sts get-caller-identity
# Should show your AWS account ID and user ARN
```

### Required IAM Permissions

Your AWS user/role needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "datazone:*",
        "sagemaker:*",
        "s3:*",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:PassRole",
        "cloudformation:*",
        "sso:*"
      ],
      "Resource": "*"
    }
  ]
}
```

## Step 1: Setup IAM Identity Center (One-Time)

SageMaker Unified Studio requires IAM Identity Center (SSO) for authentication.

### 1.1 Enable IAM Identity Center

```bash
# Check if already enabled
aws sso-admin list-instances --region eu-west-1
```

If not enabled:
1. Navigate to https://console.aws.amazon.com/singlesignon
2. Choose **Enable IAM Identity Center**
3. Select **AWS Organizations** as identity source

### 1.2 Create SSO User

1. In IAM Identity Center console, go to **Users**
2. Choose **Add user**
3. Enter user details:
   - Username: `student`
   - Email: your email
   - First/Last name
4. Choose **Next** → **Add user**
5. User receives email with password setup link

### 1.3 Verify SSO User

```bash
aws identitystore list-users \
  --identity-store-id <identity-store-id> \
  --region eu-west-1
```

## Step 2: Create SageMaker Unified Studio Domain

Domains must be created via the AWS Console (limited CloudFormation support).

### 2.1 Navigate to Console

1. Go to https://console.aws.amazon.com/datazone
2. Ensure region is set to **eu-west-1**

### 2.2 Create Domain (Quick Setup)

1. Choose **Create a Unified Studio domain**
2. Select **Quick setup**
3. Configure VPC:
   - Choose **Create new VPC** (recommended for demo)
   - Or select existing VPC with proper subnets
4. Expand **Quick setup settings**:
   - Domain name: `overheat-demo-domain`
   - Leave other defaults (roles, encryption)
5. **Onboard your data** (optional): Skip for now
6. **Create IAM Identity Center user**:
   - Select the `student` user created in Step 1
7. Choose **Create domain**

**Expected time**: 10-15 minutes

### 2.3 Verify Domain Creation

```bash
# List domains (via DataZone API)
aws datazone list-domains --region eu-west-1
```

## Step 3: Generate Synthetic Data

```bash
cd /home/oriol/esade/sagemaker-unified-studio-demo

# Install dependencies
uv sync

# Generate data
uv run python scripts/generate_data.py
```

**Output**: `data/machines.csv` with 10,000 temperature readings

### Inspect the Data

```bash
head -n 5 data/machines.csv
```

Expected format:
```csv
timestamp,machine_id,temperature,room_temp
2026-02-03 00:00:00,M1,65.3,24.8
2026-02-03 00:01:00,M1,66.1,24.9
```

## Step 4: Deploy Project Resources

### 4.1 Create CloudFormation Stack

```bash
./deploy.sh
```

Or manually:

```bash
aws cloudformation create-stack \
  --stack-name sagemaker-overheat-project \
  --template-body file://cloudformation/project-resources.yaml \
  --capabilities CAPABILITY_IAM \
  --region eu-west-1

# Wait for completion
aws cloudformation wait stack-create-complete \
  --stack-name sagemaker-overheat-project \
  --region eu-west-1
```

**Expected time**: 2-3 minutes

### 4.2 Verify Stack Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name sagemaker-overheat-project \
  --query 'Stacks[0].Outputs' \
  --output table \
  --region eu-west-1
```

Expected outputs:
- `DataBucketName`: S3 bucket name
- `ExecutionRoleArn`: IAM role ARN
- `Region`: eu-west-1

### 4.3 Upload Data to S3

```bash
uv run python scripts/upload_to_s3.py
```

Verify:
```bash
BUCKET=$(aws cloudformation describe-stacks \
  --stack-name sagemaker-overheat-project \
  --query 'Stacks[0].Outputs[?OutputKey==`DataBucketName`].OutputValue' \
  --output text \
  --region eu-west-1)

aws s3 ls s3://$BUCKET/data/raw/ --region eu-west-1
```

## Step 5: Access SageMaker Unified Studio

### 5.1 Get Portal URL

1. Navigate to https://console.aws.amazon.com/datazone (region: eu-west-1)
2. Select your domain: `overheat-demo-domain`
3. Copy the **Portal URL** (or click **Open portal**)

### 5.2 Sign In

1. Open the Portal URL
2. Sign in with IAM Identity Center credentials:
   - Username: `student`
   - Password: (set via email link)

**First login takes 1-2 minutes** to initialize.

## Step 6: Create Project

### 6.1 Create Project via Console

1. In Unified Studio portal, choose **Create project**
2. Configure project:
   - Name: `machine-overheat-prediction`
   - Description: `Predict machine overheating from temperature sensors`
   - Blueprint: **ML Development**
3. Choose **Create project**

**Expected time**: 3-5 minutes

### 6.2 Access Project

1. From portal home, select **Projects**
2. Click on `machine-overheat-prediction`
3. You'll see tabs: **Overview**, **Data**, **Notebooks**, **Models**, **Pipelines**

## Step 7: Upload Notebooks

### 7.1 Navigate to Notebooks

1. In project, click **Notebooks** tab
2. Choose **Upload** (↑ icon)

### 7.2 Upload All Notebooks

Upload these files from `notebooks/` directory:
- `01_explore_data.ipynb`
- `02_clean_data.ipynb`
- `03_feature_engineering.ipynb`
- `04_train_model.ipynb`
- `05_mlflow_tracking.ipynb`
- `06_model_registry.ipynb`
- `07_validate_model.ipynb`
- `08_deploy_endpoint.ipynb`

### 7.3 Verify Upload

All notebooks should appear in the project's Notebooks tab.

## Step 8: Register Data in Catalog

### 8.1 Navigate to Data Catalog

1. In project, click **Data** tab
2. Choose **Register data source**

### 8.2 Register S3 Data

1. Select **Amazon S3**
2. Configure:
   - Connection name: `overheat-data`
   - Bucket: (select your bucket from dropdown)
   - Prefix: `data/raw/`
3. Add metadata:
   - Description: `Machine temperature sensor data`
   - Tags: `demo`, `iot`, `temperature`
4. Choose **Register**

### 8.3 Verify Registration

1. Go to **Data** tab
2. You should see `machines.csv` listed
3. Click on it to view metadata and preview

## Step 9: Configure Environment

### 9.1 Create Environment File

In a notebook, create `.env`:

```python
import os

# Get from CloudFormation outputs
bucket_name = "sagemaker-unified-overheat-demo-<account-id>"
execution_role = "arn:aws:iam::<account-id>:role/SageMakerExecutionRole-overheat-demo"

# Write to file
with open('.env', 'w') as f:
    f.write(f"BUCKET_NAME={bucket_name}\n")
    f.write(f"EXECUTION_ROLE={execution_role}\n")
    f.write(f"REGION=eu-west-1\n")
```

Or manually create `/home/sagemaker-user/.env`:
```bash
BUCKET_NAME=sagemaker-unified-overheat-demo-123456789012
EXECUTION_ROLE=arn:aws:iam::123456789012:role/SageMakerExecutionRole-overheat-demo
REGION=eu-west-1
```

## Troubleshooting

### Cannot access Unified Studio portal

**Issue**: "You don't have permission to access this domain"

**Solution**: 
- Ensure you're signed in with IAM Identity Center user (not IAM role)
- Verify user was added to domain during creation
- Check user has proper permissions in IAM Identity Center

### Domain creation fails

**Issue**: "No VPC configured for SageMaker Unified Studio"

**Solution**: Use Quick setup to create a new VPC, or ensure existing VPC has:
- At least 2 subnets in different AZs
- Internet gateway
- Proper security groups

### Data upload fails

**Issue**: S3 access denied

**Solution**:
```bash
# Check bucket policy
aws s3api get-bucket-policy \
  --bucket $BUCKET_NAME \
  --region eu-west-1

# Verify IAM permissions
aws iam get-role \
  --role-name SageMakerExecutionRole-overheat-demo
```

### Project creation fails

**Issue**: "Blueprint not available"

**Solution**: Ensure domain was created with ML capabilities enabled. Check domain settings in console.

### Notebooks won't start

**Issue**: Kernel fails to start

**Solution**:
- Check execution role has SageMaker permissions
- Verify VPC configuration allows internet access
- Try restarting the notebook instance

## Next Steps

Once setup is complete, proceed to the [Student Guide](student-guide.md) to start working through the notebooks.

## Cleanup

### Delete Project Resources

```bash
# 1. Delete any running endpoints
aws sagemaker list-endpoints --region eu-west-1
aws sagemaker delete-endpoint \
  --endpoint-name machine-overheat-endpoint \
  --region eu-west-1

# 2. Empty S3 bucket
BUCKET=$(aws cloudformation describe-stacks \
  --stack-name sagemaker-overheat-project \
  --query 'Stacks[0].Outputs[?OutputKey==`DataBucketName`].OutputValue' \
  --output text \
  --region eu-west-1)

aws s3 rm s3://$BUCKET --recursive --region eu-west-1

# 3. Delete CloudFormation stack
aws cloudformation delete-stack \
  --stack-name sagemaker-overheat-project \
  --region eu-west-1

# 4. Delete project in Unified Studio (via console)
# Navigate to project → Settings → Delete project

# 5. Delete domain (via console)
# Navigate to https://console.aws.amazon.com/datazone
# Select domain → Actions → Delete domain
```

**Note**: Domain deletion can take 10-15 minutes.
