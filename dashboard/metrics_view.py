import streamlit as st
import plotly.graph_objects as go
import pandas as pd

def draw_metrics_chart(runtime_data):
    """Plot runtime metrics (Queue, Throughput, Loss) across all links."""
    if not runtime_data or "snapshots" not in runtime_data:
        st.warning("No runtime metrics available.")
        return
        
    snapshots = runtime_data["snapshots"]
    
    # Process data for aggregation
    time_series = []
    for snap in snapshots:
        ts = snap["timestamp"]
        total_thru = sum(l.get("throughput_mbps", 0) for l in snap["links"])
        avg_loss = sum(l.get("packet_loss", 0) for l in snap["links"]) / len(snap["links"]) * 100
        avg_util = sum(l.get("link_utilization", 0) for l in snap["links"]) / len(snap["links"]) * 100
        time_series.append({
            "Time": ts,
            "Throughput": total_thru,
            "Loss": avg_loss,
            "Utilization": avg_util
        })
    
    df = pd.DataFrame(time_series)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_thru = go.Figure()
        fig_thru.add_trace(go.Scatter(
            x=df["Time"], y=df["Throughput"], 
            fill='tozeroy', mode='lines', 
            name='Throughput', line=dict(color='#3b82f6', width=3)
        ))
        fig_thru.update_layout(
            title="Aggregate Network Throughput (Mbps)",
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#94a3b8'), height=300,
            margin=dict(l=0, r=0, t=40, b=0),
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
        )
        st.plotly_chart(fig_thru, use_container_width=True)

    with col2:
        fig_health = go.Figure()
        fig_health.add_trace(go.Scatter(
            x=df["Time"], y=df["Loss"], 
            mode='lines+markers', name='Loss (%)',
            line=dict(color='#ef4444', width=2)
        ))
        fig_health.add_trace(go.Scatter(
            x=df["Time"], y=df["Utilization"], 
            mode='lines+markers', name='Util (%)',
            line=dict(color='#10b981', width=2)
        ))
        fig_health.update_layout(
            title="Network Health Indicators",
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#94a3b8'), height=300,
            margin=dict(l=0, r=0, t=40, b=0),
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
        )
        st.plotly_chart(fig_health, use_container_width=True)

def draw_link_details(runtime_data, timestamp):
    """Display detailed metrics for all links at a specific timestamp."""
    st.markdown("### 🔗 Link Intelligence")
    
    if not runtime_data or "snapshots" not in runtime_data:
        st.info("No link data available.")
        return
        
    snap = next((s for s in runtime_data["snapshots"] if s["timestamp"] == timestamp), runtime_data["snapshots"][-1])
    
    links = snap.get("links", [])
    if not links:
        st.info("No active links in this snapshot.")
        return

    # Create a nice table or list of cards
    for link in links:
        src, dst = link["source"] + 1, link["destination"] + 1
        thru = link.get("throughput_mbps", 0)
        loss = link.get("packet_loss", 0) * 100
        util = link.get("link_utilization", 0) * 100
        
        status_color = "#10b981" # Healthy
        if loss > 5 or util > 80: status_color = "#f97316" # Warning
        if loss > 15: status_color = "#ef4444" # Critical

        st.markdown(f"""
        <div style="background: rgba(30, 41, 59, 0.3); padding: 0.8rem; border-radius: 0.5rem; margin-bottom: 0.5rem; border-left: 3px solid {status_color};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 600;">Link {src} → {dst}</span>
                <span style="color: {status_color}; font-size: 0.8rem; font-weight: 700;">{thru:.2f} Mbps</span>
            </div>
            <div style="display: flex; gap: 1rem; margin-top: 0.4rem; font-size: 0.75rem; color: #94a3b8;">
                <span>Loss: {loss:.1f}%</span>
                <span>Util: {util:.1f}%</span>
                <span>Delay: {link.get('delay_ms', 0):.1f}ms</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

