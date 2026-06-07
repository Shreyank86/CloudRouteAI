import time
import math
import heapq
import sys
import os
import json
from datetime import datetime
from context_engine import FutureEventRepository, ContextAwareValidationLayer, DecisionIntelligenceModule

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "ml_model"))

RAW_DIR = os.path.join(BASE_DIR, "outputs", "raw")
ML_DIR = os.path.join(BASE_DIR, "outputs", "ml")
ROUTING_DIR = os.path.join(BASE_DIR, "outputs", "routing")
PROCESSED_DIR = os.path.join(BASE_DIR, "outputs", "processed")
LIVE_DIR = os.path.join(BASE_DIR, "outputs", "live")
LIVE_LOG_FILE = os.path.join(LIVE_DIR, "live_telemetry_log.jsonl")


# ─────────────────────────────────────────────────────────────────────────────
# Persistent Live Telemetry Helpers
# ─────────────────────────────────────────────────────────────────────────────

def append_live_snapshot(sim):
    """Append one JSON record to the persistent live telemetry log."""
    os.makedirs(LIVE_DIR, exist_ok=True)
    state = sim.get_state()
    links = state["links"]

    # Aggregate KPIs from current link states
    active_links = [l for l in links if l["capacity"] > 0]
    if not active_links:
        return

    avg_loss = sum(l["loss"] for l in active_links) / len(active_links) * 100
    avg_util = sum(l["throughput"] / l["capacity"] for l in active_links) / len(active_links) * 100
    total_thr = sum(l["throughput"] for l in active_links)
    peak_cong = max(l["queue"] for l in active_links) * 100

    record = {
        "timestamp": float(sim.time_step * 2.0),
        "wall_time": datetime.utcnow().isoformat(),
        "avg_packet_loss_pct": round(avg_loss, 4),
        "avg_utilization_pct": round(avg_util, 4),
        "total_throughput_mbps": round(total_thr, 4),
        "peak_congestion_pct": round(peak_cong, 4),
        "flows": {
            fid: {
                "volume": f["volume"],
                "status": f.get("status", "Idle"),
            }
            for fid, f in sim.flows.items()
        },
    }

    with open(LIVE_LOG_FILE, "a") as fh:
        fh.write(json.dumps(record) + "\n")


def clear_live_log():
    """Truncate the live telemetry log file to zero bytes."""
    os.makedirs(LIVE_DIR, exist_ok=True)
    with open(LIVE_LOG_FILE, "w") as fh:
        pass  # truncate


def load_live_log():
    """Return all records from the live telemetry log as a list of dicts."""
    if not os.path.exists(LIVE_LOG_FILE):
        return []
    records = []
    with open(LIVE_LOG_FILE, "r") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records

class LiveNetworkSimulator:
    def __init__(self):
        self.nodes = list(range(1, 20))
        
        # 17-node Hybrid Mesh + Spine-Leaf  (+2 buffer nodes)
        self.links = [
            # Core Mesh (15,16,17)
            {"src": 15, "dst": 16, "capacity": 1000.0, "base_delay": 5.0},
            {"src": 16, "dst": 17, "capacity": 1000.0, "base_delay": 5.0},
            {"src": 15, "dst": 17, "capacity": 1000.0, "base_delay": 5.0},
            
            # Spines to Core
            {"src": 1, "dst": 15, "capacity": 500.0, "base_delay": 2.0},
            {"src": 1, "dst": 16, "capacity": 500.0, "base_delay": 2.0},
            {"src": 4, "dst": 15, "capacity": 500.0, "base_delay": 2.0},
            {"src": 4, "dst": 17, "capacity": 500.0, "base_delay": 2.0},
            {"src": 7, "dst": 16, "capacity": 500.0, "base_delay": 2.0},
            {"src": 7, "dst": 17, "capacity": 500.0, "base_delay": 2.0},
            {"src": 10, "dst": 15, "capacity": 500.0, "base_delay": 2.0},
            {"src": 10, "dst": 16, "capacity": 500.0, "base_delay": 2.0},
            {"src": 10, "dst": 17, "capacity": 500.0, "base_delay": 2.0},
            {"src": 13, "dst": 16, "capacity": 500.0, "base_delay": 2.0},
            
            # Buffer Nodes
            {"src": 15, "dst": 18, "capacity": 1000.0, "base_delay": 5.0},
            {"src": 16, "dst": 18, "capacity": 1000.0, "base_delay": 5.0},
            {"src": 16, "dst": 19, "capacity": 1000.0, "base_delay": 5.0},
            {"src": 17, "dst": 19, "capacity": 1000.0, "base_delay": 5.0},
            
            # Leaves to Spines
            {"src": 2, "dst": 1, "capacity": 100.0, "base_delay": 0.5},
            {"src": 3, "dst": 1, "capacity": 100.0, "base_delay": 0.5},
            {"src": 5, "dst": 4, "capacity": 100.0, "base_delay": 0.5},
            {"src": 6, "dst": 4, "capacity": 100.0, "base_delay": 0.5},
            {"src": 8, "dst": 7, "capacity": 100.0, "base_delay": 0.5},
            {"src": 9, "dst": 7, "capacity": 100.0, "base_delay": 0.5},
            {"src": 11, "dst": 10, "capacity": 100.0, "base_delay": 0.5},
            {"src": 12, "dst": 10, "capacity": 100.0, "base_delay": 0.5},
            {"src": 14, "dst": 13, "capacity": 100.0, "base_delay": 0.5},
        ]
        
        # Make bidirectional
        self.bidi_links = []
        for l in self.links:
            self.bidi_links.append(l)
            self.bidi_links.append({"src": l["dst"], "dst": l["src"], "capacity": l["capacity"], "base_delay": l["base_delay"]})
            
        self.link_states = {(l["src"], l["dst"]): {"throughput": 0.0, "queue": 0.0, "loss": 0.0, "latency": l["base_delay"], "cost": 10.0, "capacity": l["capacity"]} for l in self.bidi_links}
        
        # ML model initialization
        self.model = None
        self.preprocessor = None
        try:
            from predict import train_routing_model
            self.model, self.preprocessor = train_routing_model()
            print("[LiveEngine] ML model loaded successfully.")
        except Exception as e:
            print("[LiveEngine] ML model loading failed:", e)

        # Flows definitions
        self.flows = {
            "flow_1": {"src": 2, "dst": 8, "volume": 0, "paths": []},
            "flow_2": {"src": 5, "dst": 11, "volume": 0, "paths": []},
        }
        self.time_step = 0
        self.history = {
            "snapshots": [],
            "costs": [],
            "routing": []
        }

        # Context-Aware modules — initialised ONCE, preserved across steps
        self.event_repo = FutureEventRepository()
        self.context_layer = ContextAwareValidationLayer(lambda_weight=100.0)
        self.di_module = DecisionIntelligenceModule()

        self.update_routing() 
        
    def set_flow(self, flow_id, src, dst, volume):
        if flow_id not in self.flows or self.flows[flow_id]["src"] != src or self.flows[flow_id]["dst"] != dst:
            self.flows[flow_id] = {"src": src, "dst": dst, "volume": volume, "paths": []}
        else:
            self.flows[flow_id]["volume"] = volume
            
    def get_k_shortest_paths(self, src, dst, k=2):
        costs = {k: v["cost"] for k, v in self.link_states.items()}
        
        def run_dijkstra(current_costs):
            dist = {i: float('inf') for i in self.nodes}
            prev = {i: -1 for i in self.nodes}
            dist[src] = 0
            pq = [(0, src)]
            while pq:
                d, u = heapq.heappop(pq)
                if d > dist[u]: continue
                if u == dst: break
                for v in self.nodes:
                    if (u, v) in current_costs:
                        c = current_costs[(u, v)]
                        if dist[u] + c < dist[v]:
                            dist[v] = dist[u] + c
                            prev[v] = u
                            heapq.heappush(pq, (dist[v], v))
            path = []
            curr = dst
            while curr != -1:
                path.append(curr)
                curr = prev[curr]
            path.reverse()
            return path if path and path[0] == src else []

        paths = []
        import copy
        working_costs = copy.deepcopy(costs)
        
        for _ in range(k):
            p = run_dijkstra(working_costs)
            if not p: break
            pcost = sum(working_costs[(p[i], p[i+1])] for i in range(len(p)-1))
            paths.append({"path": p, "cost": pcost})
            
            # remove bottleneck edge to find alternative path
            if len(p) > 2:
                max_c = -1
                max_e = None
                for i in range(len(p)-1):
                    e = (p[i], p[i+1])
                    if costs[e] > max_c:
                        max_c = costs[e]
                        max_e = e
                if max_e:
                    working_costs[max_e] = 99999.0
                    
        return paths

    # ──────────────────────────────────────────────────────
    # Context-Aware path evaluation (adds FRS + penalty)
    # ──────────────────────────────────────────────────────
    def get_context_aware_shortest_paths(self, src, dst, k=2):
        base_paths = self.get_k_shortest_paths(src, dst, k=k + 2)
        current_time = self.time_step * 2.0
        events = self.event_repo.get_upcoming_events(current_time)

        for p in base_paths:
            p["base_cost"] = p["cost"]
            frs, event = self.context_layer.evaluate_path(p["path"], current_time, events)
            severity = event["severity"] if event else 0.0
            penalty = self.context_layer.calculate_penalty(frs, severity)
            p["penalty"] = penalty
            p["cost"] += penalty
            p["frs"] = frs
            p["event"] = event

        base_paths.sort(key=lambda x: x["cost"])
        return base_paths[:k]

    # ──────────────────────────────────────────────────────
    # Path telemetry helper for XAI consumption
    # ──────────────────────────────────────────────────────
    def get_path_telemetry(self, path):
        """Compute latency, max congestion, cumulative packet loss, and ML cost for a path."""
        lat = 0.0
        congestions = []
        losses = []
        ml_cost = 0.0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            state = self.link_states.get((u, v)) or self.link_states.get((v, u))
            if state:
                lat += state.get("latency", 2.0)
                congestions.append(state.get("queue", 0.0))
                losses.append(state.get("loss", 0.0))
                ml_cost += state.get("cost", 10.0)
            else:
                lat += 2.0
                congestions.append(0.0)
                losses.append(0.0)
                ml_cost += 10.0
        max_cong = max(congestions) if congestions else 0.0
        avg_cong = sum(congestions) / len(congestions) if congestions else 0.0
        cum_loss = 1.0 - math.prod(1.0 - l for l in losses) if losses else 0.0
        return {
            "latency": round(lat, 2),
            "max_congestion": round(max_cong, 4),
            "avg_congestion": round(avg_cong, 4),
            "packet_loss": round(cum_loss, 4),
            "ml_cost": round(ml_cost, 2),
        }

    def update_routing(self):
        leaf_nodes = [2, 5, 8, 11, 14]
        for f_id, f in self.flows.items():
            if f["volume"] == 0:
                f["paths"] = []
                f["status"] = "Idle"
                continue
                
            src = f["src"]
            dst = f["dst"]
            
            # Evaluate k-shortest paths to actual destination (context-aware)
            k_paths = self.get_context_aware_shortest_paths(src, dst, k=2)
            if not k_paths: continue
            
            c_primary = k_paths[0]["cost"]
            p_primary = k_paths[0]["path"]

            # ── Collect all candidate info for DI logging ──
            all_candidates = []
            for idx, kp in enumerate(k_paths):
                telem = self.get_path_telemetry(kp["path"])
                all_candidates.append({
                    "rank": idx + 1,
                    "path": kp["path"],
                    "latency": telem["latency"],
                    "congestion": telem["avg_congestion"],
                    "packet_loss": telem["packet_loss"],
                    "ml_cost": telem["ml_cost"],
                    "frs": kp.get("frs", 0.0),
                    "penalty": kp.get("penalty", 0.0),
                    "base_cost": kp.get("base_cost", telem["ml_cost"]),
                    "final_score": kp["cost"],
                    "event": {
                        "type": kp["event"]["type"] if kp.get("event") else "None",
                        "severity": kp["event"]["severity"] if kp.get("event") else 0.0,
                    } if True else None,
                })

            routing_tier = "Tier 1: Normal"
            
            # TIER 3: Extreme Congestion -> Cross-Datacenter Split (Mega-Split)
            if f["volume"] >= 600 or c_primary >= 300.0:
                alt_dsts = [n for n in leaf_nodes if n != src and n != dst]
                best_alt_dst = None
                best_alt_cost = float('inf')
                best_alt_path = None
                
                for ad in alt_dsts:
                    alt_paths = self.get_context_aware_shortest_paths(src, ad, k=1)
                    if alt_paths and alt_paths[0]["cost"] < best_alt_cost:
                        best_alt_cost = alt_paths[0]["cost"]
                        best_alt_path = alt_paths[0]["path"]
                        best_alt_dst = ad
                        
                if best_alt_path and best_alt_cost < 9000.0:
                    sibling_map = {2: 3, 3: 2, 5: 6, 6: 5, 8: 9, 9: 8, 11: 12, 12: 11}
                    
                    # 1. Primary paths (dst & its sibling)
                    primary_paths_to_use = [{"path": p_primary, "weight": 0.0, "type": "primary"}]
                    dst_sibling = sibling_map.get(dst)
                    if dst_sibling:
                        ds_paths = self.get_context_aware_shortest_paths(src, dst_sibling, k=1)
                        if ds_paths and ds_paths[0]["cost"] < 9000.0:
                            primary_paths_to_use.append({"path": ds_paths[0]["path"], "weight": 0.0, "type": "primary"})
                            
                    # 2. Alternate paths (best_alt & its sibling)
                    alt_paths_to_use = [{"path": best_alt_path, "weight": 0.0, "type": "rerouted"}]
                    alt_sibling = sibling_map.get(best_alt_dst)
                    if alt_sibling:
                        as_paths = self.get_context_aware_shortest_paths(src, alt_sibling, k=1)
                        if as_paths and as_paths[0]["cost"] < 9000.0:
                            alt_paths_to_use.append({"path": as_paths[0]["path"], "weight": 0.0, "type": "rerouted"})
                            
                    # Assign weights based on relative cost of DCs
                    w_primary_total = max(0.2, best_alt_cost / (c_primary + best_alt_cost))
                    w_alt_total = 1.0 - w_primary_total
                    
                    for p in primary_paths_to_use:
                        p["weight"] = round(w_primary_total / len(primary_paths_to_use), 2)
                    for p in alt_paths_to_use:
                        p["weight"] = round(w_alt_total / len(alt_paths_to_use), 2)
                        
                    f["paths"] = primary_paths_to_use + alt_paths_to_use
                    
                    dc_id_primary = (dst + 1) // 3
                    dc_id_alt = (best_alt_dst + 1) // 3
                    
                    msg_pri = f"{dst},{dst_sibling}" if dst_sibling else f"{dst}"
                    msg_alt = f"{best_alt_dst},{alt_sibling}" if alt_sibling else f"{best_alt_dst}"
                    
                    f["status"] = f"Mega-Split: DC{dc_id_primary} ({msg_pri}) & DC{dc_id_alt} ({msg_alt})"
                    routing_tier = "Tier 3: Cross-DC Split"

                    # Log enriched DI decision
                    self._log_di(f_id, f, k_paths, all_candidates, routing_tier)
                    continue # Skip lower tiers
                    
            # TIER 2: Moderate Congestion -> Same-Datacenter Partial Reroute (Load Balance to Sibling Leaf)
            sibling_map = {2: 3, 3: 2, 5: 6, 6: 5, 8: 9, 9: 8, 11: 12, 12: 11}
            sibling_node = sibling_map.get(dst)
            
            if (f["volume"] >= 150 or c_primary > 50.0) and sibling_node:
                sibling_paths = self.get_context_aware_shortest_paths(src, sibling_node, k=1)
                if sibling_paths and sibling_paths[0]["cost"] < 9000.0:
                    c2 = sibling_paths[0]["cost"]
                    w1 = c2 / (c_primary + c2)
                    w2 = c_primary / (c_primary + c2)
                    f["paths"] = [
                        {"path": p_primary, "weight": round(w1, 2), "type": "primary"},
                        {"path": sibling_paths[0]["path"], "weight": round(w2, 2), "type": "rerouted"}
                    ]
                    f["status"] = f"Same-DC Load Balance: Nodes {dst} & {sibling_node} ({int(w1*100)}% / {int(w2*100)}%)"
                    routing_tier = "Tier 2: Sibling Load Balance"
                    self._log_di(f_id, f, k_paths, all_candidates, routing_tier)
                    continue
            elif (f["volume"] >= 150 or c_primary > 50.0) and len(k_paths) > 1 and k_paths[1]["cost"] < 9000.0:
                # Fallback for DC5 (node 14) which has no sibling
                c2 = k_paths[1]["cost"]
                w1 = c2 / (c_primary + c2)
                w2 = c_primary / (c_primary + c2)
                f["paths"] = [
                    {"path": p_primary, "weight": round(w1, 2), "type": "primary"},
                    {"path": k_paths[1]["path"], "weight": round(w2, 2), "type": "rerouted"}
                ]
                f["status"] = f"Same-DC Core Reroute ({int(w1*100)}% / {int(w2*100)}%)"
                routing_tier = "Tier 2: Sibling Load Balance"
                self._log_di(f_id, f, k_paths, all_candidates, routing_tier)
                continue

            # TIER 1: Low Traffic -> Normal Path
            f["paths"] = [{"path": p_primary, "weight": 1.0, "type": "primary"}]
            f["status"] = "Normal Path (100%)"
            routing_tier = "Tier 1: Normal"
            self._log_di(f_id, f, k_paths, all_candidates, routing_tier)

    def _log_di(self, f_id, f, k_paths, all_candidates, routing_tier):
        """Log an enriched decision to the DI module."""
        best_path = f["paths"][0]["path"] if f["paths"] else []
        event_type = k_paths[0]["event"]["type"] if k_paths[0].get("event") else "None"
        event_severity = k_paths[0]["event"]["severity"] if k_paths[0].get("event") else 0.0
        time_until = max(0.0, k_paths[0]["event"]["start_time"] - (self.time_step * 2.0)) if k_paths[0].get("event") else 0.0

        # Build traffic split detail
        split_detail = []
        for p_info in f["paths"]:
            telem = self.get_path_telemetry(p_info["path"])
            split_detail.append({
                "path": p_info["path"],
                "weight": p_info["weight"],
                "type": p_info["type"],
                "volume_mbps": round(f["volume"] * p_info["weight"], 1),
                "percent": round(p_info["weight"] * 100, 1),
                "latency": telem["latency"],
                "congestion": telem["avg_congestion"],
                "ml_cost": telem["ml_cost"],
            })

        self.di_module.log_decision(
            timestamp=self.time_step * 2.0,
            flow_id=f_id,
            current_metrics={
                "base_cost": k_paths[0].get("base_cost", k_paths[0]["cost"]),
                "volume": f["volume"],
            },
            context_metrics={
                "future_risk_score": k_paths[0].get("frs", 0.0),
                "future_penalty": k_paths[0].get("penalty", 0.0),
                "event_type": event_type,
                "event_severity": event_severity,
                "time_until_event": time_until,
            },
            routing_metrics={
                "routing_tier": routing_tier,
                "candidate_paths": all_candidates,
                "selected_path": best_path,
                "active_paths": split_detail,
                "final_route_score": k_paths[0]["cost"],
            },
            confidence_metrics={
                "decision_confidence": max(0.0, 1.0 - k_paths[0].get("frs", 0.0)),
                "route_sustainability_score": 1.0 - k_paths[0].get("frs", 0.0),
            },
        )


    def step(self):
        self.time_step += 1
        
        # 1. Reset link offered throughput
        offered = {k: 0.0 for k in self.link_states.keys()}
        
        # 2. Add traffic from active flows
        for f_id, f in self.flows.items():
            vol = f["volume"]
            if vol > 0:
                for p_info in f["paths"]:
                    p = p_info["path"]
                    w = p_info["weight"]
                    flow_vol = vol * w
                    for i in range(len(p)-1):
                        offered[(p[i], p[i+1])] += flow_vol

        # 3. Network Physics & ML Cost Prediction
        current_time = self.time_step * 2.0
        active_events = self.event_repo.get_active_events(current_time)

        for link, state in self.link_states.items():
            cap = state["capacity"]

            # Apply active event effects physically
            is_failed = False
            for e in active_events:
                if e["type"] == "network_failure" and (link in e["affected_links"] or (link[1], link[0]) in e["affected_links"]):
                    is_failed = True
                if e["type"] == "traffic_burst" and (link in e["affected_links"] or (link[1], link[0]) in e["affected_links"]):
                    offered[link] += cap * 1.5 * e["severity"]

            if is_failed:
                state["throughput"] = 0.0
                state["queue"] = 1.0
                state["loss"] = 1.0
                state["latency"] = 9999.0
                state["cost"] = 9999.0
                continue

            thru = min(cap, offered[link])
            
            queue = 0.0
            if offered[link] > cap:
                queue = min(1.0, (offered[link] - cap) / (cap * 0.5))
                
            loss = 0.0
            if queue > 0.8:
                loss = (queue - 0.8) * 0.5
                
            # fetch base delay
            delay = 2.0
            for l in self.bidi_links:
                if l["src"] == link[0] and l["dst"] == link[1]:
                    delay = l["base_delay"]
                    break
                    
            lat = delay + (queue * 50.0)
            
            state["throughput"] = thru
            state["queue"] = queue
            state["loss"] = loss
            state["latency"] = lat
            
            # Continuous ML Evaluation
            if self.model and self.preprocessor:
                link_snap = {
                    "queue_utilization": queue,
                    "delay_ms": lat,
                    "packet_loss": loss
                }
                # The synthetic M3 model expects exactly these 3 features
                features = self.preprocessor.extract_features(link_snap)
                scaled = self.preprocessor.transform([features])
                predicted_cost = float(self.model.predict(scaled)[0])
                state["cost"] = max(1.0, predicted_cost)
            else:
                state["cost"] = 10.0 + (queue * 1000.0) + (lat * 5.0) + (loss * 5000.0)
                
        # 4. Partial rerouting based on new ML costs
        # NOTE: event_repo / context_layer / di_module are NOT re-initialised here
        #       so that decision logs and scheduled events persist across steps.
        self.update_routing()

        # 5. Record History
        timestamp = float(self.time_step * 2.0)
        
        links_data = []
        cost_links = []
        for l_key, state in self.link_states.items():
            u, v = l_key
            links_data.append({
                "source": u, "destination": v,
                "throughput_mbps": state["throughput"],
                "queue_utilization": state["queue"],
                "packet_loss": state["loss"],
                "delay_ms": state["latency"],
                "capacity_mbps": state["capacity"],
                "link_utilization": state["throughput"] / state["capacity"] if state["capacity"] > 0 else 0.0
            })
            cost_links.append({
                "source": u, "destination": v,
                "routing_cost": state["cost"]
            })
            
        self.history["snapshots"].append({
            "timestamp": timestamp,
            "links": links_data
        })
        self.history["costs"].append({
            "timestamp": timestamp,
            "links": cost_links
        })
        
        # Save routing decision for temporal analysis
        if "DC1_to_DC4" in self.flows:
            p_info = self.flows["DC1_to_DC4"]["paths"]
            decision = {
                "timestamp": timestamp,
                "action": "PARTIAL_REROUTE" if len(p_info) > 1 else "STABLE",
                "current_path": p_info[0]["path"] if p_info else [],
                "current_paths_partial": p_info,
                "dijkstra_best_path": p_info[0]["path"] if p_info else [],
                "rerouted": len(p_info) > 1
            }
            self.history["routing"].append(decision)

    def get_state(self):
        return {
            "time": self.time_step,
            "flows": self.flows,
            "links": [{"src": k[0], "dst": k[1], **v} for k, v in self.link_states.items()]
        }

    def get_aggregate_metrics(self):
        """Return real-time aggregated KPI values from the current link states.
        Returns (avg_loss_pct, avg_util_pct, total_throughput_mbps, peak_congestion_pct).
        Returns (0, 0, 0, 0) if no data yet.
        """
        if self.time_step == 0:
            return 0.0, 0.0, 0.0, 0.0
        active = [
            v for v in self.link_states.values()
            if v["capacity"] > 0
        ]
        if not active:
            return 0.0, 0.0, 0.0, 0.0
        avg_loss = sum(s["loss"] for s in active) / len(active) * 100
        avg_util = sum(s["throughput"] / s["capacity"] for s in active) / len(active) * 100
        total_thr = sum(s["throughput"] for s in active)
        peak_cong = max(s["queue"] for s in active) * 100
        return avg_loss, avg_util, total_thr, peak_cong
