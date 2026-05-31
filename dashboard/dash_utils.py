"""
CloudRouteAI — Dashboard Utilities
===================================
Data loading helpers for the Streamlit dashboard.
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "outputs", "raw")
ML_DIR = os.path.join(BASE_DIR, "outputs", "ml")
ROUTING_DIR = os.path.join(BASE_DIR, "outputs", "routing")
PROCESSED_DIR = os.path.join(BASE_DIR, "outputs", "processed")

SCENARIOS = ["normal", "congestion", "failure", "spike"]

# Topology definition (1-indexed for display, matching spec)
NODES = list(range(1, 12))
PRIMARY_LINKS = [(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8)]
ALT_LINKS = [(3,9),(9,10),(10,5)]
CONGESTION_LINK = [(11,4)]  # Node 11 (code:10) connected to Node 4 (code:3)
ALL_LINKS = PRIMARY_LINKS + ALT_LINKS + CONGESTION_LINK

# Map 0-indexed (code) to 1-indexed (display)
def to_display(path):
    return [n + 1 for n in path]

def load_json(filepath):
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath) as f:
            content = f.read().strip()
            if not content:
                return None
            return json.loads(content)
    except json.JSONDecodeError:
        return None

def load_runtime_metrics():
    return load_json(os.path.join(RAW_DIR, "runtime_metrics.json"))

def load_ml_costs():
    return load_json(os.path.join(ML_DIR, "costs.json"))

def load_routing_decisions():
    return load_json(os.path.join(ROUTING_DIR, "routing.json"))

def load_processed_metrics():
    return load_json(os.path.join(PROCESSED_DIR, "metrics.json"))

def get_available_scenarios():
    return SCENARIOS

def get_link_cost_at_timestamp(ml_data, timestamp, src, dst):
    """Get routing cost for a specific link at a specific timestamp."""
    if not ml_data:
        return None
    for snap in ml_data.get("snapshots", []):
        if snap["timestamp"] == timestamp:
            for link in snap.get("links", []):
                if link["source"] == src and link["destination"] == dst:
                    return link["routing_cost"]
    return None

def get_all_costs_at_timestamp(ml_data, timestamp):
    """Get all link costs as {(src,dst): cost} at a timestamp."""
    costs = {}
    if not ml_data:
        return costs
    for snap in ml_data.get("snapshots", []):
        if snap["timestamp"] == timestamp:
            for link in snap.get("links", []):
                costs[(link["source"], link["destination"])] = link["routing_cost"]
    return costs

def scenario_description(scenario):
    descriptions = {
        "normal": "Baseline — stable network, no overrides. Traffic flows at 200 pkt/sec.",
        "congestion": "Congestion — Node 11 sends traffic through main chain (bottleneck 3→4). Node 1 traffic routed via alternate path.",
        "failure": "Link Failure — Link 4→5 is failed from the start. Traffic always uses alternate path.",
        "spike": "Traffic Spike — Burst of 1500 pkt/sec during t=5–10s.",
    }
    return descriptions.get(scenario, "")
def get_summary_metrics(runtime_data, t):
    """Calculate aggregate network metrics for a specific timestamp."""
    if not runtime_data or "snapshots" not in runtime_data:
        return 0, 0, 0, 0
    
    # Find snapshot for current_time
    snap = next((s for s in runtime_data["snapshots"] if s["timestamp"] == t), runtime_data["snapshots"][-1])
    
    links = snap.get("links", [])
    if not links:
        return 0, 0, 0, 0
        
    avg_loss = sum(l.get("packet_loss", 0) for l in links) / len(links) * 100
    avg_util = sum(l.get("link_utilization", 0) for l in links) / len(links) * 100
    total_thru = sum(l.get("throughput_mbps", 0) for l in links)
    max_queue = max(l.get("queue_utilization", 0) for l in links) * 100
    
    return avg_loss, avg_util, total_thru, max_queue

def get_routing_description(dec):
    """Generate a human-readable description for a routing decision."""
    action = dec["action"]
    if action == "REROUTED" or action == "IMMEDIATE_FAILOVER":
        new_path = " → ".join(map(str, to_display(dec["dijkstra_best_path"])))
        return f"Intelligence triggered reroute due to cost breach (Ratio: {dec['threshold_ratio']:.2f}x). Optimizing for path: <b>{new_path}</b>"
    elif action == "LINK_FAILED_AT_START":
        return "Critical link failure detected at 4→5. Routing through alternate path immediately."
    elif action == "THRESHOLD_BREACHED_NO_BETTER_PATH":
        return "Network congestion detected, but no superior physical path exists. Maintaining current route with throttle awareness."
    else:
        return f"Network state optimal. Current path cost: {dec.get('current_cost', 0):.2f}"
