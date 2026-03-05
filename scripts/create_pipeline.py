#!/usr/bin/env python3
"""
Create and execute SageMaker Pipeline for the overheat prediction workflow.

This script demonstrates Step 10: Workflow Orchestration.
"""

import boto3
import sagemaker
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ProcessingStep, TrainingStep
from sagemaker.workflow.parameters import ParameterString
from sagemaker.sklearn.processing import SKLearnProcessor
from sagemaker.sklearn.estimator import SKLearn
from sagemaker.processing import ProcessingInput, ProcessingOutput
from sagemaker.inputs import TrainingInput

# Configuration
REGION = 'eu-west-1'
PIPELINE_NAME = 'machine-overheat-pipeline'


def get_stack_outputs():
    """Get bucket name and execution role from CloudFormation."""
    cf = boto3.client('cloudformation', region_name=REGION)
    response = cf.describe_stacks(StackName='sagemaker-overheat-project')
    outputs = response['Stacks'][0]['Outputs']
    
    result = {}
    for output in outputs:
        if output['OutputKey'] == 'DataBucketName':
            result['bucket'] = output['OutputValue']
        elif output['OutputKey'] == 'ExecutionRoleArn':
            result['role'] = output['OutputValue']
    
    return result


def create_pipeline():
    """Create SageMaker Pipeline."""
    print("Creating SageMaker Pipeline...")
    
    # Get configuration
    config = get_stack_outputs()
    bucket = config['bucket']
    role = config['role']
    
    # Pipeline parameters
    input_data = ParameterString(
        name="InputData",
        default_value=f"s3://{bucket}/data/raw/machines.csv"
    )
    
    # Step 1: Data processing (cleaning + feature engineering)
    sklearn_processor = SKLearnProcessor(
        framework_version='1.2-1',
        role=role,
        instance_type='ml.m5.large',
        instance_count=1
    )
    
    processing_step = ProcessingStep(
        name="DataProcessing",
        processor=sklearn_processor,
        code="scripts/preprocess.py",
        inputs=[
            ProcessingInput(
                source=input_data,
                destination="/opt/ml/processing/input"
            )
        ],
        outputs=[
            ProcessingOutput(
                output_name="train",
                source="/opt/ml/processing/train",
                destination=f"s3://{bucket}/data/processed/train"
            ),
            ProcessingOutput(
                output_name="test",
                source="/opt/ml/processing/test",
                destination=f"s3://{bucket}/data/processed/test"
            )
        ]
    )
    
    # Step 2: Model training
    sklearn_estimator = SKLearn(
        entry_point="scripts/train.py",
        role=role,
        instance_type='ml.m5.large',
        framework_version='1.2-1',
        py_version='py3'
    )
    
    training_step = TrainingStep(
        name="TrainModel",
        estimator=sklearn_estimator,
        inputs={
            "train": TrainingInput(
                s3_data=processing_step.properties.ProcessingOutputConfig.Outputs["train"].S3Output.S3Uri,
                content_type="text/csv"
            )
        }
    )
    
    # Create pipeline
    pipeline = Pipeline(
        name=PIPELINE_NAME,
        parameters=[input_data],
        steps=[processing_step, training_step]
    )
    
    return pipeline


def main():
    """Create and start pipeline execution."""
    # Create pipeline
    pipeline = create_pipeline()
    
    # Upsert pipeline (create or update)
    print(f"Upserting pipeline: {PIPELINE_NAME}")
    pipeline.upsert(role_arn=get_stack_outputs()['role'])
    
    # Start execution
    print("Starting pipeline execution...")
    execution = pipeline.start()
    
    print(f"\n✓ Pipeline execution started!")
    print(f"  Execution ARN: {execution.arn}")
    print(f"\nMonitor progress in SageMaker Unified Studio:")
    print(f"  Navigate to your project → Pipelines → {PIPELINE_NAME} → Executions")
    
    # Wait for completion (optional)
    # print("\nWaiting for pipeline to complete...")
    # execution.wait()
    # print("✓ Pipeline execution complete!")


if __name__ == "__main__":
    main()
