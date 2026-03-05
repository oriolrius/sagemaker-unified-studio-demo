#!/bin/bash
set -e

echo "========================================="
echo "SageMaker Unified Studio - Project Setup"
echo "========================================="
echo ""

# Configuration
STACK_NAME="sagemaker-overheat-project"
REGION="eu-west-1"

# Step 1: Generate synthetic data
echo "Step 1: Generating synthetic data..."
if [ ! -f "data/machines.csv" ]; then
    uv run python scripts/generate_data.py
else
    echo "  ✓ Data already exists: data/machines.csv"
fi
echo ""

# Step 2: Create project resources (S3, IAM roles)
echo "Step 2: Creating project resources..."
aws cloudformation create-stack \
  --stack-name $STACK_NAME \
  --template-body file://cloudformation/project-resources.yaml \
  --capabilities CAPABILITY_IAM \
  --region $REGION \
  2>/dev/null || echo "  Stack already exists or creation failed"

echo "  Waiting for stack creation (2-3 minutes)..."
aws cloudformation wait stack-create-complete \
  --stack-name $STACK_NAME \
  --region $REGION

echo "  ✓ Stack created successfully!"
echo ""

# Step 3: Upload data to S3
echo "Step 3: Uploading data to S3..."
uv run python scripts/upload_to_s3.py
echo ""

# Step 4: Display outputs
echo "========================================="
echo "Project Setup Complete!"
echo "========================================="
echo ""

echo "Stack Outputs:"
aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs' \
  --output table \
  --region $REGION

echo ""
echo "Next Steps:"
echo "  1. Navigate to https://console.aws.amazon.com/datazone (region: eu-west-1)"
echo "  2. Sign in with your IAM Identity Center user"
echo "  3. Select your SageMaker Unified Studio domain"
echo "  4. Create a new project using the 'ML Development' blueprint"
echo "  5. Upload notebooks from the notebooks/ directory"
echo "  6. Follow the Student Guide: docs/student-guide.md"
echo ""
echo "To clean up:"
echo "  aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION"
echo ""
