#!/usr/bin/env python3
"""
Generate synthetic test data for local validation.
Replicates the logic from notebook 03_generate_data.ipynb.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Configuration (smaller dataset for testing)
NUM_MACHINES = 5
NUM_DAYS = 3  # Reduced for quick testing
OVERHEAT_PROBABILITY = 0.08

# Temperature parameters
NORMAL_TEMP_MEAN = 67
NORMAL_TEMP_STD = 5
OVERHEAT_TEMP_MEAN = 85
OVERHEAT_TEMP_STD = 3
ROOM_TEMP_MEAN = 25
ROOM_TEMP_STD = 1

def generate_data():
    np.random.seed(42)

    data = []
    start_date = datetime(2024, 1, 1)

    for machine_id in range(1, NUM_MACHINES + 1):
        for day in range(NUM_DAYS):
            for minute in range(0, 1440, 10):  # Every 10 minutes for speed
                timestamp = start_date + timedelta(days=day, minutes=minute)

                # Determine if overheating
                is_overheat = np.random.random() < OVERHEAT_PROBABILITY

                if is_overheat:
                    temperature = np.random.normal(OVERHEAT_TEMP_MEAN, OVERHEAT_TEMP_STD)
                else:
                    temperature = np.random.normal(NORMAL_TEMP_MEAN, NORMAL_TEMP_STD)

                room_temp = np.random.normal(ROOM_TEMP_MEAN, ROOM_TEMP_STD)

                data.append({
                    'machine_id': f'M{machine_id}',
                    'timestamp': timestamp.isoformat(),
                    'temperature': round(temperature, 2),
                    'room_temp': round(room_temp, 2)
                })

    df = pd.DataFrame(data)
    return df

if __name__ == '__main__':
    df = generate_data()
    output_path = 'data/raw/machines.csv'
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df):,} rows")
    print(f"Saved to: {output_path}")
    print(f"\nSample:")
    print(df.head())
    print(f"\nOverheat rate: {(df['temperature'] > 80).mean()*100:.2f}%")
