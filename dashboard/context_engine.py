"""
CloudRouteAI — Context-Aware Engine
====================================
Provides future-event awareness and decision intelligence logging
for the live routing simulator.

Classes:
    FutureEventRepository   — stores and queries scheduled network events
    ContextAwareValidationLayer — evaluates Future Risk Score (FRS) per path
    DecisionIntelligenceModule  — logs every routing decision for XAI consumption
"""

import json
import time


class FutureEventRepository:
    """Manages scheduled future network events (traffic bursts, failures, etc.)."""

    def __init__(self):
        self.events = {}
        self.next_id = 1

    def add_event(self, event_type, severity, start_time, duration, affected_links=None):
        event_id = f"E{self.next_id}"
        self.next_id += 1

        self.events[event_id] = {
            "event_id": event_id,
            "type": event_type,
            "severity": severity,        # 0.0 to 1.0
            "start_time": start_time,
            "duration": duration,
            "affected_links": affected_links or []
        }
        return event_id

    def remove_event(self, event_id):
        if event_id in self.events:
            del self.events[event_id]

    def get_upcoming_events(self, current_time, horizon=60.0):
        """Return events that are active now or start within the horizon."""
        upcoming = []
        for eid, e in self.events.items():
            if e["start_time"] <= current_time + horizon and (e["start_time"] + e["duration"]) >= current_time:
                upcoming.append(e)
        return upcoming

    def get_active_events(self, current_time):
        """Return events that are currently in progress."""
        active = []
        for eid, e in self.events.items():
            if e["start_time"] <= current_time <= (e["start_time"] + e["duration"]):
                active.append(e)
        return active


class ContextAwareValidationLayer:
    """
    Evaluates paths against upcoming events and computes:
      • Future Risk Score (FRS) — 0.0 (safe) to 1.0 (critical)
      • Routing Penalty        — λ × FRS × EventSeverity
    """

    def __init__(self, lambda_weight=100.0):
        self.lambda_weight = lambda_weight

    def evaluate_path(self, path, current_time, upcoming_events):
        """Computes the Future Risk Score (FRS) for a given path."""
        if not path or len(path) < 2:
            return 0.0, None

        max_risk = 0.0
        most_critical_event = None

        # Create pairs of links from the path (both directions)
        path_links = []
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            path_links.append((u, v))
            path_links.append((v, u))

        for e in upcoming_events:
            event_impact = False
            for link in path_links:
                if link in e["affected_links"]:
                    event_impact = True
                    break

            if event_impact:
                time_until = max(0.0, e["start_time"] - current_time)
                # Proximity factor: 1.0 if happening now, approaches 0 as time_until grows
                proximity_factor = 1.0 / (1.0 + (time_until / 10.0))
                risk = e["severity"] * proximity_factor
                if risk > max_risk:
                    max_risk = risk
                    most_critical_event = e

        frs = min(1.0, max(0.0, max_risk))
        return frs, most_critical_event

    def calculate_penalty(self, frs, event_severity):
        """Penalty = λ × FRS × EventSeverity."""
        return self.lambda_weight * frs * event_severity


class DecisionIntelligenceModule:
    """Logs routing decisions for downstream XAI consumption."""

    def __init__(self):
        self.decision_logs = []

    def log_decision(self, timestamp, flow_id, current_metrics, context_metrics,
                     routing_metrics, confidence_metrics):
        log_entry = {
            "timestamp": timestamp,
            "flow_id": flow_id,
            "current_metrics": current_metrics,
            "context_metrics": context_metrics,
            "routing_metrics": routing_metrics,
            "confidence_metrics": confidence_metrics
        }
        self.decision_logs.append(log_entry)
        return log_entry

    def get_latest_logs(self, limit=10):
        return self.decision_logs[-limit:]
