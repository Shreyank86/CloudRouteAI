import streamlit as st
from dash_utils import to_display, get_routing_description

def draw_routing_decisions(routing_data, current_timestamp):
    """Display routing decisions as a modern activity feed."""
    st.markdown("### 🧠 Routing Intelligence Feed")
    
    if not routing_data or "decisions" not in routing_data:
        st.info("No intelligence logs available for this session.")
        return
        
    decisions = routing_data["decisions"]
    visible_decisions = [d for d in decisions if d["timestamp"] <= current_timestamp]
    
    if not visible_decisions:
        st.info("Awaiting initial telemetry analysis...")
        return
        
    # Container for feed items
    for dec in reversed(visible_decisions):
        ts = dec["timestamp"]
        action = dec["action"]
        path_str = " → ".join(map(str, to_display(dec["current_path"])))
        
        status_color = "#3b82f6" # Stable
        badge_text = "STABLE"
        icon = "✅"
        
        if action in ["REROUTED", "IMMEDIATE_FAILOVER"]:
            status_color = "#ef4444"
            badge_text = "REROUTE"
            icon = "🚨"
        elif action == "LINK_FAILED_AT_START":
            status_color = "#ef4444"
            badge_text = "FAILURE"
            icon = "❌"
        elif action == "THRESHOLD_BREACHED_NO_BETTER_PATH":
            status_color = "#f97316"
            badge_text = "CONGESTION"
            icon = "⚠️"

        st.markdown(f"""
        <div style="background: rgba(30, 41, 59, 0.4); padding: 1rem; border-radius: 0.8rem; margin-bottom: 1rem; border-left: 4px solid {status_color};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-weight: 700; color: {status_color}; font-size: 0.9rem;">{icon} {badge_text}</span>
                <span style="color: #94a3b8; font-size: 0.8rem;">t = {ts}s</span>
            </div>
            <div style="font-size: 0.9rem; color: #f8fafc;">
                {get_routing_description(dec)}
            </div>
            <div style="margin-top: 0.8rem; padding-top: 0.8rem; border-top: 1px solid rgba(255,255,255,0.05); font-family: monospace; font-size: 0.8rem; color: #3b82f6;">
                {path_str}
            </div>
        </div>
        """, unsafe_allow_html=True)


