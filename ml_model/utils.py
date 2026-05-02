import json
import os

def load_metrics(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data

def save_costs(data, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def extract_features(flow):
    return [
        flow.get("latency_ms", 0.0),
        flow.get("throughput_mbps", 0.0),
        flow.get("packet_loss_rate", 0.0),
        flow.get("tx_packets", 0.0),
        flow.get("rx_packets", 0.0),
        flow.get("jitter_ms", 0.0),
        flow.get("queue_delay_ms", 0.0)
    ]
