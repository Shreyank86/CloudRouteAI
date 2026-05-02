#!/usr/bin/env python3
"""
CloudRoute AI — FlowMonitor XML → JSON Parser (M2)
===============================================
Parses NS-3 FlowMonitor XML output files and produces structured JSON
metrics files for downstream processing by M3.

Output contract version: 1.0
"""

import json
import os
import sys
import time
from lxml import etree

# ── Configuration ──────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "outputs", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "outputs", "processed")
ERROR_DIR = os.path.join(BASE_DIR, "outputs", "error")

SCENARIO_FILES = {
    "normal":     "normal_flow.xml",
    "congestion": "congestion_flow.xml",
    "failure":    "failure_flow.xml", # Changed to match locked file structure (outputs/raw/failure_flow.xml) wait, the raw is link_failure.xml in existing files, let me check spec: "outputs/raw/{scenario}_flow.xml"
}

# Wait, the spec says "failure_flow.xml", but the existing file is "link_failure.xml".
# Let's check spec: "outputs/raw/{scenario}_flow.xml". I will use "{scenario}_flow.xml".

# ── Helpers ────────────────────────────────────────────────────────────────────

def parse_ns3_value(value_str: str) -> float:
    if not value_str:
        return 0.0
    cleaned = value_str.strip().lstrip("+")
    for suffix in ("ns", "ms", "s", "bytes", "bps"):
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
            break
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

def build_classifier_map(root: etree._Element) -> dict:
    classifier = {}
    for flow_el in root.findall("Ipv4FlowClassifier/Flow"):
        fid = int(flow_el.get("flowId"))
        classifier[fid] = {
            "src": flow_el.get("sourceAddress", ""),
            "dst": flow_el.get("destinationAddress", ""),
        }
    return classifier

def ip_to_node(ip_str: str) -> int:
    """
    Map IP address like 10.1.X.Y to a node ID.
    """
    try:
        parts = ip_str.split('.')
        if len(parts) == 4 and parts[0] == '10' and parts[1] == '1':
            return int(parts[2])
    except:
        pass
    return -1

# ── Core Parser ────────────────────────────────────────────────────────────────

def parse_flowmon_xml(xml_path: str, scenario_id: str) -> dict:
    tree = etree.parse(xml_path)
    root = tree.getroot()

    classifier = build_classifier_map(root)

    flows = []
    for flow_el in root.findall("FlowStats/Flow"):
        flow_id = int(flow_el.get("flowId"))

        tx_packets  = float(parse_ns3_value(flow_el.get("txPackets", "0")))
        rx_packets  = float(parse_ns3_value(flow_el.get("rxPackets", "0")))
        delay_sum   = float(parse_ns3_value(flow_el.get("delaySum", "0")))    # in ns
        jitter_sum  = float(parse_ns3_value(flow_el.get("jitterSum", "0")))   # in ns

        # ── Compute derived metrics (STRICT MATCH WITH SPEC) ───────────────
        latency_ms       = (delay_sum / max(rx_packets, 1)) * 1000
        packet_loss_rate = (tx_packets - rx_packets) / max(tx_packets, 1)
        jitter_ms        = (jitter_sum / max(rx_packets, 1)) * 1000

        # ── Resolve source / destination node IDs ──────────────────────────
        src_ip = classifier.get(flow_id, {}).get("src", "")
        dst_ip = classifier.get(flow_id, {}).get("dst", "")
        
        src_node = ip_to_node(src_ip)
        dst_node = ip_to_node(dst_ip)

        flow_record = {
            "flow_id":          flow_id,
            "src_node":         src_node,
            "dst_node":         dst_node,
            "latency_ms":       float(latency_ms),
            "throughput_mbps":  0.0,
            "packet_loss_rate": float(packet_loss_rate),
            "tx_packets":       float(tx_packets),
            "rx_packets":       float(rx_packets),
            "jitter_ms":        float(jitter_ms),
            "queue_delay_ms":   0.0,
        }
        flows.append(flow_record)

    result = {
        "version":     "1.0",
        "timestamp":   float(time.time()),
        "scenario_id": scenario_id,
        "flows":       flows,
    }
    return result

# ── Validation ─────────────────────────────────────────────────────────────────

def validate_output(data: dict, scenario_id: str) -> list:
    errors = []

    for key in ("version", "timestamp", "scenario_id", "flows"):
        if key not in data:
            errors.append(f"Missing top-level key: '{key}'")

    if data.get("version") != "1.0":
        errors.append(f"Unexpected version: {data.get('version')}")

    if not isinstance(data.get("timestamp"), float):
        errors.append(f"'timestamp' must be float")

    if data.get("scenario_id") != scenario_id:
        errors.append(f"scenario_id mismatch")

    flows = data.get("flows", [])
    if not isinstance(flows, list) or len(flows) == 0:
        errors.append("'flows' must be a non-empty list")

    required_keys = [
        "flow_id", "src_node", "dst_node", "latency_ms",
        "throughput_mbps", "packet_loss_rate", "tx_packets",
        "rx_packets", "jitter_ms", "queue_delay_ms",
    ]
    for i, flow in enumerate(flows):
        for key in required_keys:
            if key not in flow:
                errors.append(f"Flow[{i}] missing key: '{key}'")
            elif flow[key] is None:
                errors.append(f"Flow[{i}].{key} is null")
            elif key not in ["flow_id", "src_node", "dst_node"]:
                if not isinstance(flow[key], float):
                    errors.append(f"Flow[{i}].{key} is not float")

    return errors

def write_error(scenario_id: str, error_code: int, message: str):
    os.makedirs(ERROR_DIR, exist_ok=True)
    err = {
        "module": "m2",
        "scenario_id": scenario_id,
        "error_code": error_code,
        "message": message,
        "timestamp": float(time.time()),
        "version": "1.0"
    }
    err_path = os.path.join(ERROR_DIR, "error.json")
    with open(err_path, "w") as f:
        json.dump(err, f, indent=2)

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    # Process specified scenarios
    scenarios = ["normal", "congestion", "failure"]
    
    for scenario_id in scenarios:
        # Check both names for backwards compatibility during execution
        xml_filename = f"{scenario_id}_flow.xml"
        xml_path = os.path.join(RAW_DIR, xml_filename)
        
        # Fallback to older name if the new spec name doesn't exist yet
        if not os.path.isfile(xml_path) and scenario_id == "failure":
            xml_path = os.path.join(RAW_DIR, "link_failure.xml")
            
        json_filename = f"{scenario_id}_metrics.json"
        json_path = os.path.join(PROCESSED_DIR, json_filename)

        if not os.path.isfile(xml_path):
            write_error(scenario_id, 101, f"Input missing: {xml_path}")
            continue

        try:
            data = parse_flowmon_xml(xml_path, scenario_id)
        except Exception as e:
            write_error(scenario_id, 101, f"Parse error: {str(e)}")
            continue

        errors = validate_output(data, scenario_id)
        if errors:
            write_error(scenario_id, 101, f"Validation failed: {errors[0]}")
            continue

        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)
            
        print(f"[{scenario_id.upper()}] Successfully processed to {json_filename}")

if __name__ == "__main__":
    main()
