import streamlit as st
import os
import subprocess
import sys
import time
import threading

# ── Telemetry server is managed independently by Kubernetes ──

from dash_utils import (
    get_available_scenarios, scenario_description,
    load_ml_costs, load_routing_decisions, load_runtime_metrics,
    get_summary_metrics, BASE_DIR
)
from topology_view import draw_topology
from topology_lab import draw_topology_lab
from metrics_view import draw_metrics_chart, draw_link_details
from routing_view import draw_routing_decisions
from comparison_view import draw_comparison, draw_live_telemetry_chart
from simulation_view import draw_simulation_lab
from react_topology import draw_enhanced_movement_sim
from live_view import draw_live_dashboard
from xai_view import draw_xai_tab

import theme_engine as te

st.set_page_config(
    page_title="CloudRouteAI | Adaptive Network Control",
    page_icon="🌐", layout="wide", initial_sidebar_state="expanded"
)

# --- Session State ---
if "active_tab_label" not in st.session_state:
    st.session_state["active_tab_label"] = "🌐 Global Network Ops"

# --- Sidebar Query Parameter Routing ---
if "tab" in st.query_params:
    selected_tab = st.query_params["tab"]
    tab_query_map = {
        "dashboard": "🌐 Global Network Ops",
        "topology": "🗺️ Topology Lab",
        "reports": "📋 Reports",
        "devices": "🖥️ Devices",
    }
    if selected_tab in tab_query_map:
        st.session_state["active_tab_label"] = tab_query_map[selected_tab]
    del st.query_params["tab"]

# Telemetry server is now started at module-level above (before any session).
# Mark session state so other parts of the UI know the server is active.
if "telemetry_server_started" not in st.session_state:
    st.session_state.telemetry_server_started = True

if "live_sim" not in st.session_state:
    from live_engine import LiveNetworkSimulator, LIVE_DIR
    import os as _os
    _os.makedirs(LIVE_DIR, exist_ok=True)
    st.session_state.live_sim = LiveNetworkSimulator()
if "active_tab" not in st.session_state:
    st.session_state.active_tab = 0
if "playing" not in st.session_state:
    st.session_state.playing = False
if "current_sim_time" not in st.session_state:
    st.session_state.current_sim_time = 0.0

# Inject theme engine CSS
te.inject_global_css()

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
    dash_active = "cn-nav-active" if active_tab == "🌐 Global Network Ops" else ""
    topo_active = "cn-nav-active" if active_tab == "🗺️ Topology Lab" else ""
    rep_active = "cn-nav-active" if active_tab == "📋 Reports" else ""
    dev_active = "cn-nav-active" if active_tab == "🖥️ Devices" else ""

    st.markdown(f'''
    <a href="/?tab=dashboard" target="_self" style="text-decoration: none;">
        <div class="cn-nav-item {dash_active}">📊 Dashboard</div>
    </a>
    <a href="/?tab=devices" target="_self" style="text-decoration: none;">
        <div class="cn-nav-item {dev_active}">🖥️ Devices</div>
    </a>
    <a href="/?tab=topology" target="_self" style="text-decoration: none;">
        <div class="cn-nav-item {topo_active}">🗺️ Topology Lab</div>
    </a>
    <a href="/?tab=reports" target="_self" style="text-decoration: none;">
        <div class="cn-nav-item {rep_active}">📋 Reports</div>
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
        st.markdown('<div class="cn-badge cn-badge-healthy">CORE OK</div>', unsafe_allow_html=True)
    with sc2:
        st.markdown('<div class="cn-badge cn-badge-active">AI ACTIVE</div>', unsafe_allow_html=True)

# --- Main Dashboard ---
te.hero_banner("🌐 CloudRouteAI", "Adaptive Multi-Path Routing & Intelligent Congestion Control")


def reset_topology_callback(tab_key):
    st.session_state.playing = False
    st.session_state.current_sim_time = 0.0
    for d in ["outputs/raw", "outputs/ml", "outputs/routing", "outputs/processed"]:
        full_d = os.path.join(BASE_DIR, d)
        os.makedirs(full_d, exist_ok=True)
        for f in os.listdir(full_d):
            try:
                os.remove(os.path.join(full_d, f))
            except Exception:
                pass
    tab_map = {
        "t0": "🌐 Global Network Ops",
        "tdev": "🖥️ Devices",
        "t1": "🗺️ Topology Lab",
        "t2": "⚡ Simulation Lab",
        "t3": "📊 Performance Analytics",
        "t4": "🧠 Adaptive Intelligence",
        "t5": "📋 Reports",
        "t6": "⚡ True LIVE Simulator",
        "txai": "🔍 Explainable AI (XAI)",
    }
    if tab_key in tab_map:
        st.session_state["active_tab_label"] = tab_map[tab_key]

def draw_global_header(tab_key):
    # Action buttons row
    btn_cols = st.columns([1, 1, 1, 3])
    with btn_cols[0]:
        st.button("🔄 Reset Topology", use_container_width=True, key=f"reset_{tab_key}", on_click=reset_topology_callback, args=(tab_key,))

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Real-Time KPI Cards ────────────────────────────────────────────────────
    # Fetch real-time client telemetry
    import sys, os
    _root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _root_dir not in sys.path:
        sys.path.insert(0, _root_dir)
    try:
        from telemetry.client_registry import get_registered_clients
        active_clients = get_registered_clients(timeout=5.0)
    except Exception:
        active_clients = []

    live_sim = st.session_state.get("live_sim")
    sim_live = live_sim is not None and live_sim.time_step > 0

    if active_clients:
        # Real-time Client Metrics
        total_thru = sum(c["total_throughput_mbps"] for c in active_clients)
        avg_util = min(100.0, total_thru / 500.0 * 100) # heuristic load based on 500Mbps capacity
        avg_loss = 0.0 # clients assume 0 loss unless reported
        max_queue = min(100.0, avg_util * 1.2)
        source_label = f"🔴 REAL-TIME  ·  {len(active_clients)} Clients"
    elif sim_live:
        avg_loss, avg_util, total_thru, max_queue = live_sim.get_aggregate_metrics()
        source_label = f"🔴 LIVE SIM  ·  t = {live_sim.time_step * 2:.0f} s"
    else:
        avg_loss, avg_util, total_thru, max_queue = get_summary_metrics(runtime_data, st.session_state.current_sim_time)
        source_label = "📁 Static (Simulated)"

    st.caption(f"Data source: {source_label}")

    mcols = st.columns(4)
    with mcols[0]:
        te.metric_card("Avg Packet Loss", f"{avg_loss:.2f}%", icon="📉", color=te.COLORS["danger"], idx=0)
    with mcols[1]:
        te.metric_card("Network Load", f"{avg_util:.1f}%", icon="⚖️", color=te.COLORS["accent_1"], idx=1)
    with mcols[2]:
        te.metric_card("Total Mbps", f"{total_thru:.2f}", icon="⚡", color=te.COLORS["success"], idx=2)
    with mcols[3]:
        te.metric_card("Peak Congestion", f"{max_queue:.1f}%", icon="🔥", color=te.COLORS["warning"], idx=3)



# Tabbed Interface
tab_names = [
    "🖥️ Devices", "⚡ True LIVE Simulator", "🗺️ Topology Lab", "⚡ Simulation Lab", 
    "📊 Performance Analytics", "🧠 Adaptive Intelligence", "🔍 Explainable AI (XAI)", "📋 Reports", "🌐 Global Network Ops"
]
tab_dev, tab6, tab1, tab2, tab3, tab4, tab_xai, tab5, tab0 = st.tabs(tab_names)

with tab_dev:
    from devices_view import draw_devices_dashboard
    draw_devices_dashboard()

with tab0:
    draw_global_header("t0")
    te.section_header("Global Operations Center", "Real-time multi-data-center traffic movement and intelligent routing visualization.", icon="🌐")
    
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
    draw_live_telemetry_chart()

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
    te.section_header("System Analysis & Reports", "Export simulation runs data, validation engine metrics, and routing decisions.", icon="📋")

    r_col1, r_col2 = st.columns([2, 1.2])

    with r_col1:
        st.markdown("### 📊 Available Datasets for Export")
        st.markdown("<p style='color:var(--text-muted); font-size:0.85rem; margin-top:-0.5rem;'>Downloads include all generated JSON data from the latest active simulation run.</p>", unsafe_allow_html=True)

        def safe_read_file(subdir, filename):
            path = os.path.join(BASE_DIR, "outputs", subdir, filename)
            if os.path.exists(path):
                with open(path, "r") as f:
                    return f.read()
            return None

        metrics_data = safe_read_file("raw", "runtime_metrics.json")
        decisions_data = safe_read_file("routing", "routing.json")
        costs_data = safe_read_file("ml", "costs.json")

        import json
        import pandas as pd

        def json_to_csv(json_str, file_type):
            if not json_str: return ""
            try:
                data = json.loads(json_str)
                if file_type == "runtime" and "snapshots" in data:
                    rows = []
                    for snap in data["snapshots"]:
                        ts = snap.get("timestamp")
                        for link in snap.get("links", []):
                            row = {"timestamp": ts}
                            row.update(link)
                            rows.append(row)
                    df = pd.DataFrame(rows)
                elif file_type == "routing" and "decisions" in data:
                    df = pd.DataFrame(data["decisions"])
                else:
                    # Generic flattening attempt
                    if isinstance(data, list):
                        df = pd.json_normalize(data)
                    elif isinstance(data, dict):
                        # Try to find the first list
                        for k, v in data.items():
                            if isinstance(v, list):
                                df = pd.json_normalize(v)
                                break
                        else:
                            df = pd.json_normalize([data])
                return df.to_csv(index=False).encode('utf-8')
            except Exception as e:
                return ""

        metrics_csv = json_to_csv(metrics_data, "runtime")
        decisions_csv = json_to_csv(decisions_data, "routing")
        costs_csv = json_to_csv(costs_data, "ml")

        if metrics_data:
            st.success("✅ **Active Simulation Datasets Found!**")
            
            dcols = st.columns(3)
            with dcols[0]:
                st.download_button(
                    label="📥 Runtime Metrics (CSV)",
                    data=metrics_csv,
                    file_name="runtime_metrics.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="dl_metrics"
                )
                st.caption("Flow statistics and network loads.")

            with dcols[1]:
                st.download_button(
                    label="📥 Routing Decisions (CSV)",
                    data=decisions_csv if decisions_csv else b"",
                    file_name="routing_decisions.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="dl_decisions"
                )
                st.caption("Core routing actions and tiers.")

            with dcols[2]:
                st.download_button(
                    label="📥 ML Cost Models (CSV)",
                    data=costs_csv if costs_csv else b"",
                    file_name="ml_costs.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="dl_costs"
                )
                st.caption("Machine Learning predicted costs.")
        else:
            st.warning("⚠️ **No Active Simulation Data Found**")
            st.info("💡 Run a Python network simulation in the **Simulation Lab** tab to generate exportable datasets.")

    with r_col2:
        st.markdown(f"""
        <div class="cn-glass-panel" style="height: 100%;">
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
                <span style="font-size: 1.2rem;">ℹ️</span>
                <span style="font-size: 1.05rem; font-weight: 600; color: var(--accent-1); font-family: var(--font-display);">Verification Info</span>
            </div>
            <p style="font-size: 0.85rem; color: var(--text-primary); line-height: 1.6;">
                These datasets contain raw metrics generated from the simulation models, which feed directly into our 
                <b>Decision Intelligence Layer</b> and the <b>Explainable AI (XAI)</b> dashboard.
            </p>
            <p style="font-size: 0.85rem; color: var(--text-muted); line-height: 1.6; margin-top: 1rem;">
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
