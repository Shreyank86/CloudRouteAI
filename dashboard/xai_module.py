"""
CloudRouteAI — Explainable AI (XAI) Module
============================================
Observational module that parses decision intelligence logs and network metrics
to generate plain-English explanations and explainability analytics.

This module does NOT influence routing decisions.  It only explains them.
"""

import math

# ─── Offline scenario paths (NetworkX / NS-3 8-node topology) ───
PRIMARY_PATH_OFFLINE = [0, 1, 2, 3, 4, 5, 6, 7]
ALT_PATH_OFFLINE     = [0, 1, 2, 8, 9, 4, 5, 6, 7]


def to_display_offline(path):
    return [n + 1 for n in path]


# ──────────────────────────────────────────────────────────────────
# Offline Event Configuration
# ──────────────────────────────────────────────────────────────────
def get_offline_events_config(scenario, routing_decisions):
    """Detect event details based on the scenario and routing decisions."""
    event = None
    if scenario == "failure":
        fail_time = 8.0
        for dec in routing_decisions:
            if dec.get("action") in ["IMMEDIATE_FAILOVER", "REROUTED"] or dec.get("rerouted", False):
                fail_time = dec["timestamp"]
                break
        event = {
            "type": "Link Failure",
            "severity": 1.0,
            "start_time": fail_time,
            "duration": 12.0,
            "affected_links": [(3, 4)],
            "description": "A physical link failure on the core trunk 4→5 is scheduled."
        }
    elif scenario == "congestion":
        event = {
            "type": "Network Congestion",
            "severity": 0.75,
            "start_time": 4.0,
            "duration": 16.0,
            "affected_links": [(3, 4)],
            "description": "Persistent cross-traffic congestion is active on link 4→5."
        }
    elif scenario == "spike":
        event = {
            "type": "Traffic Spike",
            "severity": 0.85,
            "start_time": 5.0,
            "duration": 5.0,
            "affected_links": [(0, 1), (1, 2), (2, 3), (3, 4)],
            "description": "A high-volume traffic burst (1500 packets/sec) is scheduled."
        }
    return event


# ──────────────────────────────────────────────────────────────────
# Offline XAI Metrics
# ──────────────────────────────────────────────────────────────────
def get_offline_xai_metrics(current_time, scenario, runtime_data, ml_data, routing_data):
    """Explainability metrics for offline NetworkX / NS-3 simulation at current_time."""
    decisions = routing_data.get("decisions", []) if routing_data else []

    # 1. Find routing decision at current_time
    current_dec = None
    for dec in decisions:
        if dec["timestamp"] == current_time:
            current_dec = dec
            break
    if not current_dec and decisions:
        past_decs = [d for d in decisions if d["timestamp"] <= current_time]
        current_dec = past_decs[-1] if past_decs else decisions[0]

    selected_path = current_dec["current_path"] if current_dec else PRIMARY_PATH_OFFLINE
    is_rerouted = current_dec["rerouted"] if current_dec else False
    action = current_dec["action"] if current_dec else "STABLE"

    candidates = [PRIMARY_PATH_OFFLINE, ALT_PATH_OFFLINE]

    # Runtime snapshot lookup
    snap = None
    if runtime_data and "snapshots" in runtime_data:
        snaps = runtime_data["snapshots"]
        snap = next((s for s in snaps if s["timestamp"] == current_time), None)
        if not snap and snaps:
            snap = snaps[-1]

    ml_snap = None
    if ml_data and "snapshots" in ml_data:
        ml_snaps = ml_data["snapshots"]
        ml_snap = next((s for s in ml_snaps if s["timestamp"] == current_time), None)
        if not ml_snap and ml_snaps:
            ml_snap = ml_snaps[-1]

    link_metrics = {}
    if snap:
        for link in snap.get("links", []):
            link_metrics[(link["source"], link["destination"])] = link

    link_costs = {}
    if ml_snap:
        for link in ml_snap.get("links", []):
            link_costs[(link["source"], link["destination"])] = link["routing_cost"]

    # Future Event Impact
    event = get_offline_events_config(scenario, decisions)
    frs = 0.0
    penalty = 0.0
    time_until = 0.0
    event_active = False

    if event:
        time_until = max(0.0, event["start_time"] - current_time)
        event_active = event["start_time"] <= current_time <= (event["start_time"] + event["duration"])
        if event_active:
            frs = event["severity"]
        elif time_until <= 10.0:
            proximity = 1.0 / (1.0 + (time_until / 5.0))
            frs = event["severity"] * proximity
        penalty = 100.0 * frs * event["severity"]

    # Populate candidates
    candidate_paths_data = []
    for path in candidates:
        path_name = "Primary Route" if path == PRIMARY_PATH_OFFLINE else "Alternate Route"
        lat = 0.0; congestions = []; losses = []; base_cost = 0.0; ml_cost = 0.0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            ld = link_metrics.get((u, v))
            if ld:
                lat += ld.get("delay_ms", 2.0)
                congestions.append(ld.get("queue_utilization", 0.0))
                losses.append(ld.get("packet_loss", 0.0))
            else:
                lat += 2.0; congestions.append(0.0); losses.append(0.0)
            base_cost += 10.0
            ml_cost += link_costs.get((u, v), 10.0)

        avg_cong = sum(congestions) / len(congestions) if congestions else 0.0
        success_prob = 1.0
        for loss in losses:
            success_prob *= (1.0 - loss)
        path_loss = 1.0 - success_prob

        path_frs = frs if path == PRIMARY_PATH_OFFLINE else 0.0
        path_penalty = penalty if path == PRIMARY_PATH_OFFLINE else 0.0
        final_score = ml_cost + path_penalty

        candidate_paths_data.append({
            "name": path_name,
            "path": path,
            "display_path": " → ".join(map(str, to_display_offline(path))),
            "latency": round(lat, 2),
            "congestion": round(avg_cong * 100, 1),
            "packet_loss": round(path_loss * 100, 2),
            "base_cost": round(base_cost, 1),
            "ml_cost": round(ml_cost, 1),
            "frs": round(path_frs, 2),
            "penalty": round(path_penalty, 1),
            "final_score": round(final_score, 1),
        })

    sel_data = next((c for c in candidate_paths_data if c["path"] == selected_path), candidate_paths_data[0])
    rej_data = next((c for c in candidate_paths_data if c["path"] != selected_path), candidate_paths_data[1])

    # Metric contribution decomposition
    sel_lat_cost = sum(5.0 * link_metrics.get((selected_path[i], selected_path[i + 1]), {}).get("delay_ms", 2.0) for i in range(len(selected_path) - 1))
    sel_cong_cost = sum(
        1000.0 * link_metrics.get((selected_path[i], selected_path[i + 1]), {}).get("queue_utilization", 0.0)
        + 5000.0 * link_metrics.get((selected_path[i], selected_path[i + 1]), {}).get("packet_loss", 0.0)
        for i in range(len(selected_path) - 1)
    )
    sel_base_cost = (len(selected_path) - 1) * 10.0
    sel_frs_cost = sel_data["penalty"]

    total_decomp = sel_lat_cost + sel_cong_cost + sel_base_cost + sel_frs_cost
    if total_decomp > 0:
        latency_contrib = (sel_lat_cost / total_decomp) * 100.0
        congestion_contrib = (sel_cong_cost / total_decomp) * 100.0
        risk_contrib = (sel_frs_cost / total_decomp) * 100.0
        cost_contrib = (sel_base_cost / total_decomp) * 100.0
    else:
        latency_contrib = congestion_contrib = risk_contrib = cost_contrib = 25.0

    # Confidence & Sustainability
    confidence = 100.0 - (sel_data["frs"] * 60.0) - (sel_data["congestion"] * 0.3) - (sel_data["packet_loss"] * 2.0)
    confidence = max(10.0, min(99.0, confidence))
    sustainability = 100.0 - (sel_data["congestion"] * 0.4) - (sel_data["frs"] * 50.0)
    if selected_path == PRIMARY_PATH_OFFLINE and rej_data["final_score"] < 500.0:
        sustainability += 10.0
    sustainability = max(10.0, min(99.0, sustainability))

    # Plain-English explanations
    confidence_expl = _explain_confidence(confidence, sel_data["frs"])
    sustainability_expl = _explain_sustainability(sustainability)
    selection_reason, rejection_reason = _explain_offline_selection(
        selected_path, scenario, sel_data, rej_data
    )

    return {
        "selected_path": selected_path,
        "selected_display_path": sel_data["display_path"],
        "selected_name": sel_data["name"],
        "selection_reason": selection_reason,
        "rejected_reason": rejection_reason,
        "candidates": candidate_paths_data,
        "event": event,
        "event_active": event_active,
        "time_until_event": time_until,
        "frs": frs,
        "penalty": penalty,
        "confidence": round(confidence, 1),
        "confidence_expl": confidence_expl,
        "sustainability": round(sustainability, 1),
        "sustainability_expl": sustainability_expl,
        "contributions": {
            "Latency": round(latency_contrib, 1),
            "Congestion": round(congestion_contrib, 1),
            "Future Risk": round(risk_contrib, 1),
            "Routing Cost": round(cost_contrib, 1),
        },
        "traffic_split_explanation": None,   # offline is single-path only
    }


# ──────────────────────────────────────────────────────────────────
# Live XAI Metrics
# ──────────────────────────────────────────────────────────────────
def get_live_xai_metrics(current_time, flow_id, sim):
    """Explainability metrics for LiveNetworkSimulator in-memory state."""

    flow = sim.flows.get(flow_id)
    if not flow or not flow.get("paths"):
        return None

    paths_info = flow["paths"]
    selected_path_info = paths_info[0]
    selected_path = selected_path_info["path"]

    # Events
    up_evs = sim.event_repo.get_upcoming_events(current_time)
    most_critical_event = None
    max_risk = 0.0
    for e in up_evs:
        path_links = [(selected_path[i], selected_path[i + 1]) for i in range(len(selected_path) - 1)]
        path_links += [(selected_path[i + 1], selected_path[i]) for i in range(len(selected_path) - 1)]
        if any(link in e["affected_links"] for link in path_links):
            time_until = max(0.0, e["start_time"] - current_time)
            proximity = 1.0 / (1.0 + (time_until / 10.0))
            risk = e["severity"] * proximity
            if risk > max_risk:
                max_risk = risk
                most_critical_event = e

    frs = min(1.0, max_risk)
    penalty = 100.0 * frs * (most_critical_event["severity"] if most_critical_event else 0.0)

    # Candidate paths
    k_paths = sim.get_context_aware_shortest_paths(flow["src"], flow["dst"], k=2)
    candidates_data = []
    for idx, p_item in enumerate(k_paths):
        path = p_item["path"]
        path_name = "Primary Optimal Route" if idx == 0 else "Alternative Route"
        lat = 0.0; congestions = []; losses = []; ml_cost = 0.0; base_cost = 0.0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            state = sim.link_states.get((u, v)) or sim.link_states.get((v, u))
            if state:
                lat += state.get("latency", 2.0)
                congestions.append(state.get("queue", 0.0))
                losses.append(state.get("loss", 0.0))
                ml_cost += state.get("cost", 10.0)
            else:
                lat += 2.0; congestions.append(0.0); losses.append(0.0); ml_cost += 10.0
            base_cost += 10.0

        avg_cong = sum(congestions) / len(congestions) if congestions else 0.0
        success_prob = 1.0
        for loss in losses:
            success_prob *= (1.0 - loss)
        path_loss = 1.0 - success_prob

        path_frs = 0.0; path_penalty = 0.0
        if most_critical_event:
            pl = [(path[i], path[i + 1]) for i in range(len(path) - 1)]
            pl += [(path[i + 1], path[i]) for i in range(len(path) - 1)]
            if any(link in most_critical_event["affected_links"] for link in pl):
                path_frs = frs
                path_penalty = penalty

        final_score = ml_cost + path_penalty
        candidates_data.append({
            "name": path_name,
            "path": path,
            "display_path": " → ".join(map(str, path)),
            "latency": round(lat, 2),
            "congestion": round(avg_cong * 100, 1),
            "packet_loss": round(path_loss * 100, 2),
            "base_cost": round(base_cost, 1),
            "ml_cost": round(ml_cost, 1),
            "frs": round(path_frs, 2),
            "penalty": round(path_penalty, 1),
            "final_score": round(final_score, 1),
        })

    sel_data = candidates_data[0] if candidates_data else {}

    # Metric contribution
    sel_lat_cost = sum(5.0 * (sim.link_states.get((selected_path[i], selected_path[i + 1]), {}).get("latency", 2.0)) for i in range(len(selected_path) - 1))
    sel_cong_cost = sum(
        1000.0 * (sim.link_states.get((selected_path[i], selected_path[i + 1]), {}).get("queue", 0.0))
        + 5000.0 * (sim.link_states.get((selected_path[i], selected_path[i + 1]), {}).get("loss", 0.0))
        for i in range(len(selected_path) - 1)
    )
    sel_base_cost = (len(selected_path) - 1) * 10.0
    sel_frs_cost = penalty if most_critical_event else 0.0

    total_decomp = sel_lat_cost + sel_cong_cost + sel_base_cost + sel_frs_cost
    if total_decomp > 0:
        latency_contrib = (sel_lat_cost / total_decomp) * 100.0
        congestion_contrib = (sel_cong_cost / total_decomp) * 100.0
        risk_contrib = (sel_frs_cost / total_decomp) * 100.0
        cost_contrib = (sel_base_cost / total_decomp) * 100.0
    else:
        latency_contrib = congestion_contrib = risk_contrib = cost_contrib = 25.0

    # Confidence & Sustainability
    confidence = 100.0 - (frs * 60.0) - (sel_data.get("congestion", 0) * 0.3) - (sel_data.get("packet_loss", 0) * 2.0)
    confidence = max(10.0, min(99.0, confidence))
    sustainability = 100.0 - (sel_data.get("congestion", 0) * 0.4) - (frs * 50.0)
    sustainability = max(10.0, min(99.0, sustainability))

    confidence_expl = _explain_confidence(confidence, frs)
    sustainability_expl = _explain_sustainability(sustainability)

    # ── Selection / Rejection explanations ──
    status = flow.get("status", "")
    selection_reason, rejection_reason = _explain_live_selection(
        paths_info, status, sel_data, most_critical_event, frs, current_time
    )

    # ── Traffic Split Explanation ──
    traffic_split_explanation = _explain_traffic_split(flow, paths_info, sim)

    event_formatted = None
    if most_critical_event:
        event_formatted = {
            "type": most_critical_event["type"].replace("_", " ").title(),
            "severity": most_critical_event["severity"],
            "start_time": most_critical_event["start_time"],
            "duration": most_critical_event["duration"],
            "description": f"A {most_critical_event['type'].replace('_', ' ')} event is scheduled on affected links.",
        }

    return {
        "selected_path": selected_path,
        "selected_display_path": " → ".join(map(str, selected_path)),
        "selected_name": "Active Path",
        "selection_reason": selection_reason,
        "rejected_reason": rejection_reason,
        "candidates": candidates_data,
        "event": event_formatted,
        "event_active": (most_critical_event["start_time"] <= current_time <= (most_critical_event["start_time"] + most_critical_event["duration"])) if most_critical_event else False,
        "time_until_event": max(0.0, most_critical_event["start_time"] - current_time) if most_critical_event else 0.0,
        "frs": frs,
        "penalty": penalty,
        "confidence": round(confidence, 1),
        "confidence_expl": confidence_expl,
        "sustainability": round(sustainability, 1),
        "sustainability_expl": sustainability_expl,
        "contributions": {
            "Latency": round(latency_contrib, 1),
            "Congestion": round(congestion_contrib, 1),
            "Future Risk": round(risk_contrib, 1),
            "Routing Cost": round(cost_contrib, 1),
        },
        "traffic_split_explanation": traffic_split_explanation,
    }


# ──────────────────────────────────────────────────────────────────
# Plain-English Generators
# ──────────────────────────────────────────────────────────────────

def _explain_confidence(confidence, frs):
    if confidence < 50.0:
        return f"Low confidence due to active critical risk or heavy congestion on the selected route (FRS: {frs:.2f})."
    elif confidence < 75.0:
        return "Moderate confidence: Route is operational, but upcoming events or rising queue occupancy warrant close monitoring."
    elif confidence < 90.0:
        return "High confidence: Minor network fluctuations or distant events slightly lower the certainty score."
    return "Stable route with low congestion and no critical future events detected."


def _explain_sustainability(sustainability):
    if sustainability < 50.0:
        return "Low sustainability: Route has severe bottlenecks, high failure risk, and lacks adequate high-fidelity alternate paths."
    elif sustainability < 75.0:
        return "Moderate sustainability: Exposure to upcoming events or elevated queue occupancy might cause routing instability."
    elif sustainability < 85.0:
        return "Good sustainability: Traffic is balanced; however, minor network events could trigger adaptive failovers."
    return "High sustainability: Low future congestion exposure, low failure probability, and stable traffic patterns."


def _explain_offline_selection(selected_path, scenario, sel_data, rej_data):
    """Generates selection / rejection explanations for offline scenarios."""
    selected_name = sel_data["name"]
    rejected_name = rej_data["name"]

    if selected_path == PRIMARY_PATH_OFFLINE:
        if sel_data["congestion"] > 40.0:
            selection_reason = (
                f"The {selected_name} was selected despite elevated congestion ({sel_data['congestion']:.1f}%) "
                f"because the alternate route incurs a higher latency penalty and routing cost. "
                f"The overall path cost is currently within acceptable margins."
            )
        else:
            selection_reason = (
                f"The {selected_name} was selected because it represents the shortest path with the lowest base cost, "
                f"optimal latency ({sel_data['latency']} ms), and no future event risk (FRS: 0.0)."
            )
        rejection_reason = (
            f"The {rejected_name} was bypassed because the primary route is fully functional. "
            f"Bypassing to the alternate regional transit path would unnecessarily increase "
            f"network latency from {sel_data['latency']} ms to {rej_data['latency']} ms."
        )
    else:
        if scenario == "failure":
            selection_reason = (
                f"The {selected_name} was selected as an active failover route to bypass the critical link failure "
                f"on the primary trunk (link 4→5). This route guarantees 100% packet delivery by routing around the dead zone."
            )
            rejection_reason = (
                f"The {rejected_name} was rejected because a critical physical link failure occurred on link 4→5. "
                f"Attempting to route traffic through this path would result in 100% packet loss and complete disconnection."
            )
        elif scenario == "congestion":
            selection_reason = (
                f"The {selected_name} was selected to steer traffic away from the heavily congested link 4→5. "
                f"By utilising the Alternate regional DC path, the engine reduces queue congestion and packet loss."
            )
            rejection_reason = (
                f"The {rejected_name} was rejected because link 4→5 is experiencing severe congestion. "
                f"The predicted routing cost of the primary path exceeds the threshold limit ({rej_data['final_score']:.1f} vs {sel_data['final_score']:.1f})."
            )
        else:
            selection_reason = (
                f"The {selected_name} was selected to balance network load. The primary path is currently overloaded "
                f"due to a traffic burst, making the alternate transit path more cost-effective."
            )
            rejection_reason = (
                f"The {rejected_name} was bypassed because the traffic spike on the primary links breached "
                f"the threshold, making the alternative route the most sustainable choice."
            )

    return selection_reason, rejection_reason


def _explain_live_selection(paths_info, status, sel_data, most_critical_event, frs, current_time):
    """Generates selection / rejection explanations for live mode."""

    if len(paths_info) > 1:
        selection_reason = (
            f"The engine is currently load balancing traffic across multiple paths: {status}. "
            f"This multi-path approach is selected because the primary destination path score is elevated, "
            f"and splitting load across node siblings reduces link utilisation below bottleneck limits."
        )
        rejection_reason = (
            f"Using a single route (100% capacity) was rejected because it would cause queue buffer saturation. "
            f"Distributing traffic reduces peak queue utilisation and avoids packet drops."
        )
    else:
        selection_reason = (
            f"The primary optimal route was selected because it represents the path with the lowest overall cost penalty. "
            f"Average link latency is {sel_data.get('latency', 0)} ms and queue buffer utilisation is optimal ({sel_data.get('congestion', 0)}%)."
        )
        rejection_reason = (
            f"Alternative routes were bypassed because they incur higher base routing costs (longer hops) "
            f"or cross regions experiencing elevated ML predicted costs."
        )

    # Override if critical event is active
    if most_critical_event and most_critical_event["start_time"] <= current_time:
        ev_type_str = most_critical_event["type"].replace("_", " ").title()
        selection_reason = (
            f"An active {ev_type_str} event was detected on the primary links. The engine bypassed the primary route "
            f"and selected a safe alternative path to avoid the risk zone, maintaining packet transmission integrity."
        )
        rejection_reason = (
            f"The primary candidate route was rejected because it intersects the active {ev_type_str} event. "
            f"Routing traffic through it would risk a Future Risk Score of {frs:.2f} and cause packet drops."
        )

    return selection_reason, rejection_reason


# ──────────────────────────────────────────────────────────────────
# Traffic Split Explanation
# ──────────────────────────────────────────────────────────────────
def _explain_traffic_split(flow, paths_info, sim):
    """
    When data is split across 2+ paths/DCs, produce a clear plain-English
    explanation of which DCs receive traffic, the percentage split, the
    actual Mbps quantity, and the reasoning behind the split ratio.
    """
    if len(paths_info) <= 1:
        return None   # No split active

    volume = flow.get("volume", 0)
    status = flow.get("status", "")

    # DC name lookup
    dc_names = {
        2: "DC1 (Origin)", 3: "DC1 (Origin)",
        5: "DC2 (Compute A)", 6: "DC2 (Compute A)",
        8: "DC3 (Compute B)", 9: "DC3 (Compute B)",
        11: "DC4 (Storage)", 12: "DC4 (Storage)",
        14: "DC5 (Backup)",
    }

    lines = []
    lines.append("**Traffic is currently being split across multiple paths:**\n")

    for idx, p_info in enumerate(paths_info):
        path = p_info["path"]
        weight = p_info["weight"]
        ptype = p_info.get("type", "primary")
        dst_node = path[-1] if path else "?"
        dc_label = dc_names.get(dst_node, f"Node {dst_node}")
        mbps = round(volume * weight, 1)
        pct = round(weight * 100, 1)
        type_tag = "Primary" if ptype == "primary" else "Rerouted"

        # Compute path telemetry
        telem = sim.get_path_telemetry(path)

        lines.append(
            f"- **Path {idx + 1} ({type_tag})** → **{dc_label}** (Node {dst_node}):  "
            f"receives **{pct}%** of traffic (**{mbps} Mbps**).  "
            f"Latency: {telem['latency']} ms | ML Cost: {telem['ml_cost']}"
        )

    lines.append("")

    # Reasoning
    if "Mega-Split" in status:
        lines.append(
            "**Reasoning:** The total traffic volume or primary-path cost exceeds the Tier-3 threshold, "
            "triggering a Cross-Datacenter Mega-Split. Traffic is distributed across multiple data centres "
            "to prevent queue buffer saturation and packet loss on any single DC spine. The split ratio "
            "is inversely proportional to each DC's routing cost — the DC with the lower cost absorbs "
            "a larger share of the load."
        )
    elif "Same-DC" in status or "Core Reroute" in status:
        lines.append(
            "**Reasoning:** Moderate congestion or traffic volume activated Tier-2 Sibling Load Balance. "
            "Traffic is split between the destination leaf and its sibling node within the same data centre "
            "to halve the per-node queue pressure. The split ratio is based on the relative ML-predicted "
            "routing costs of each path: the cheaper path receives a proportionally larger share."
        )
    else:
        lines.append(
            "**Reasoning:** The engine determined that distributing traffic across multiple paths "
            "reduces overall network stress and improves reliability."
        )

    return "\n".join(lines)
