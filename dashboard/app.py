import streamlit as st
import os
import subprocess
import time

from dash_utils import (
    get_available_scenarios, scenario_description,
    load_ml_costs, load_routing_decisions, load_runtime_metrics,
    get_summary_metrics, BASE_DIR
)
from topology_view import draw_topology
from topology_lab import draw_topology_lab
from metrics_view import draw_metrics_chart, draw_link_details
from routing_view import draw_routing_decisions
from comparison_view import draw_comparison
from simulation_view import draw_simulation_lab
from react_topology import draw_enhanced_movement_sim
from live_view import draw_live_dashboard
from xai_view import draw_xai_tab

st.set_page_config(
    page_title="CloudRouteAI | Adaptive Network Control",
    page_icon="🌐", layout="wide", initial_sidebar_state="expanded"
)

# --- Session State ---
if "active_tab_label" not in st.session_state:
    st.session_state.active_tab_label = "🌐 Global Network Ops"

# --- Sidebar Query Parameter Routing ---
if "tab" in st.query_params:
    selected_tab = st.query_params["tab"]
    tab_query_map = {
        "dashboard": "🌐 Global Network Ops",
        "topology": "🗺️ Topology Lab",
        "reports": "📋 Reports",
        "devices": "🗺️ Topology Lab",
    }
    if selected_tab in tab_query_map:
        st.session_state.active_tab_label = tab_query_map[selected_tab]
        if selected_tab == "devices":
            st.toast("🖥️ Devices inventory view is under construction. Please use Topology Lab for active routing details.", icon="ℹ️")
    del st.query_params["tab"]

if "live_sim" not in st.session_state:
    from live_engine import LiveNetworkSimulator
    st.session_state.live_sim = LiveNetworkSimulator()
if "active_tab" not in st.session_state:
    st.session_state.active_tab = 0
if "playing" not in st.session_state:
    st.session_state.playing = False
if "current_sim_time" not in st.session_state:
    st.session_state.current_sim_time = 0.0

# Premium CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
* { font-family: 'Outfit', sans-serif; }
.main { background: linear-gradient(135deg, #0a0f1a 0%, #111827 50%, #0f172a 100%); color: #f8fafc; }
.stApp { background-color: #0a0f1a; }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
}
.metric-card {
    background: rgba(30, 41, 59, 0.5);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 1.5rem; border-radius: 1rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    text-align: center; transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
}
.metric-card:hover { transform: translateY(-4px); border-color: rgba(59,130,246,0.4); box-shadow: 0 12px 40px rgba(59,130,246,0.15); }
.metric-value { font-size: 2rem; font-weight: 700; background: linear-gradient(135deg, #3b82f6, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.3rem; }
.metric-label { font-size: 0.8rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; }
h1, h2, h3 { color: #f8fafc !important; font-weight: 600 !important; }
.stButton>button {
    background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
    color: white; border: none; border-radius: 0.75rem;
    padding: 0.6rem 1.2rem; font-weight: 600;
    transition: all 0.3s; box-shadow: 0 4px 15px rgba(59,130,246,0.3);
}
.stButton>button:hover { opacity: 0.9; box-shadow: 0 6px 25px rgba(59,130,246,0.5); transform: translateY(-1px); }
.nav-item {
    padding: 0.7rem 1rem; border-radius: 0.75rem; margin-bottom: 0.3rem;
    color: #94a3b8; font-size: 0.9rem; font-weight: 500;
    display: flex; align-items: center; gap: 0.6rem;
    transition: all 0.2s; cursor: pointer;
}
.nav-active { background: rgba(59,130,246,0.15); color: #3b82f6; border-left: 3px solid #3b82f6; }
.scenario-card {
    background: rgba(30, 41, 59, 0.4); padding: 1rem; border-radius: 0.75rem;
    border: 1px solid rgba(255,255,255,0.06); margin-bottom: 0.5rem;
    transition: all 0.2s; cursor: pointer;
}
.scenario-card:hover { border-color: rgba(59,130,246,0.3); }
.scenario-card.active { border-color: #ef4444; background: rgba(239,68,68,0.1); }
.status-badge { padding: 0.2rem 0.6rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; }
.status-healthy { background-color: #064e3b; color: #10b981; border: 1px solid #10b981; }
.status-active { background-color: #1e3a8a; color: #3b82f6; border: 1px solid #3b82f6; }
.status-alert { background-color: #7c2d12; color: #f97316; border: 1px solid #f97316; }
.status-critical { background-color: #7f1d1d; color: #ef4444; border: 1px solid #ef4444; }
hr { border-color: rgba(255,255,255,0.06); }
.glass-panel {
    background: rgba(30, 41, 59, 0.4); backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.08); border-radius: 1rem; padding: 1.5rem;
}
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:0.75rem; margin-bottom:1.5rem;">
        <div style="width:42px;height:42px;background:linear-gradient(135deg,#3b82f6,#8b5cf6);border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:1.3rem;">🌐</div>
        <div>
            <div style="font-weight:700;font-size:1.1rem;color:#f8fafc;">CloudRouteAI</div>
            <div style="font-size:0.7rem;color:#64748b;">Platform v2.0</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    active_tab = st.session_state.get("active_tab_label", "🌐 Global Network Ops")
    dash_active = "nav-active" if active_tab == "🌐 Global Network Ops" else ""
    topo_active = "nav-active" if active_tab == "🗺️ Topology Lab" else ""
    rep_active = "nav-active" if active_tab == "📋 Reports" else ""

    st.markdown(f'''
    <a href="/?tab=dashboard" target="_self" style="text-decoration: none;">
        <div class="nav-item {dash_active}">📊 Dashboard</div>
    </a>
    <a href="/?tab=devices" target="_self" style="text-decoration: none;">
        <div class="nav-item">🖥️ Devices</div>
    </a>
    <a href="/?tab=topology" target="_self" style="text-decoration: none;">
        <div class="nav-item {topo_active}">🗺️ Topology Lab</div>
    </a>
    <a href="/?tab=reports" target="_self" style="text-decoration: none;">
        <div class="nav-item {rep_active}">📋 Reports</div>
    </a>
    ''', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🎯 Scenario Simulator")

    available_scenarios = get_available_scenarios()
    scenario = st.selectbox("Network Scenario", available_scenarios,
                            index=1 if "congestion" in available_scenarios else 0,
                            label_visibility="collapsed")

    st.markdown("---")
    st.markdown("### ⏱️ Temporal Analysis")

    runtime_data = load_runtime_metrics()
    routing_data = load_routing_decisions()
    ml_data = load_ml_costs()

    max_time = 20
    if runtime_data and "snapshots" in runtime_data:
        snaps = runtime_data["snapshots"]
        if snaps:
            timestamps = [int(s["timestamp"]) for s in snaps]
            if timestamps: max_time = max(timestamps)

    # Main slider tied to session state
    current_time = st.slider("Simulation Time (s)", 0.0, float(max_time), st.session_state.current_sim_time, step=2.0, key="sim_time_slider")
    st.session_state.current_sim_time = current_time

    st.markdown("---")
    st.markdown("### ⏩ Playback Controls")
    playback_speed = st.slider("Playback Speed", 0.5, 2.0, 1.0, step=0.1)

    st.markdown("---")
    st.markdown("### 📡 System Status")
    sc1, sc2 = st.columns(2)
    with sc1:
        st.markdown('<div class="status-badge status-healthy">CORE OK</div>', unsafe_allow_html=True)
    with sc2:
        st.markdown('<div class="status-badge status-active">AI ACTIVE</div>', unsafe_allow_html=True)

# --- Main Dashboard ---
st.markdown("""
<div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.5rem;">
    <h1 style="margin:0;">🌐 CloudRouteAI</h1>
</div>
<p style="color:#94a3b8;margin-top:0;">Adaptive Multi-Path Routing & Intelligent Congestion Control</p>
""", unsafe_allow_html=True)

def draw_global_header(tab_key):
    # Action buttons row
    btn_cols = st.columns([1, 1, 1, 3])
    with btn_cols[0]:
        if st.button("🔄 Reset Topology", use_container_width=True, key=f"reset_{tab_key}"):
            st.session_state.playing = False
            st.session_state.current_sim_time = 0.0
            for d in ["outputs/raw", "outputs/ml", "outputs/routing", "outputs/processed"]:
                full_d = os.path.join(BASE_DIR, d)
                os.makedirs(full_d, exist_ok=True)
                for f in os.listdir(full_d):
                    os.remove(os.path.join(full_d, f))
            tab_map = {
                "t0": "🌐 Global Network Ops",
                "t1": "🗺️ Topology Lab",
                "t2": "⚡ Simulation Lab",
                "t3": "📊 Performance Analytics",
                "t4": "🧠 Adaptive Intelligence",
                "t5": "📋 Reports",
                "t6": "⚡ True LIVE Simulator",
                "txai": "🔍 Explainable AI (XAI)",
            }
            if tab_key in tab_map:
                st.session_state.active_tab_label = tab_map[tab_key]
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Key Metrics
    avg_loss, avg_util, total_thru, max_queue = get_summary_metrics(runtime_data, st.session_state.current_sim_time)
    mcols = st.columns(4)
    with mcols[0]:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{avg_loss:.2f}%</div><div class="metric-label">Avg Packet Loss</div></div>', unsafe_allow_html=True)
    with mcols[1]:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{avg_util:.1f}%</div><div class="metric-label">Network Load</div></div>', unsafe_allow_html=True)
    with mcols[2]:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{total_thru:.2f}</div><div class="metric-label">Total Mbps</div></div>', unsafe_allow_html=True)
    with mcols[3]:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{max_queue:.1f}%</div><div class="metric-label">Peak Congestion</div></div>', unsafe_allow_html=True)


# Tabbed Interface
tab_names = [
    "🌐 Global Network Ops", "⚡ True LIVE Simulator", "🗺️ Topology Lab", "⚡ Simulation Lab", 
    "📊 Performance Analytics", "🧠 Adaptive Intelligence", "🔍 Explainable AI (XAI)", "📋 Reports"
]
tab0, tab6, tab1, tab2, tab3, tab4, tab_xai, tab5 = st.tabs(tab_names, key="active_tab_label", on_change="rerun")

with tab0:
    draw_global_header("t0")
    st.markdown("""
    <div class="glass-panel" style="margin-bottom: 1.5rem;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <h2 style="margin:0; color: #f8fafc;">🌐 Global Operations Center</h2>
                <p style="color: #94a3b8; margin: 0.5rem 0 0 0; font-size: 0.95rem;">
                    Real-time multi-data-center traffic movement and intelligent routing visualization.
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_play, col_stop, col_spacer = st.columns([1, 1, 3])
    with col_play:
        if st.button("▶️ Play Demo", use_container_width=True):
            st.session_state.playing = True
    with col_stop:
        if st.button("⏹️ Stop", use_container_width=True):
            st.session_state.playing = False

    draw_enhanced_movement_sim(st.session_state.current_sim_time, routing_data, ml_data, runtime_data, playback_speed=playback_speed, is_playing=st.session_state.playing)

with tab1:
    draw_global_header("t1")
    draw_topology_lab(st.session_state.current_sim_time, routing_data, ml_data, runtime_data)
    st.markdown("---")
    col_topo, col_info = st.columns([3, 1])
    with col_topo:
        draw_topology(st.session_state.current_sim_time, routing_data, ml_data)
    with col_info:
        st.subheader("Network State")
        if ml_data:
            classified_scenario = ml_data.get("classified_scenario", "unknown")
            sc = "#3b82f6"
            if "congestion" in classified_scenario: sc = "#f97316"
            elif "failure" in classified_scenario: sc = "#ef4444"
            st.markdown(f"""
            <div style="background:rgba(30,41,59,0.5);padding:1rem;border-radius:0.5rem;border-left:4px solid {sc};">
                <h4 style="margin:0;color:{sc};">ML Classification</h4>
                <p style="font-size:1.2rem;font-weight:600;margin:0.5rem 0;">{classified_scenario.upper()}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ **Awaiting Data** — Run a simulation first.")
        st.markdown("---")
        draw_link_details(runtime_data, st.session_state.current_sim_time)

with tab2:
    draw_global_header("t2")
    draw_simulation_lab(scenario)

with tab3:
    draw_global_header("t3")
    st.subheader("Real-time Performance Metrics")
    draw_metrics_chart(runtime_data)
    st.markdown("---")
    draw_comparison()

with tab4:
    draw_global_header("t4")
    draw_routing_decisions(routing_data, st.session_state.current_sim_time)

with tab_xai:
    if "live_sim" in st.session_state:
        draw_xai_tab(st.session_state.live_sim)
    else:
        st.info("💡 **Start the True LIVE Simulator first** to populate the XAI dashboard.")

with tab6:
    draw_live_dashboard()

with tab5:
    draw_global_header("t5")
    st.markdown("""
    <div class="glass-panel" style="margin-bottom: 1.5rem;">
        <h2 style="margin:0; color: #f8fafc;">📋 System Analysis & Reports</h2>
        <p style="color: #94a3b8; margin: 0.5rem 0 0 0; font-size: 0.95rem;">
            Export simulation runs data, validation engine metrics, and routing decisions.
        </p>
    </div>
    """, unsafe_allow_html=True)

    r_col1, r_col2 = st.columns([2, 1.2])

    with r_col1:
        st.markdown("### 📊 Available Datasets for Export")
        st.markdown("<p style='color:#64748b; font-size:0.85rem; margin-top:-0.5rem;'>Downloads include all generated JSON data from the latest active simulation run.</p>", unsafe_allow_html=True)

        def safe_read_file(filename):
            path = os.path.join(BASE_DIR, "outputs", "processed", filename)
            if os.path.exists(path):
                with open(path, "r") as f:
                    return f.read()
            return None

        metrics_data = safe_read_file("runtime_metrics.json")
        decisions_data = safe_read_file("routing_decisions.json")
        costs_data = safe_read_file("ml_costs.json")

        if metrics_data:
            st.success("✅ **Active Simulation Datasets Found!**")
            
            dcols = st.columns(3)
            with dcols[0]:
                st.download_button(
                    label="📥 Runtime Metrics",
                    data=metrics_data,
                    file_name="runtime_metrics.json",
                    mime="application/json",
                    use_container_width=True,
                    key="dl_metrics"
                )
                st.caption("Flow statistics and network loads.")

            with dcols[1]:
                st.download_button(
                    label="📥 Routing Decisions",
                    data=decisions_data if decisions_data else "{}",
                    file_name="routing_decisions.json",
                    mime="application/json",
                    use_container_width=True,
                    key="dl_decisions"
                )
                st.caption("Core routing actions and tiers.")

            with dcols[2]:
                st.download_button(
                    label="📥 ML Cost Models",
                    data=costs_data if costs_data else "{}",
                    file_name="ml_costs.json",
                    mime="application/json",
                    use_container_width=True,
                    key="dl_costs"
                )
                st.caption("Machine Learning predicted costs.")
        else:
            st.warning("⚠️ **No Active Simulation Data Found**")
            st.info("💡 Run a NetworkX or NS-3 simulation in the **Simulation Lab** tab to generate exportable datasets.")

    with r_col2:
        st.markdown(f"""
        <div style="background: rgba(30, 41, 59, 0.4); padding: 1.5rem; border-radius: 1rem;
                    border: 1px solid rgba(255, 255, 255, 0.06); height: 100%;
                    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);">
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
                <span style="font-size: 1.2rem;">ℹ️</span>
                <span style="font-size: 1.05rem; font-weight: 600; color: #f8fafc;">Verification Info</span>
            </div>
            <p style="font-size: 0.85rem; color: #cbd5e1; line-height: 1.6;">
                These datasets contain raw metrics generated from the simulation models, which feed directly into our 
                <b>Decision Intelligence Layer</b> and the <b>Explainable AI (XAI)</b> dashboard.
            </p>
            <p style="font-size: 0.85rem; color: #94a3b8; line-height: 1.6; margin-top: 1rem;">
                JSON schemas are fully compatible with validation engines and offline analyzers.
            </p>
        </div>
        """, unsafe_allow_html=True)

# Playback Logic (At the end of the script)
if st.session_state.playing:
    if st.session_state.current_sim_time < float(max_time):
        time.sleep(2.0 / playback_speed)
        st.session_state.current_sim_time += 2.0
        st.rerun()
    else:
        st.session_state.playing = False
        st.rerun()
