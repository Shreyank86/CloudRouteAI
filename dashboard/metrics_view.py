import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import theme_engine as te

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
            name='Throughput', line=dict(color=te.CHART_COLORS["primary"], width=3)
        ))
        
        layout_thru = te.chart_theme()
        layout_thru.update(title="Aggregate Network Throughput (Mbps)", height=300)
        fig_thru.update_layout(layout_thru)
        st.plotly_chart(fig_thru, use_container_width=True)

    with col2:
        fig_health = go.Figure()
        fig_health.add_trace(go.Scatter(
            x=df["Time"], y=df["Loss"], 
            mode='lines+markers', name='Loss (%)',
            line=dict(color=te.CHART_COLORS["danger"], width=2)
        ))
        fig_health.add_trace(go.Scatter(
            x=df["Time"], y=df["Utilization"], 
            mode='lines+markers', name='Util (%)',
            line=dict(color=te.CHART_COLORS["success"], width=2)
        ))
        
        layout_health = te.chart_theme()
        layout_health.update(title="Network Health Indicators", height=300)
        fig_health.update_layout(layout_health)
        st.plotly_chart(fig_health, use_container_width=True)

    # ── Image Downloads ──────────────────────────────────────────────────────────
    dl_col1, dl_col2 = st.columns(2)
    with dl_col1:
        try:
            st.download_button(
                "📥 Download Throughput Graph (PNG)",
                data=fig_thru.to_image(format="png", width=1200, height=600, scale=2),
                file_name="throughput_graph.png",
                mime="image/png",
                key="dl_thru_png"
            )
        except Exception:
            pass
    with dl_col2:
        try:
            st.download_button(
                "📥 Download Health Graph (PNG)",
                data=fig_health.to_image(format="png", width=1200, height=600, scale=2),
                file_name="health_graph.png",
                mime="image/png",
                key="dl_health_png"
            )
        except Exception:
            pass

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

    # Create a nice list of themed cards
    for link in links:
        src, dst = link["source"] + 1, link["destination"] + 1
        thru = link.get("throughput_mbps", 0)
        loss = link.get("packet_loss", 0) * 100
        util = link.get("link_utilization", 0) * 100
        
        status_color = te.COLORS["accent_3"] # Healthy
        if loss > 5 or util > 80: status_color = te.COLORS["warning"] # Warning
        if loss > 15: status_color = te.COLORS["danger"] # Critical

        st.markdown(f"""
        <div style="background: rgba(13, 27, 46, 0.4); padding: 0.8rem; border-radius: 10px; margin-bottom: 0.5rem; border-left: 3px solid {status_color}; border-top: 1px solid rgba(0, 212, 255, 0.05); border-right: 1px solid rgba(0, 212, 255, 0.05); border-bottom: 1px solid rgba(0, 212, 255, 0.05);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 600; font-family: var(--font-display); color: var(--text-primary);">Link {src} → {dst}</span>
                <span style="color: {status_color}; font-family: var(--font-display); font-size: 0.8rem; font-weight: 700;">{thru:.2f} Mbps</span>
            </div>
            <div style="display: flex; gap: 1rem; margin-top: 0.4rem; font-size: 0.75rem; color: var(--text-muted);">
                <span>Loss: <strong style="color: var(--text-primary);">{loss:.1f}%</strong></span>
                <span>Util: <strong style="color: var(--text-primary);">{util:.1f}%</strong></span>
                <span>Delay: <strong style="color: var(--text-primary);">{link.get('delay_ms', 0):.1f}ms</strong></span>
            </div>
        </div>
        """, unsafe_allow_html=True)


