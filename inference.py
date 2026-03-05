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
