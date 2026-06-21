import streamlit as st
import time
import theme_engine as te

def draw_devices_dashboard():
    te.section_header("Devices & Telemetry", "Real-Time Distributed Telemetry Dashboard", icon="🖥️")
    
    # Load client telemetry
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
                "| Device ID | Current Throughput | Upload Rate | Download Rate | Active Conn | Last Seen |\\n"
                "| :--- | :--- | :--- | :--- | :--- | :--- |\\n" + 
                "\\n".join(table_rows),
                unsafe_allow_html=True
            )
        else:
            st.info("💡 **Awaiting Client Connections** — Run `python agent.py` on client devices to send telemetry.")
