#!/usr/bin/env python3
"""
Generate synthetic machine temperature data for the overheat prediction demo.

Creates realistic temperature readings with:
- 5 machines (M1-M5)
- 30 days of minute-by-minute data
- Normal operating temperatures (60-75°C)
- Occasional overheating events (>80°C)
- Realistic room temperature variation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# Configuration
NUM_MACHINES = 5
DAYS = 30
SAMPLES_PER_DAY = 1440  # One per minute
TOTAL_SAMPLES = NUM_MACHINES * DAYS * SAMPLES_PER_DAY

# Temperature parameters
NORMAL_TEMP_MEAN = 67
NORMAL_TEMP_STD = 5
OVERHEAT_TEMP_MEAN = 85
OVERHEAT_TEMP_STD = 3
OVERHEAT_PROBABILITY = 0.08  # 8% of readings are overheating

ROOM_TEMP_MEAN = 25
ROOM_TEMP_STD = 1

# Output path
OUTPUT_DIR = "data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "machines.csv")


def generate_temperature_reading(machine_id, timestamp, is_overheat=False):
    """Generate a single temperature reading."""
    if is_overheat:
        temperature = np.random.normal(OVERHEAT_TEMP_MEAN, OVERHEAT_TEMP_STD)
    else:
        temperature = np.random.normal(NORMAL_TEMP_MEAN, NORMAL_TEMP_STD)
    
    # Ensure temperature is positive and realistic
    temperature = max(55, min(95, temperature))
    
    # Room temperature varies slightly
    room_temp = np.random.normal(ROOM_TEMP_MEAN, ROOM_TEMP_STD)
    room_temp = max(20, min(30, room_temp))
    
    return {
        "timestamp": timestamp,
        "machine_id": machine_id,
        "temperature": round(temperature, 1),
        "room_temp": round(room_temp, 1)
    }


def generate_dataset():
    """Generate complete synthetic dataset."""
    print(f"Generating {TOTAL_SAMPLES:,} temperature readings...")
    
    # Start date
    start_date = datetime.now() - timedelta(days=DAYS)
    
    # Generate data
    data = []
    for machine_num in range(1, NUM_MACHINES + 1):
        machine_id = f"M{machine_num}"
        
        for day in range(DAYS):
            for minute in range(SAMPLES_PER_DAY):
                timestamp = start_date + timedelta(days=day, minutes=minute)
                
                # Randomly decide if this reading is overheating
                is_overheat = np.random.random() < OVERHEAT_PROBABILITY
                
                reading = generate_temperature_reading(machine_id, timestamp, is_overheat)
                data.append(reading)
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Sort by timestamp
    df = df.sort_values("timestamp").reset_index(drop=True)
    
    return df


def save_dataset(df):
    """Save dataset to CSV."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved to: {OUTPUT_FILE}")


def print_statistics(df):
    """Print dataset statistics."""
    print(f"\nDataset Statistics:")
    print(f"  Total readings: {len(df):,}")
    print(f"  Machines: {', '.join(sorted(df['machine_id'].unique()))}")
    print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"  Temperature range: {df['temperature'].min():.1f}°C to {df['temperature'].max():.1f}°C")
    print(f"  Room temp range: {df['room_temp'].min():.1f}°C to {df['room_temp'].max():.1f}°C")
    
    # Overheating statistics
    overheat_count = (df['temperature'] > 80).sum()
    overheat_pct = (overheat_count / len(df)) * 100
    print(f"  Overheating events: {overheat_count:,} ({overheat_pct:.2f}%)")


if __name__ == "__main__":
    # Generate data
    df = generate_dataset()
    
    # Print statistics
    print_statistics(df)
    
    # Save to file
    save_dataset(df)
    
    print("\n✓ Data generation complete!")
