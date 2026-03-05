# Environment Configuration

The notebooks use `python-dotenv` to load configuration from a `.env` file. You must create this file **in JupyterLab** before running any notebooks.

> **IMPORTANT**: The `.env` file must be created in JupyterLab's `/shared/` directory (where the notebooks are located), NOT in your local project folder.

## Required Configuration

Create a `.env` file with these values:

```bash
BUCKET_NAME=sagemaker-unified-overheat-demo-<account-id>
REGION=eu-west-1
```

Example with real account ID:
```bash
BUCKET_NAME=sagemaker-unified-overheat-demo-792641153717
REGION=eu-west-1
```

## Create .env in JupyterLab

1. Open JupyterLab in SageMaker Unified Studio
2. Click **File** → **New** → **Text File**
3. Type the configuration content above
4. Press **Ctrl+S** to save
5. Rename the file to `.env` when prompted
6. Click **Rename and Save**

## Get Your Values from CloudFormation

Run these commands in your local terminal to get your actual values:

```bash
# Get bucket name (this is what you need for .env)
aws cloudformation describe-stacks \
  --stack-name sagemaker-overheat-project \
  --query 'Stacks[0].Outputs[?OutputKey==`DataBucketName`].OutputValue' \
  --output text \
  --region eu-west-1

# Get execution role (optional, used for model deployment)
aws cloudformation describe-stacks \
  --stack-name sagemaker-overheat-project \
  --query 'Stacks[0].Outputs[?OutputKey==`ExecutionRoleArn`].OutputValue' \
  --output text \
  --region eu-west-1
```

## Verify Configuration Works

After creating the `.env` file in JupyterLab, run this in a notebook cell:

```python
from dotenv import load_dotenv
import os

load_dotenv()
bucket_name = os.getenv('BUCKET_NAME')
print(f"Using bucket: {bucket_name}")

# Expected output:
# Using bucket: sagemaker-unified-overheat-demo-792641153717
```

If you see `Using bucket: None`:
1. Verify the `.env` file exists in the file browser
2. Check the file is named exactly `.env` (not `.env.txt`)
3. Restart the kernel: **Kernel** → **Restart Kernel**

## Troubleshooting

### File shows as `.env.txt` instead of `.env`

JupyterLab may add a `.txt` extension. To fix:
1. Right-click the file in the file browser
2. Select **Rename**
3. Change the name to just `.env`

### `.env` file not visible in file browser

Files starting with `.` are sometimes hidden. Try:
1. Click the **Toggle File Filter** button in the file browser toolbar
2. Or type `.env` directly in the file path

### Changes not taking effect

After modifying the `.env` file:
1. Save the file (**Ctrl+S**)
2. Restart the kernel: **Kernel** → **Restart Kernel**
3. Re-run the cells that load the configuration
