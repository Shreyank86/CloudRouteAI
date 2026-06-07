import streamlit as st
from dash_utils import to_display, get_routing_description
import theme_engine as te

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
        
        status_color = te.COLORS["accent_1"] # Stable / Blue
        badge_text = "STABLE"
        icon = "✅"
        
        if action in ["REROUTED", "IMMEDIATE_FAILOVER"]:
            status_color = te.COLORS["danger"]
            badge_text = "REROUTE"
            icon = "🚨"
        elif action == "LINK_FAILED_AT_START":
            status_color = te.COLORS["danger"]
            badge_text = "FAILURE"
            icon = "❌"
        elif action == "THRESHOLD_BREACHED_NO_BETTER_PATH":
            status_color = te.COLORS["warning"]
            badge_text = "CONGESTION"
            icon = "⚠️"

        st.markdown(f"""
        <div class="cn-glass-panel" style="margin-bottom: 1rem; border-left: 4px solid {status_color}; border-top: 1px solid rgba(0, 212, 255, 0.05); border-right: 1px solid rgba(0, 212, 255, 0.05); border-bottom: 1px solid rgba(0, 212, 255, 0.05); padding: 1rem; border-radius: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-weight: 700; color: {status_color}; font-size: 0.9rem; font-family: var(--font-display);">{icon} {badge_text}</span>
                <span style="color: var(--text-muted); font-size: 0.8rem; font-family: var(--font-display);">t = {ts}s</span>
            </div>
            <div style="font-size: 0.9rem; color: var(--text-primary);">
                {get_routing_description(dec)}
            </div>
            <div style="margin-top: 0.8rem; padding-top: 0.8rem; border-top: 1px solid rgba(255,255,255,0.05); font-family: var(--font-mono); font-size: 0.8rem; color: var(--accent-1);">
                {path_str}
            </div>
        </div>
        """, unsafe_allow_html=True)



