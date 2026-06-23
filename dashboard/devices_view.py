import streamlit as st
import streamlit.components.v1 as components
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


    # --- Inject stat cards CSS (div-based, safe for st.markdown) ---
    st.markdown("""
    <style>
    .devices-stats-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .device-stat-card {
        background: rgba(13, 27, 46, 0.6);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(0, 212, 255, 0.1);
        border-radius: 16px;
        padding: 1.25rem 1.5rem;
        position: relative;
        overflow: hidden;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        animation: devSlideUp 0.5s ease-out both;
    }
    .device-stat-card:hover {
        transform: translateY(-3px);
        border-color: rgba(0, 212, 255, 0.25);
        box-shadow: 0 12px 40px rgba(0, 212, 255, 0.1);
    }
    .device-stat-card .stat-icon {
        font-size: 1.3rem;
        margin-bottom: 0.6rem;
        filter: drop-shadow(0 0 8px rgba(0, 212, 255, 0.4));
    }
    .device-stat-card .stat-label {
        font-size: 0.7rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 600;
        font-family: 'Exo 2', sans-serif;
        margin-bottom: 0.3rem;
    }
    .device-stat-card .stat-value {
        font-family: 'Exo 2', sans-serif;
        font-size: 1.8rem;
        font-weight: 800;
        line-height: 1.1;
    }
    .device-stat-card .stat-sub {
        font-size: 0.75rem;
        color: #64748b;
        margin-top: 0.4rem;
        font-family: 'DM Sans', sans-serif;
    }
    @keyframes devSlideUp {
        from { opacity: 0; transform: translateY(20px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    </style>
    """, unsafe_allow_html=True)

    # --- Determine load color ---
    load_level = client_metrics['load_level']
    if 'Low' in load_level:
        load_color = te.COLORS['success']
        load_icon = "🟢"
    elif 'Medium' in load_level:
        load_color = te.COLORS['warning']
        load_icon = "🟡"
    else:
        load_color = te.COLORS['danger']
        load_icon = "🔴"

    # --- Stat Cards Row (div-based, safe for st.markdown) ---
    st.markdown(f"""
    <div class="devices-stats-grid">
        <div class="device-stat-card" style="animation-delay:0s;">
            <div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg, #00d4ff, #7c3aed);border-radius:16px 16px 0 0;"></div>
            <div class="stat-icon">👥</div>
            <div class="stat-label">Active Clients</div>
            <div class="stat-value" style="background:linear-gradient(135deg,#00d4ff,#7c3aed);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">{client_metrics['active_clients_count']}</div>
            <div class="stat-sub">Connected devices sending telemetry</div>
        </div>
        <div class="device-stat-card" style="animation-delay:0.1s;">
            <div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg, #00d4ff, #00ff88);border-radius:16px 16px 0 0;"></div>
            <div class="stat-icon">📡</div>
            <div class="stat-label">Total Throughput</div>
            <div class="stat-value" style="color:#00d4ff;">{client_metrics['total_throughput_mbps']:.2f} <span style="font-size:0.9rem;font-weight:500;color:#64748b;">Mbps</span></div>
            <div class="stat-sub">Aggregated bandwidth across all agents</div>
        </div>
        <div class="device-stat-card" style="animation-delay:0.2s;">
            <div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg, {load_color}, {load_color}88);border-radius:16px 16px 0 0;"></div>
            <div class="stat-icon">{load_icon}</div>
            <div class="stat-label">Load Level</div>
            <div class="stat-value" style="color:{load_color};font-size:1.5rem;">{load_level}</div>
            <div class="stat-sub">Current network demand classification</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Connected Client Agents Table (rendered via components.html to avoid sanitization) ---
    _table_css = """
    .agents-table-wrapper {
        background: rgba(13, 27, 46, 0.5);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(0, 212, 255, 0.08);
        border-radius: 16px;
        overflow: hidden;
        animation: fadeIn 0.6s ease-out both;
        margin-top: 1.5rem;
    }
    .agents-table-wrapper * {
        box-sizing: border-box;
    }
    .agents-table-header {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding: 1.25rem 1.5rem;
        border-bottom: 1px solid rgba(0, 212, 255, 0.08);
    }
    .agents-table-header h3 {
        margin: 0 !important;
        font-family: 'Exo 2', sans-serif !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        color: #e2e8f0 !important;
    }
    .count-badge {
        background: rgba(0, 212, 255, 0.12);
        color: #00d4ff;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-family: 'Exo 2', sans-serif;
        letter-spacing: 0.05em;
    }
    .agents-table {
        width: 100%;
        border-collapse: collapse;
        margin: 0;
    }
    .agents-table thead th {
        padding: 0.8rem 1rem;
        font-family: 'Exo 2', sans-serif;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #64748b;
        background: rgba(5, 13, 26, 0.4);
        border-bottom: 1px solid rgba(0, 212, 255, 0.06);
        text-align: left;
        white-space: nowrap;
    }
    .agents-table tbody tr {
        transition: all 0.2s ease;
        border-bottom: 1px solid rgba(0, 212, 255, 0.04);
    }
    .agents-table tbody tr:hover {
        background: rgba(0, 212, 255, 0.04);
    }
    .agents-table tbody tr:last-child { border-bottom: none; }
    .agents-table tbody td {
        padding: 0.9rem 1rem;
        font-family: 'DM Sans', sans-serif;
        font-size: 0.85rem;
        color: #e2e8f0;
        white-space: nowrap;
        vertical-align: middle;
    }
    .device-id-cell {
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .device-id-dot {
        width: 8px; height: 8px;
        border-radius: 50%;
        background: #00ff88;
        box-shadow: 0 0 8px rgba(0, 255, 136, 0.5);
        animation: dotPulse 2s ease-in-out infinite;
        flex-shrink: 0;
    }
    .device-id-text {
        font-family: 'Exo 2', monospace;
        font-size: 0.82rem;
        color: #00d4ff;
        background: rgba(0, 212, 255, 0.08);
        padding: 0.2rem 0.5rem;
        border-radius: 6px;
        font-weight: 600;
    }
    .throughput-value {
        font-family: 'Exo 2', sans-serif;
        font-weight: 700;
        color: #00d4ff;
        font-size: 0.9rem;
    }
    .rate-value { color: #94a3b8; font-size: 0.82rem; }
    .conn-badge {
        background: rgba(124, 58, 237, 0.12);
        color: #a78bfa;
        padding: 0.2rem 0.6rem;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.82rem;
        font-family: 'Exo 2', sans-serif;
        display: inline-block;
    }
    .lastseen-badge { color: #10b981; font-size: 0.8rem; font-weight: 600; }
    .lastseen-badge.stale { color: #f59e0b; }
    .agents-empty-state { text-align: center; padding: 3rem 2rem; }
    .agents-empty-state .empty-icon { font-size: 2.5rem; margin-bottom: 1rem; opacity: 0.5; }
    .agents-empty-state .empty-title {
        font-family: 'Exo 2', sans-serif; font-size: 1.1rem;
        font-weight: 700; color: #e2e8f0; margin-bottom: 0.5rem;
    }
    .agents-empty-state .empty-desc {
        color: #64748b; font-size: 0.85rem;
        font-family: 'DM Sans', sans-serif; line-height: 1.5;
    }
    .agents-empty-state code {
        background: rgba(0, 212, 255, 0.1); color: #00d4ff;
        padding: 0.2rem 0.5rem; border-radius: 6px; font-size: 0.82rem;
    }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    @keyframes dotPulse {
        0%, 100% { box-shadow: 0 0 4px rgba(0, 255, 136, 0.3); }
        50%      { box-shadow: 0 0 12px rgba(0, 255, 136, 0.7); }
    }
    """
 
    if active_clients:
        from datetime import datetime
        table_rows_html = ""
        for c in active_clients:
            ls = c["last_seen"]
            if isinstance(ls, str):
                try:
                    last_seen_sec = (datetime.now() - datetime.fromisoformat(ls)).total_seconds()
                except ValueError:
                    last_seen_sec = 0.0
            else:
                last_seen_sec = time.time() - float(ls)
            
            stale_class = "stale" if last_seen_sec > 30 else ""
            device_short = c['device_id'][:10]
            
            table_rows_html += f"""
            <tr>
                <td>
                    <div class="device-id-cell">
                        <div class="device-id-dot"></div>
                        <span class="device-id-text">{device_short}…</span>
                    </div>
                </td>
                <td><span class="throughput-value">{c['total_throughput_mbps']:.2f} Mbps</span></td>
                <td><span class="rate-value">↑ {c['upload_rate_mbps']:.2f} Mbps</span></td>
                <td><span class="rate-value">↓ {c['download_rate_mbps']:.2f} Mbps</span></td>
                <td><span class="conn-badge">{c['active_connections']}</span></td>
                <td><span class="lastseen-badge {stale_class}">{last_seen_sec:.1f}s ago</span></td>
            </tr>
            """

        st.markdown(f"""
        <style>{_table_css}</style>
        <div class="agents-table-wrapper">
            <div class="agents-table-header">
                <span style="font-size:1.2rem;">🖥️</span>
                <h3>Connected Client Agents</h3>
                <span class="count-badge">{len(active_clients)} ONLINE</span>
            </div>
            <table class="agents-table">
                <thead>
                    <tr>
                        <th>Device ID</th>
                        <th>Throughput</th>
                        <th>Upload Rate</th>
                        <th>Download Rate</th>
                        <th>Connections</th>
                        <th>Last Seen</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows_html}
                </tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <style>{_table_css}</style>
        <div class="agents-table-wrapper">
            <div class="agents-table-header">
                <span style="font-size:1.2rem;">🖥️</span>
                <h3>Connected Client Agents</h3>
                <span class="count-badge">0 ONLINE</span>
            </div>
            <div class="agents-empty-state">
                <div class="empty-icon">📡</div>
                <div class="empty-title">Awaiting Client Connections</div>
                <div class="empty-desc">
                    Run <code>python agent.py</code> on client devices to start sending telemetry data.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

