try:
    from telemetry.telemetry_storage import storage
except ImportError:
    from telemetry_storage import storage

# Configure thresholds in Mbps
LOAD_THRESHOLDS = {
    "low": 20.0,
    "medium": 80.0,
    "high": 150.0
}

def get_total_client_throughput(timeout=5.0):
    """Get the sum of throughput (Mbps) across all active clients."""
    return storage.get_aggregated_throughput(timeout_sec=timeout)

def map_throughput_to_load(throughput_mbps):
    """
    Map total throughput to a load tier:
    - 0-20 Mbps: Low Load
    - 20-80 Mbps: Medium Load
    - 80-150 Mbps: High Load
    - 150+ Mbps: Critical Load
    """
    if throughput_mbps < LOAD_THRESHOLDS["low"]:
        return "Low Load"
    elif throughput_mbps < LOAD_THRESHOLDS["medium"]:
        return "Medium Load"
    elif throughput_mbps < LOAD_THRESHOLDS["high"]:
        return "High Load"
    else:
        return "Critical Load"

def get_aggregate_metrics(timeout=5.0):
    """Get aggregated metrics dict for dashboard consumption."""
    active_clients = storage.get_active_clients(timeout_sec=timeout)
    throughput = sum(c["total_throughput_mbps"] for c in active_clients)
    load_level = map_throughput_to_load(throughput)
    
    return {
        "total_throughput_mbps": round(throughput, 2),
        "active_clients_count": len(active_clients),
        "load_level": load_level
    }
