import json
import os
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "outputs", "raw")
ML_DIR = os.path.join(BASE_DIR, "outputs", "ml")

def load_raw_metrics():
    """Load the Phase 2 runtime metrics."""
    file_path = os.path.join(RAW_DIR, "runtime_metrics.json")
    if not os.path.exists(file_path):
        # Allow fallback to current directory if script run from root
        file_path = os.path.join("outputs", "raw", "runtime_metrics.json")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Could not find {file_path}")
            
    with open(file_path, 'r') as f:
        return json.load(f)

def save_predicted_costs(costs_data):
    """Save the Phase 3 predicted routing costs."""
    # Ensure directory exists
    os.makedirs(ML_DIR, exist_ok=True)
    os.makedirs(os.path.join("outputs", "ml"), exist_ok=True)
    
    file_path = os.path.join(ML_DIR, "costs.json")
    if not os.path.exists(ML_DIR):
        file_path = os.path.join("outputs", "ml", "costs.json")
        
    with open(file_path, 'w') as f:
        json.dump(costs_data, f, indent=2)
    print(f"  [EXPORT] Predicted costs saved to {file_path}")

def generate_synthetic_training_data(num_samples=1000):
    """
    Generate synthetic data representing our 'Routing Cost Philosophy'.
    Returns (X, y) where X is [queue_utilization, delay_ms, packet_loss]
    and y is the routing_cost.
    
    Philosophy:
    - Healthy: queue=0, delay~2ms, loss=0 -> cost=10
    - Congested: queue~1.0, delay~150+ms, loss>0 -> cost~1000
    - Failed: zero throughput or artificial extreme -> cost=9999
    """
    X = []
    y = []
    
    for _ in range(num_samples):
        scenario_type = random.choice(["healthy", "mild_congestion", "severe_congestion", "failed"])
        
        if scenario_type == "healthy":
            queue_util = random.uniform(0.0, 0.1)
            delay = random.uniform(2.0, 10.0)
            loss = 0.0
            cost = random.uniform(10.0, 50.0)
            
        elif scenario_type == "mild_congestion":
            queue_util = random.uniform(0.1, 0.6)
            delay = random.uniform(10.0, 50.0)
            loss = random.uniform(0.0, 0.05)
            cost = random.uniform(100.0, 400.0)
            
        elif scenario_type == "severe_congestion":
            queue_util = random.uniform(0.8, 1.0)
            delay = random.uniform(100.0, 300.0)
            loss = random.uniform(0.1, 0.6)
            cost = random.uniform(800.0, 1500.0)
            
        elif scenario_type == "failed":
            # For failed, we simulate the 'abandoned' state or extreme degradation
            queue_util = 1.0 
            delay = 999.0
            loss = 1.0
            cost = 9999.0
            
        X.append([queue_util, delay, loss])
        y.append(cost)
        
    return X, y
