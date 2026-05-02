import os
import pickle
import sys
import math
import pandas as pd
import numpy as np
from utils import load_metrics, save_costs, extract_features

FEATURE_COLS = ['latency_ms', 'throughput_mbps', 'packet_loss_rate',
                'tx_packets', 'rx_packets', 'jitter_ms', 'queue_delay_ms']

def load_all_scenarios(processed_dir, scenarios):
    """Load all scenario flows into a flat list for cross-scenario normalization."""
    all_flows = {}
    for scenario in scenarios:
        filepath = os.path.join(processed_dir, f"{scenario}_metrics.json")
        if os.path.exists(filepath):
            data = load_metrics(filepath)
            all_flows[scenario] = data
    return all_flows

def cross_scenario_normalize(all_scenario_data, scenarios):
    """
    Normalize features relative to the min/max values seen ACROSS all scenarios.
    This ensures Normal vs Congestion vs Failure produce genuinely different inputs
    to the model, even when absolute values are extreme (e.g., latency in billions).
    """
    # Collect all feature vectors across all scenarios
    all_feature_rows = []
    for scenario in scenarios:
        if scenario not in all_scenario_data:
            continue
        data = all_scenario_data[scenario]
        for flow in data.get("flows", []):
            all_feature_rows.append(extract_features(flow))

    if not all_feature_rows:
        return {}

    arr = np.array(all_feature_rows, dtype=float)
    col_min = arr.min(axis=0)
    col_max = arr.max(axis=0)
    col_range = col_max - col_min

    # Build normalized lookup: scenario -> list of normalized feature vectors per flow
    normalized_map = {}
    idx = 0
    for scenario in scenarios:
        if scenario not in all_scenario_data:
            continue
        data = all_scenario_data[scenario]
        scenario_norms = []
        for flow in data.get("flows", []):
            raw = np.array(extract_features(flow), dtype=float)
            # Min-max normalize; suppress divide-by-zero warning when range=0
            with np.errstate(invalid='ignore', divide='ignore'):
                norm = np.where(col_range > 0, (raw - col_min) / col_range, 0.5)
            scenario_norms.append(norm.tolist())
            idx += 1
        normalized_map[scenario] = scenario_norms
    return normalized_map

def predict_costs():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, "model.pkl")
    processed_dir = os.path.abspath(os.path.join(current_dir, "..", "outputs", "processed"))
    ml_output_dir = os.path.abspath(os.path.join(current_dir, "..", "outputs", "ml"))

    # Load the trained ML model
    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}. Please run train.py first.")
        sys.exit(1)

    print(f"Loading trained ML model from {model_path}...")
    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    os.makedirs(ml_output_dir, exist_ok=True)

    scenarios = ["normal", "congestion", "failure"]

    # Load ALL scenarios first so we can normalize them relative to each other
    print("Loading all scenario metrics for cross-scenario normalization...")
    all_scenario_data = load_all_scenarios(processed_dir, scenarios)
    normalized_map = cross_scenario_normalize(all_scenario_data, scenarios)

    # Process each scenario using normalized features
    for scenario in scenarios:
        if scenario not in all_scenario_data:
            print(f"Warning: No data found for {scenario}. Skipping.")
            continue

        output_file = os.path.join(ml_output_dir, f"{scenario}_costs.json")
        data = all_scenario_data[scenario]

        costs_data = {
            "scenario_id": data.get("scenario_id", scenario),
            "link_costs": []
        }

        flows = data.get("flows", [])
        norm_vectors = normalized_map.get(scenario, [])

        for i, flow in enumerate(flows):
            norm_features = norm_vectors[i] if i < len(norm_vectors) else [0.0] * 7

            # Predict using normalized features with proper column names
            input_df = pd.DataFrame([norm_features], columns=FEATURE_COLS)
            cost_pred = model.predict(input_df)[0]

            costs_data["link_costs"].append({
                "flow_id": flow.get("flow_id"),
                "src_node": flow.get("src_node"),
                "dst_node": flow.get("dst_node"),
                "predicted_cost": round(cost_pred, 4)
            })

        save_costs(costs_data, output_file)
        print(f"[{scenario.upper()}] Generated {output_file}")
        for entry in costs_data["link_costs"]:
            print(f"  Flow {entry['flow_id']} ({entry['src_node']} -> {entry['dst_node']}): cost = {entry['predicted_cost']}")

if __name__ == "__main__":
    predict_costs()
