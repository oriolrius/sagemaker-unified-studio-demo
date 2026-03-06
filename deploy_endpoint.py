"""Deploy the machine overheat prediction endpoint via AWS SDK."""
import boto3
from botocore.exceptions import ClientError
import time
import json
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()
bucket_name = os.getenv('BUCKET_NAME', 'sagemaker-unified-overheat-demo-792641153717')
region = os.getenv('REGION', 'eu-west-1')

print(f"Bucket: {bucket_name}")
print(f"Region: {region}")

# Get execution role from CloudFormation stack
cfn = boto3.client('cloudformation', region_name=region)
try:
    response = cfn.describe_stacks(StackName='sagemaker-overheat-project')
    outputs = {o['OutputKey']: o['OutputValue'] for o in response['Stacks'][0]['Outputs']}
    role = outputs.get('ExecutionRoleArn')
    print(f"Execution Role: {role}")
except Exception as e:
    print(f"Error getting role: {e}")
    role = None

if not role:
    print("Could not get execution role. Exiting.")
    exit(1)

# Model details
model_data = f's3://{bucket_name}/models/logistic_regression/model.tar.gz'
model_name = 'machine-overheat-model'
endpoint_config_name = 'machine-overheat-endpoint-config'
endpoint_name = 'machine-overheat-endpoint'

print(f"\nModel data: {model_data}")
print(f"Endpoint name: {endpoint_name}")

sm_client = boto3.client('sagemaker', region_name=region)
sm_runtime = boto3.client('sagemaker-runtime', region_name=region)

def delete_endpoint_resources():
    """Clean up existing endpoint resources."""
    try:
        sm_client.delete_endpoint(EndpointName=endpoint_name)
        print(f"Deleted endpoint: {endpoint_name}")
        time.sleep(5)
    except:
        pass
    try:
        sm_client.delete_endpoint_config(EndpointConfigName=endpoint_config_name)
        print(f"Deleted endpoint config: {endpoint_config_name}")
    except:
        pass
    try:
        sm_client.delete_model(ModelName=model_name)
        print(f"Deleted model: {model_name}")
    except:
        pass

# Check if endpoint already exists
try:
    response = sm_client.describe_endpoint(EndpointName=endpoint_name)
    status = response['EndpointStatus']
    print(f"\nEndpoint already exists with status: {status}")
    
    if status == 'InService':
        print("Endpoint is ready. Testing it...")
    elif status == 'Failed':
        print("Endpoint in Failed state. Cleaning up...")
        delete_endpoint_resources()
        time.sleep(10)
        raise ClientError({'Error': {'Code': 'NotFound'}}, 'describe_endpoint')
    else:
        print(f"Endpoint is in {status} state. Waiting...")
        waiter = sm_client.get_waiter('endpoint_in_service')
        waiter.wait(EndpointName=endpoint_name)
        print("Endpoint is now ready.")
        
except ClientError as e:
    if 'Could not find endpoint' in str(e) or 'NotFound' in str(e.response.get('Error', {}).get('Code', '')):
        print("\nEndpoint does not exist. Creating new endpoint...")
        
        # First, ensure inference.py exists in S3
        s3 = boto3.client('s3', region_name=region)
        inference_code = '''
import joblib
import json
import numpy as np

def model_fn(model_dir):
    """Load model from directory"""
    model = joblib.load(f"{model_dir}/model.pkl")
    return model

def input_fn(request_body, content_type):
    """Parse input request"""
    if content_type == 'application/json':
        data = json.loads(request_body)
        temp = data['temperature']
        room_temp = data['room_temp']
        temp_diff = temp - room_temp
        return np.array([[temp, temp_diff]])
    raise ValueError(f"Unsupported content type: {content_type}")

def predict_fn(input_data, model):
    """Make prediction"""
    prediction = model.predict(input_data)[0]
    probability = model.predict_proba(input_data)[0][1]
    return {'prediction': int(prediction), 'probability': float(probability)}

def output_fn(prediction, accept):
    """Format output"""
    return json.dumps(prediction), accept
'''
        
        # Get the sklearn container image
        # SKLearn 1.2-1 container for eu-west-1
        sklearn_image = f'141502667606.dkr.ecr.{region}.amazonaws.com/sagemaker-scikit-learn:1.2-1-cpu-py3'
        
        # Create model
        print("Creating SageMaker model...")
        try:
            sm_client.create_model(
                ModelName=model_name,
                PrimaryContainer={
                    'Image': sklearn_image,
                    'ModelDataUrl': model_data,
                    'Environment': {
                        'SAGEMAKER_PROGRAM': 'inference.py',
                        'SAGEMAKER_SUBMIT_DIRECTORY': f's3://{bucket_name}/code/sourcedir.tar.gz'
                    }
                },
                ExecutionRoleArn=role
            )
            print(f"Created model: {model_name}")
        except ClientError as e:
            if 'already exists' in str(e):
                print(f"Model {model_name} already exists")
            else:
                raise
        
        # Create endpoint config
        print("Creating endpoint configuration...")
        try:
            sm_client.create_endpoint_config(
                EndpointConfigName=endpoint_config_name,
                ProductionVariants=[{
                    'VariantName': 'AllTraffic',
                    'ModelName': model_name,
                    'InitialInstanceCount': 1,
                    'InstanceType': 'ml.t2.medium'
                }]
            )
            print(f"Created endpoint config: {endpoint_config_name}")
        except ClientError as e:
            if 'already exists' in str(e):
                print(f"Endpoint config {endpoint_config_name} already exists")
            else:
                raise
        
        # Create endpoint
        print("Creating endpoint (this may take 5-10 minutes)...")
        sm_client.create_endpoint(
            EndpointName=endpoint_name,
            EndpointConfigName=endpoint_config_name
        )
        
        print("Waiting for endpoint to be in service...")
        waiter = sm_client.get_waiter('endpoint_in_service')
        waiter.wait(
            EndpointName=endpoint_name,
            WaiterConfig={'Delay': 30, 'MaxAttempts': 30}
        )
        print(f"✓ Endpoint deployed: {endpoint_name}")
    else:
        print(f"Error: {e}")
        exit(1)

# Test the endpoint
print("\n" + "="*50)
print("Testing the endpoint")
print("="*50)

def test_endpoint(temp, room_temp):
    """Test the endpoint with given inputs."""
    payload = json.dumps({'temperature': temp, 'room_temp': room_temp})
    response = sm_runtime.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType='application/json',
        Body=payload
    )
    result = json.loads(response['Body'].read().decode())
    return result

# Test 1: Normal temperature
test_input = {'temperature': 72, 'room_temp': 25}
response = test_endpoint(72, 25)
print(f"\nTest 1: Normal temperature")
print(f"Input: {test_input}")
print(f"Response: {response}")
print(f"→ Temperature {test_input['temperature']}°C: {'⚠️ OVERHEAT!' if response['prediction'] == 1 else '✓ Normal'}")
print(f"→ Probability of overheat: {response['probability']*100:.1f}%")

# Test 2: High temperature
test_input = {'temperature': 85, 'room_temp': 25}
response = test_endpoint(85, 25)
print(f"\nTest 2: High temperature")
print(f"Input: {test_input}")
print(f"Response: {response}")
print(f"→ Temperature {test_input['temperature']}°C: {'⚠️ OVERHEAT!' if response['prediction'] == 1 else '✓ Normal'}")
print(f"→ Probability of overheat: {response['probability']*100:.1f}%")

# Test 3: Borderline temperature
test_input = {'temperature': 79, 'room_temp': 25}
response = test_endpoint(79, 25)
print(f"\nTest 3: Borderline temperature")
print(f"Input: {test_input}")
print(f"Response: {response}")
print(f"→ Temperature {test_input['temperature']}°C: {'⚠️ OVERHEAT!' if response['prediction'] == 1 else '✓ Normal'}")
print(f"→ Probability of overheat: {response['probability']*100:.1f}%")

print("\n" + "="*50)
print("Endpoint deployment complete!")
print("="*50)
