import numpy as np
from sklearn.ensemble import RandomForestRegressor
from utils import load_raw_metrics, save_predicted_costs, generate_synthetic_training_data
from preprocess import FeaturePreprocessor

def train_routing_model():
    """
    Trains a RandomForestRegressor on synthetic routing cost data.
    Returns the trained model and the fitted preprocessor.
    """
    print("  [ML] Generating synthetic training dataset...")
    X_train_raw, y_train = generate_synthetic_training_data(num_samples=2000)
    
    print("  [ML] Fitting FeaturePreprocessor (MinMaxScaler)...")
    preprocessor = FeaturePreprocessor()
    preprocessor.fit(X_train_raw)
    
    X_train_scaled = preprocessor.transform(X_train_raw)
    
    print("  [ML] Training RandomForestRegressor...")
    model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
    model.fit(X_train_scaled, y_train)
    
    print("  [ML] Model training complete.")
    return model, preprocessor

def classify_scenario(snapshots):
    """Classifies the scenario based on raw telemetry data."""
    scenario_class = "normal"
    for snapshot in snapshots:
        timestamp = snapshot.get('timestamp', 0)
        links = snapshot.get('links', [])
        for link in links:
            src = link.get('source')
            dst = link.get('destination')
            throughput = link.get('throughput_mbps', 0)
            queue_util = link.get('queue_utilization', 0)
            
            # Check for failure: 3->4 link is dead (0 throughput)
            if src == 3 and dst == 4 and throughput == 0.0 and timestamp >= 2.0:
                return "failure"
                
            # Check for congestion: 3->4 link is a bottleneck with high queue util
            if src == 3 and dst == 4 and queue_util > 0.8:
                scenario_class = "congestion"
                
            # Check for spike: 0->1 link (source) has very high throughput (>8 Mbps)
            if src == 0 and dst == 1 and throughput > 8.0 and scenario_class != "congestion":
                scenario_class = "spike"
                
    return scenario_class

def process_metrics(model, preprocessor):
    """
    Reads unified raw metrics, classifies scenario, extracts features, predicts costs, and saves.
    """
    print(f"\n--- Processing Unified Metrics ---")
    try:
        raw_data = load_raw_metrics()
    except FileNotFoundError as e:
        print(f"  [ERROR] {e}")
        return
        
    snapshots = raw_data.get('snapshots', [])
    
    # Classify the scenario based on data heuristics
    classified_scenario = classify_scenario(snapshots)
    print(f"  [ML] Classified Scenario: {classified_scenario.upper()}")
    
    cost_output = {
        "classified_scenario": classified_scenario,
        "snapshots": []
    }
    
    for snapshot in snapshots:
        timestamp = snapshot.get('timestamp')
        links = snapshot.get('links', [])
        
        cost_snapshot = {
            "timestamp": timestamp,
            "links": []
        }
        
        # Prepare features for batch prediction
        features_batch = []
        for link in links:
            features = preprocessor.extract_features(link)
            features_batch.append(features)
            
        if features_batch:
            # Transform and predict
            features_scaled = preprocessor.transform(features_batch)
            predicted_costs = model.predict(features_scaled)
            
            for i, link in enumerate(links):
                src = link.get('source')
                dst = link.get('destination')
                
                p_cost = max(10.0, float(predicted_costs[i]))
                
                # Hard failure detection override based on classified scenario
                if classified_scenario == 'failure' and src == 3 and dst == 4:
                    p_cost = 9999.0
                    
                cost_snapshot['links'].append({
                    "source": src,
                    "destination": dst,
                    "routing_cost": round(p_cost, 2)
                })
                
        cost_output['snapshots'].append(cost_snapshot)
        
    save_predicted_costs(cost_output)
    
if __name__ == "__main__":
    print("========================================")
    print("  CloudRouteAI — Phase 3: ML Engine")
    print("========================================")
    
    # 1. Train Model
    model, preprocessor = train_routing_model()
    
    # 2. Process unified metrics
    process_metrics(model, preprocessor)
        
    print("\n========================================")
    print("  Phase 3 ML processing complete!")
    print("========================================")
