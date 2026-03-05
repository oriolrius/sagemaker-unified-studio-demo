#!/usr/bin/env python3
"""
Upload generated data to S3 bucket.
"""

import boto3
import os
import sys

# Configuration
DATA_FILE = "data/machines.csv"
S3_KEY = "data/raw/machines.csv"


def get_bucket_name():
    """Get bucket name from CloudFormation stack outputs."""
    cf = boto3.client('cloudformation', region_name='eu-west-1')
    
    try:
        response = cf.describe_stacks(StackName='sagemaker-overheat-project')
        outputs = response['Stacks'][0]['Outputs']
        
        for output in outputs:
            if output['OutputKey'] == 'DataBucketName':
                return output['OutputValue']
        
        print("Error: DataBucketName output not found in stack")
        sys.exit(1)
    
    except Exception as e:
        print(f"Error: Could not get bucket name from CloudFormation: {e}")
        print("\nMake sure the stack 'sagemaker-overheat-project' exists and is complete.")
        sys.exit(1)


def upload_to_s3(bucket_name):
    """Upload data file to S3."""
    if not os.path.exists(DATA_FILE):
        print(f"Error: {DATA_FILE} not found. Run generate_data.py first.")
        sys.exit(1)
    
    s3 = boto3.client('s3', region_name='eu-west-1')
    
    print(f"Uploading {DATA_FILE} to s3://{bucket_name}/{S3_KEY}...")
    
    try:
        s3.upload_file(DATA_FILE, bucket_name, S3_KEY)
        print(f"✓ Upload complete!")
        print(f"\nS3 URI: s3://{bucket_name}/{S3_KEY}")
    
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        sys.exit(1)


if __name__ == "__main__":
    bucket_name = get_bucket_name()
    upload_to_s3(bucket_name)
