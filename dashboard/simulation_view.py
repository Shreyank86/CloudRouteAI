import streamlit as st
import subprocess
import time
from dash_utils import BASE_DIR
from network_simulator import run_simulation, save_simulation_results, SCENARIO_CONFIG
import theme_engine as te

def draw_simulation_lab(scenario):
    """Render the simulation lab with dual-engine support."""

    te.section_header("Traffic Simulation Lab", "Run network simulations using the built-in NetworkX engine (instant) or the full NS-3 pipeline.", icon="⚡")

    # Simulation engine cards
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(0, 212, 255, 0.15), rgba(0, 212, 255, 0.02)); 
                    padding: 1.5rem; border-radius: 1rem; border: 1px solid rgba(0, 212, 255, 0.3);
                    height: 100%;">
            <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
                <span style="font-size: 1.8rem;">🐍</span>
                <div>
                    <div style="font-weight: 700; color: var(--accent-1); font-size: 1.1rem; font-family: var(--font-display);">NetworkX Engine</div>
                    <div style="color: var(--text-muted); font-size: 0.8rem;">Pure Python • Instant Results</div>
                </div>
            </div>
            <ul style="color: var(--text-primary); font-size: 0.85rem; padding-left: 1.2rem;">
                <li>Same topology as NS-3 (11 nodes)</li>
                <li>Dijkstra adaptive routing</li>
                <li>ML cost computation inline</li>
                <li>No compilation needed</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚀 Run NetworkX Simulation", key="run_nx", use_container_width=True):
            with st.spinner("Simulating network traffic..."):
                try:
                    start = time.time()
                    base_runtime, base_costs, base_routing = run_simulation(scenario, adaptive=False)
                    runtime, costs, routing = run_simulation(scenario, adaptive=True)
                    save_simulation_results(runtime, costs, routing, base_runtime, base_routing)
                    elapsed = time.time() - start

                    st.success(f"✅ Simulation complete in {elapsed:.2f}s!")
                    
                    # Compute summary variables first
                    n_snaps = len(runtime.get("snapshots", []))
                    n_decisions = len(routing.get("decisions", []))
                    classified = costs.get("classified_scenario", "unknown")

                    st.markdown(f"""
                    <div style="background: rgba(0, 255, 136, 0.1); padding: 1rem; border-radius: 0.5rem; border: 1px solid rgba(0, 255, 136, 0.3); margin-bottom: 1rem;">
                        <div style="color: var(--accent-3); font-weight: 700; margin-bottom: 0.5rem; font-family: var(--font-display);">🎯 Analysis Ready</div>
                        <div style="color: var(--text-muted); font-size: 0.85rem;">
                            The network was classified as <b>{classified.upper()}</b>. 
                            New routing decisions ({n_decisions}) have been generated using the ML model.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Show metrics
                    cols = st.columns(3)
                    with cols[0]:
                        te.metric_card("Snapshots", str(n_snaps), icon="📸", color=te.COLORS["accent_1"], idx=0)
                    with cols[1]:
                        te.metric_card("Routing Decisions", str(n_decisions), icon="🧠", color=te.COLORS["accent_2"], idx=1)
                    with cols[2]:
                        te.metric_card("Classification", classified.upper(), icon="🏷️", color=te.COLORS["warning"] if "congest" in classified else te.COLORS["success"], idx=2)

                    st.session_state.active_tab_label = "⚡ Simulation Lab"
                    st.rerun()
                except Exception as e:
                    st.error(f"Simulation error: {str(e)}")

    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(124, 58, 237, 0.15), rgba(124, 58, 237, 0.02)); 
                    padding: 1.5rem; border-radius: 1rem; border: 1px solid rgba(124, 58, 237, 0.3);
                    height: 100%;">
            <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
                <span style="font-size: 1.8rem;">🔬</span>
                <div>
                    <div style="font-weight: 700; color: #8b5cf6; font-size: 1.1rem; font-family: var(--font-display);">NS-3 Pipeline</div>
                    <div style="color: var(--text-muted); font-size: 0.8rem;">Full C++ Simulation • High Fidelity</div>
                </div>
            </div>
            <ul style="color: var(--text-primary); font-size: 0.85rem; padding-left: 1.2rem;">
                <li>FlowMonitor packet-level metrics</li>
                <li>NetAnim visualization output</li>
                <li>ML cost prediction (RandomForest)</li>
                <li>Requires NS-3 installation</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔬 Run NS-3 Pipeline", key="run_ns3", use_container_width=True):
            with st.spinner("Running full NS-3 pipeline (this may take 30-60s)..."):
                try:
                    result = subprocess.run(
                        ["bash", "run_all.sh", scenario],
                        cwd=BASE_DIR,
                        capture_output=True, text=True,
                        timeout=120
                    )
                    if result.returncode == 0:
                        st.session_state.active_tab_label = "⚡ Simulation Lab"
                        st.rerun()
                    else:
                        st.error("Pipeline failed. See details below.")
                        with st.expander("🔍 Debug Output"):
                            st.code(result.stdout[-2000:] if result.stdout else "No stdout")
                            st.code(result.stderr[-2000:] if result.stderr else "No stderr")
                except subprocess.TimeoutExpired:
                    st.error("Pipeline timed out after 120 seconds.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    st.markdown("---")

    # Scenario details
    st.markdown("### 📋 Scenario Configuration")
    config = SCENARIO_CONFIG.get(scenario, {})

    detail_cols = st.columns(4)
    with detail_cols[0]:
        te.metric_card("Traffic Rate", f"{config.get('traffic_rate_pps', 200)} pps", icon="📊", color=te.COLORS["accent_1"], idx=0)
    with detail_cols[1]:
        n_overrides = len(config.get("link_overrides", {}))
        te.metric_card("Link Overrides", f"{n_overrides} links", icon="🔗", color=te.COLORS["warning"] if n_overrides > 0 else te.COLORS["success"], idx=1)
    with detail_cols[2]:
        n_events = len(config.get("events", []))
        te.metric_card("Events Scheduled", f"{n_events} events", icon="📅", color=te.COLORS["danger"] if n_events > 0 else te.COLORS["success"], idx=2)
    with detail_cols[3]:
        path_str = "→".join(str(n+1) for n in config.get("initial_path", [0,1,2,3,4,5,6,7]))
        is_alt = config.get("initial_path") == [0,1,2,8,9,4,5,6,7]
        te.metric_card("Initial Path", f"{'ALT' if is_alt else 'PRIMARY'}", icon="🗺️", color=te.COLORS["accent_2"] if is_alt else te.COLORS["accent_1"], idx=3)

