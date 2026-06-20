import streamlit as st
import streamlit.components.v1 as components
import time
from live_engine import LiveNetworkSimulator, append_live_snapshot, clear_live_log
import theme_engine as te


def draw_live_dashboard():
    if "live_sim" not in st.session_state:
        st.session_state.live_sim = LiveNetworkSimulator()
        
    if "is_running" not in st.session_state:
        st.session_state.is_running = False

    sim = st.session_state.live_sim
    state = sim.get_state()
    
    # Load client telemetry once to avoid redundant reads & lock collisions
    import sys
    import os
    _root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _root_dir not in sys.path:
        sys.path.insert(0, _root_dir)
    from telemetry.client_registry import get_registered_clients
    from telemetry.traffic_aggregator import map_throughput_to_load
    
    active_clients = get_registered_clients(timeout=5.0)
    total_throughput = sum(c["total_throughput_mbps"] for c in active_clients)
    client_metrics = {
        "total_throughput_mbps": total_throughput,
        "active_clients_count": len(active_clients),
        "load_level": map_throughput_to_load(total_throughput)
    }
    
    te.section_header("Live Network Operations", "Hybrid Mesh + Hierarchical Spine-Leaf | Real-time ML Evaluation & Partial Rerouting", icon="🔴")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown("### 🎛️ Dynamic Routing Control")
        st.markdown("<p style='color:var(--text-muted); font-size:0.8rem;'>Select custom Source/Destination pairs and inject traffic to see partial routing automatically optimize the core paths.</p>", unsafe_allow_html=True)
        
        dc_map = {
            "DC1 (Origin)": 2,
            "DC2 (Compute A)": 5,
            "DC3 (Compute B)": 8,
            "DC4 (Storage)": 11,
            "DC5 (Backup)": 14
        }
        
        dc_names = list(dc_map.keys())
        
        # Import telemetry modules
        import sys
        import os
        _root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if _root_dir not in sys.path:
            sys.path.insert(0, _root_dir)
        from telemetry.traffic_aggregator import get_aggregate_metrics
        
        st.markdown("<h4 style='color:var(--accent-1); font-family:var(--font-display); margin-bottom:0.25rem;'>Traffic Sourcing Mode</h4>", unsafe_allow_html=True)
        traffic_mode = st.selectbox("Sourcing Mode", ["Simulation", "Real Client", "Hybrid"], index=0, key="traffic_source_mode")
        
        st.markdown("<h4 style='color:var(--accent-1); font-family:var(--font-display); margin-bottom:0.25rem;'>Flow 1</h4>", unsafe_allow_html=True)
        f1_c1, f1_c2 = st.columns(2)
        with f1_c1: src1 = st.selectbox("Source 1", dc_names, index=0)
        with f1_c2: dst1 = st.selectbox("Dest 1", dc_names, index=2)
        
        if traffic_mode == "Real Client":
            v1 = client_metrics["total_throughput_mbps"]
            st.markdown(f"""
            <div style="background:rgba(0, 212, 255, 0.1); padding:0.5rem; border-radius:0.5rem; border:1px solid rgba(0, 212, 255, 0.3); margin-bottom:0.5rem;">
                <div style="font-size:0.8rem; color:var(--text-muted);">Real Telemetry Bandwidth:</div>
                <div style="font-size:1.1rem; font-weight:bold; color:var(--accent-1);">{v1:.2f} Mbps</div>
            </div>
            """, unsafe_allow_html=True)
        elif traffic_mode == "Hybrid":
            real_v1 = client_metrics["total_throughput_mbps"]
            st.markdown(f"""
            <div style="background:rgba(0, 212, 255, 0.1); padding:0.5rem; border-radius:0.5rem; border:1px solid rgba(0, 212, 255, 0.3); margin-bottom:0.5rem;">
                <div style="font-size:0.8rem; color:var(--text-muted);">Real Telemetry Bandwidth:</div>
                <div style="font-size:1.1rem; font-weight:bold; color:var(--accent-1);">{real_v1:.2f} Mbps</div>
            </div>
            """, unsafe_allow_html=True)
            sim_v1 = st.slider("Simulated Traffic Volume (Mbps)", 0, 800, 0, 50, key="sim_v1")
            v1 = real_v1 + sim_v1
        else:
            v1 = st.slider("Traffic Volume 1 (Mbps)", 0, 800, sim.flows.get("flow_1", {}).get("volume", 0), 50, key="v1")
        
        s1 = sim.flows.get("flow_1", {}).get("status", "Normal Path (100%)")
        c1_color = te.COLORS["accent_3"] if "Normal" in s1 else te.COLORS["warning"]
        st.markdown(f"<div style='color:{c1_color}; font-size:0.85rem; font-weight:bold; margin-bottom:1rem; font-family:var(--font-display);'>Routing: {s1}</div>", unsafe_allow_html=True)
        
        st.markdown("<h4 style='color:var(--accent-2); font-family:var(--font-display); margin-bottom:0.25rem;'>Flow 2</h4>", unsafe_allow_html=True)
        f2_c1, f2_c2 = st.columns(2)
        with f2_c1: src2 = st.selectbox("Source 2", dc_names, index=1)
        with f2_c2: dst2 = st.selectbox("Dest 2", dc_names, index=3)
        v2 = st.slider("Traffic Volume 2 (Mbps)", 0, 800, sim.flows.get("flow_2", {}).get("volume", 0), 50, key="v2")
        
        s2 = sim.flows.get("flow_2", {}).get("status", "Normal Path (100%)")
        c2_color = te.COLORS["accent_3"] if "Normal" in s2 else te.COLORS["warning"]
        st.markdown(f"<div style='color:{c2_color}; font-size:0.85rem; font-weight:bold; margin-bottom:1rem; font-family:var(--font-display);'>Routing: {s2}</div>", unsafe_allow_html=True)

        # ── Scenario Orchestration (Context-Aware Events) ──
        st.markdown("#### 📅 Scenario Orchestration")
        with st.expander("Add Context-Aware Event"):
            ev_type = st.selectbox("Event Type", ["traffic_burst", "network_failure", "future_congestion"])
            ev_sev = st.slider("Severity", 0.0, 1.0, 0.8)
            ev_start = st.number_input("Start Time (s)", min_value=0.0, value=sim.time_step * 2.0 + 10.0, step=2.0)
            ev_dur = st.number_input("Duration (s)", min_value=2.0, value=20.0, step=2.0)

            link_opts = [f"{u}-{v}" for u, v in [(4, 15), (7, 16), (15, 16), (16, 17)]]
            ev_link_str = st.selectbox("Affected Link", link_opts)
            ev_u, ev_v = map(int, ev_link_str.split('-'))

            if st.button("Schedule Event"):
                eid = sim.event_repo.add_event(ev_type, ev_sev, ev_start, ev_dur, [(ev_u, ev_v), (ev_v, ev_u)])
                st.success(f"Added {eid}")

        active_evs = sim.event_repo.get_active_events(sim.time_step * 2.0)
        up_evs = sim.event_repo.get_upcoming_events(sim.time_step * 2.0)
        if active_evs or up_evs:
            st.markdown(f"<div style='background:rgba(239,68,68,0.1); padding:0.5rem; border-radius:0.5rem; border:1px solid {te.COLORS['danger']}; color:var(--text-primary); font-size:0.85rem;'>", unsafe_allow_html=True)
            st.markdown(f"**Active Events:** {len(active_evs)} | **Upcoming:** {len(up_evs) - len(active_evs)}")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("#### Playback Speed")
        play_speed = st.slider("Simulation Speed", 0.5, 5.0, 1.0, 0.5)

        st.markdown("---")
        if st.button("▶️ Start / ⏸️ Pause", use_container_width=True):
            st.session_state.is_running = not st.session_state.is_running
            if st.session_state.is_running:
                st.session_state.show_live_analysis = False
            
        if st.button("🔄 Reset Engine", use_container_width=True):
            st.session_state.live_sim = LiveNetworkSimulator()
            st.session_state.is_running = False
            st.session_state.show_live_analysis = False
            st.rerun()

        if st.button("🗑️ Clear Telemetry Log", use_container_width=True, type="secondary"):
            clear_live_log()
            # Also reset in-memory history on the current engine
            sim.history = {"snapshots": [], "costs": [], "routing": []}
            st.success("✅ Telemetry log cleared.")
            st.rerun()

        if not st.session_state.is_running:
            st.markdown("---")
            if st.button("📊 Generate Performance Analysis", use_container_width=True):
                st.session_state.show_live_analysis = True
                
        if st.session_state.get("show_live_analysis") and not st.session_state.is_running:
            st.markdown("### 📈 Real-Time Engine Report")
            
            max_util = 0.0
            max_lat = 0.0
            total_loss = 0.0
            for l in state["links"]:
                u = l["throughput"] / l["capacity"] if l["capacity"] else 0
                if u > max_util: max_util = u
                if l["latency"] > max_lat: max_lat = l["latency"]
                total_loss += l["loss"]
                
            st.markdown(f"**Peak Link Utilization:** `{max_util*100:.1f}%`")
            st.markdown(f"**Max Latency Spike:** `{max_lat:.1f} ms`")
            st.markdown(f"**Network Packets Dropped:** `{total_loss:.2f}%`")
            
            for f_id, f in state["flows"].items():
                if f["volume"] > 0:
                    status = f["status"]
                    if "Mega-Split" in status or "Global" in status or "Cross-DC" in status:
                        st.info(f"**{f_id.upper()} ({f['volume']} Mbps):** ML Model enacted Tier-3 Cross-DC Split. Traffic successfully spilled over to external datacenter to prevent node failure. Optimal global load balancing achieved.")
                    elif "Same-DC" in status or "Partial" in status:
                        st.warning(f"**{f_id.upper()} ({f['volume']} Mbps):** ML Model enacted Tier-2 Sibling Load Balance. Internal Datacenter traffic distributed across 2 nodes to prevent single-server bottleneck.")
                    else:
                        st.success(f"**{f_id.upper()} ({f['volume']} Mbps):** Network stable. Tier-1 Direct Routing maintained via primary path.")
                        
            history = sim.history.get("snapshots", [])
            if len(history) > 1:
                st.markdown("#### 📊 Temporal Telemetry Trends")
                import pandas as pd
                time_data = []
                for snap in history:
                    t = snap["timestamp"]
                    max_lat = max([l.get("delay_ms", 0) for l in snap["links"]]) if snap["links"] else 0
                    max_util = max([l.get("queue_utilization", 0) for l in snap["links"]]) if snap["links"] else 0
                    total_loss = sum([l.get("packet_loss", 0) for l in snap["links"]]) if snap["links"] else 0
                    time_data.append({
                        "Time": t,
                        "Peak Latency (ms)": max_lat,
                        "Peak Queue Util (%)": max_util * 100,
                        "Total Packet Loss (%)": total_loss
                    })
                df = pd.DataFrame(time_data).set_index("Time")
                st.line_chart(df)

            # ── XAI Decision Intelligence Summary (human-readable) ──
            st.markdown("#### 🧠 XAI Decision Intelligence Logs")
            logs = sim.di_module.get_latest_logs(limit=2)
            if logs:
                for log in logs:
                    rm = log.get("routing_metrics", {})
                    cm = log.get("context_metrics", {})
                    conf = log.get("confidence_metrics", {})
                    tier = rm.get("routing_tier", "Unknown")
                    frs_val = cm.get("future_risk_score", 0.0)
                    conf_val = conf.get("decision_confidence", 1.0) * 100

                    with st.expander(f"Decision — {log['flow_id']} @ t={log['timestamp']}s  |  {tier}"):
                        st.markdown(f"**Routing Tier:** `{tier}`")
                        st.markdown(f"**Decision Confidence:** `{conf_val:.0f}%`  |  **Future Risk Score:** `{frs_val:.2f}`")

                        active_paths = rm.get("active_paths", [])
                        if active_paths:
                            st.markdown("**Active Traffic Split:**")
                            for ap in active_paths:
                                path_str = " → ".join(map(str, ap["path"]))
                                st.markdown(
                                    f"- **{ap['type'].title()}** path `{path_str}` — "
                                    f"**{ap['percent']:.0f}%** ({ap['volume_mbps']} Mbps)  "
                                    f"Latency: {ap['latency']} ms | ML Cost: {ap['ml_cost']}"
                                )
            else:
                st.caption("No decision logs yet — start the simulator to generate routing intelligence.")


    with col2:
        # Direct SVG coordinates (800x600 canvas)
        pos = {
            1: (150, 150), 2: (100, 80), 3: (200, 80),      # DC1
            4: (400, 150), 5: (350, 80), 6: (450, 80),      # DC2
            7: (650, 150), 8: (600, 80), 9: (700, 80),      # DC3
            10: (250, 450), 11: (200, 520), 12: (300, 520), # DC4
            13: (550, 450), 14: (550, 520),                 # DC5
            15: (300, 300), 16: (400, 300), 17: (500, 300), # Core Mesh
            18: (300, 200), 19: (500, 200)                  # Buffer Nodes
        }
        
        groups = {
            "DC1 (Origin)": [1,2,3],
            "DC2 (Compute A)": [4,5,6],
            "DC3 (Compute B)": [7,8,9],
            "DC4 (Storage)": [10,11,12],
            "DC5 (Backup)": [13,14],
            "Core Mesh": [15,16,17],
            "Buffer Zone": [18,19]
        }
        
        svg_elements = []
        
        # Draw Group Bounding Boxes
        for g_name, g_nodes in groups.items():
            xs = [pos[n][0] for n in g_nodes]
            ys = [pos[n][1] for n in g_nodes]
            min_x, max_x = min(xs) - 40, max(xs) + 40
            min_y, max_y = min(ys) - 40, max(ys) + 40
            w = max_x - min_x
            h = max_y - min_y
            
            box_color = "rgba(0, 212, 255, 0.2)"
            text_color = "#00d4ff"
            if "DC2" in g_name or "DC5" in g_name or "Buffer" in g_name:
                box_color = "rgba(124, 58, 237, 0.2)"
                text_color = "#7c3aed"
            elif "DC3" in g_name:
                box_color = "rgba(0, 255, 136, 0.2)"
                text_color = "#00ff88"
            
            svg_elements.append(f'<rect x="{min_x}" y="{min_y}" width="{w}" height="{h}" rx="10" fill="rgba(5, 13, 26, 0.4)" stroke="{box_color}" stroke-width="1.5" stroke-dasharray="4" />')
            svg_elements.append(f'<text x="{min_x + w/2}" y="{min_y + 16}" font-family="Exo 2, DM Sans" font-size="11" font-weight="bold" fill="{text_color}" text-anchor="middle">{g_name}</text>')
            
        # Draw edges & animated packets
        for l in state["links"]:
            u, v = l["src"], l["dst"]
            if u > v: continue 
            
            x1, y1 = pos[u][0], pos[u][1]
            x2, y2 = pos[v][0], pos[v][1]
            
            is_active = False
            edge_types = set()
            for f_id, f in state["flows"].items():
                if f["volume"] > 0:
                    for p_info in f["paths"]:
                        p = p_info["path"]
                        ptype = p_info.get("type", "primary")
                        for i in range(len(p)-1):
                            if (p[i] == u and p[i+1] == v) or (p[i] == v and p[i+1] == u):
                                is_active = True
                                is_active = True
                                edge_types.add(ptype)
                                
            cost = l["cost"]
            thru = l["throughput"]
            
            color = 'rgba(0, 212, 255, 0.1)'
            width = 1.5
            
            if is_active:
                width = 2.5
                if "rerouted" in edge_types and "primary" in edge_types:
                    color = '#7c3aed' # Purple if shared
                elif "rerouted" in edge_types:
                    color = '#f59e0b' # Orange for rerouted
                else:
                    color = '#00d4ff' # Blue for primary
            
            if cost > 9000:
                color = '#ef4444'
                width = 3.0
                
            path_id = f"path_{u}_{v}"
            svg_elements.append(f'<path id="{path_id}" d="M{x1},{y1} L{x2},{y2}" stroke="{color}" stroke-width="{width}" fill="none" />')
            
            path_id_rev = f"path_{v}_{u}"
            svg_elements.append(f'<path id="{path_id_rev}" d="M{x2},{y2} L{x1},{y1}" stroke="none" fill="none" />')
            
            # Packet Animation CSS
            if is_active and st.session_state.is_running:
                for f_id, f in state["flows"].items():
                    if f["volume"] == 0: continue
                    for p_info in f["paths"]:
                        p = p_info["path"]
                        ptype = p_info.get("type", "primary")
                        pweight = p_info["weight"]
                        
                        # Find direction on this link
                        link_dir = None
                        for i in range(len(p)-1):
                            if p[i] == u and p[i+1] == v:
                                link_dir = "forward"
                            elif p[i] == v and p[i+1] == u:
                                link_dir = "reverse"
                                
                        if link_dir:
                            path_vol = f["volume"] * pweight
                            if path_vol > 5.0:
                                base_dur = max(0.4, 2.5 - (path_vol / 200.0))
                                duration = base_dur / play_speed
                                num_particles = min(12, max(2, int(path_vol / 40.0)))
                                
                                particle_color = "#f59e0b" if ptype == "rerouted" else "#00d4ff"
                                target_path_id = path_id if link_dir == "forward" else path_id_rev
                                
                                for i in range(num_particles):
                                    delay = (duration / num_particles) * i
                                    svg_elements.append(f'''
                                    <circle r="3" fill="{particle_color}" filter="drop-shadow(0 0 4px {particle_color})">
                                        <animateMotion dur="{duration}s" begin="{delay}s" repeatCount="indefinite">
                                            <mpath href="#{target_path_id}" />
                                        </animateMotion>
                                    </circle>
                                    ''')

        # Draw nodes
        for n in sim.nodes:
            x, y = pos[n][0], pos[n][1]
            color = "#00ff88"
            if n in [15,16,17]: color = "#38bdf8"
            elif n in [18,19]: color = "#7c3aed"
            elif n in [1,4,7,10,13]: color = "#00ff88"
            
            svg_elements.append(f'<circle cx="{x}" cy="{y}" r="16" fill="#132238" stroke="{color}" stroke-width="3" />')
            svg_elements.append(f'<text x="{x}" y="{y+4}" font-family="Exo 2, DM Sans" font-size="11" font-weight="bold" fill="#e2e8f0" text-anchor="middle">{n}</text>')
            
        html_code = f'''
        <div style="background-color: #050d1a; width: 100%; height: 500px; border-radius: 10px; border: 1px solid rgba(0, 212, 255, 0.08); display: flex; justify-content: center; align-items: center; overflow: hidden;">
            <svg width="800" height="600" viewBox="0 0 800 600">
                {"".join(svg_elements)}
            </svg>
        </div>
        '''
        components.html(html_code, height=520)

    # ── Real-Time Telemetry Dashboard (Aggregator & registry) ──
    st.markdown("---")
    st.markdown("### 🔌 Real-Time Distributed Telemetry Dashboard")
    
    tc1, tc2 = st.columns([1, 2])
    
    with tc1:
        st.markdown("#### 📡 Traffic Demand Overview")
        
        st.markdown(f"""
        <div style="background:rgba(5, 13, 26, 0.6); padding:1.5rem; border-radius:0.75rem; border:1px solid rgba(0, 212, 255, 0.15); border-left:4px solid var(--accent-1);">
            <div style="font-size:0.9rem; color:var(--text-muted); margin-bottom:0.25rem;">Active Clients Count</div>
            <div style="font-size:1.8rem; font-weight:700; color:var(--text-primary); margin-bottom:1rem;">{client_metrics['active_clients_count']}</div>
            <div style="font-size:0.9rem; color:var(--text-muted); margin-bottom:0.25rem;">Total Aggregated Throughput</div>
            <div style="font-size:1.8rem; font-weight:700; color:var(--accent-1); margin-bottom:1rem;">{client_metrics['total_throughput_mbps']:.2f} Mbps</div>
            <div style="font-size:0.9rem; color:var(--text-muted); margin-bottom:0.25rem;">Current Load Level</div>
            <div style="font-size:1.4rem; font-weight:700; color:{te.COLORS['success'] if 'Low' in client_metrics['load_level'] else (te.COLORS['warning'] if 'Medium' in client_metrics['load_level'] else te.COLORS['danger'])};">{client_metrics['load_level']}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with tc2:
        st.markdown("#### 🖥️ Connected Client Agents")
        
        if active_clients:
            table_rows = []
            for c in active_clients:
                ls = c["last_seen"]
                if isinstance(ls, str):
                    try:
                        from datetime import datetime
                        last_seen_sec = (datetime.now() - datetime.fromisoformat(ls)).total_seconds()
                    except ValueError:
                        last_seen_sec = 0.0
                else:
                    last_seen_sec = time.time() - float(ls)
                table_rows.append(
                    f"| `{c['device_id'][:8]}...` | **{c['total_throughput_mbps']:.2f} Mbps** | {c['upload_rate_mbps']} Mbps | {c['download_rate_mbps']} Mbps | {c['active_connections']} | {last_seen_sec:.1f}s ago |"
                )
            
            st.markdown(
                "| Device ID | Current Throughput | Upload Rate | Download Rate | Active Conn | Last Seen |\n"
                "| :--- | :--- | :--- | :--- | :--- | :--- |\n" + 
                "\n".join(table_rows),
                unsafe_allow_html=True
            )
        else:
            st.info("💡 **Awaiting Client Connections** — Run `python agent.py` on client devices to send telemetry.")

        
    if st.session_state.is_running:
        sim.set_flow("flow_1", dc_map[src1], dc_map[dst1], v1)
        sim.set_flow("flow_2", dc_map[src2], dc_map[dst2], v2)
        sim.step(ignore_events=(traffic_mode == "Real Client"))
        # Persist this step to the permanent telemetry log
        append_live_snapshot(sim)
        time.sleep(1.0 / play_speed)
        st.rerun()
