# Environment Configuration

Create a `.env` file in the project root with your AWS resources:

```bash
BUCKET_NAME=sagemaker-unified-overheat-demo-123456789012
EXECUTION_ROLE=arn:aws:iam::123456789012:role/SageMakerExecutionRole-overheat-demo
REGION=eu-west-1
```

## Get Values from CloudFormation

```bash
# Get bucket name
aws cloudformation describe-stacks \
  --stack-name sagemaker-overheat-project \
  --query 'Stacks[0].Outputs[?OutputKey==`DataBucketName`].OutputValue' \
  --output text \
  --region eu-west-1

# Get execution role
aws cloudformation describe-stacks \
  --stack-name sagemaker-overheat-project \
  --query 'Stacks[0].Outputs[?OutputKey==`ExecutionRoleArn`].OutputValue' \
  --output text \
  --region eu-west-1
```

## Or Create Automatically

```bash
cat > .env << EOF
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name sagemaker-overheat-project \
  --query 'Stacks[0].Outputs[?OutputKey==`DataBucketName`].OutputValue' \
  --output text \
  --region eu-west-1)
EXECUTION_ROLE=$(aws cloudformation describe-stacks \
  --stack-name sagemaker-overheat-project \
  --query 'Stacks[0].Outputs[?OutputKey==`ExecutionRoleArn`].OutputValue' \
  --output text \
  --region eu-west-1)
REGION=eu-west-1
EOF
```
