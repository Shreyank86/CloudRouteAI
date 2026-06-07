import streamlit as st
import plotly.graph_objects as go
from dash_utils import load_processed_metrics
from live_engine import load_live_log
import theme_engine as te

def draw_comparison():
    """Compare Base vs Adaptive Routing performance metrics with premium visuals."""
    st.markdown("### ⚖️ Performance Benchmark (Base vs Adaptive)")
    
    metrics_data = load_processed_metrics()
    
    if not metrics_data or "runs" not in metrics_data or len(metrics_data["runs"]) < 2:
        st.info("Performance delta data not yet available. Run the simulation to generate comparison.")
        return
        
    base_data = metrics_data["runs"][0]
    adaptive_data = metrics_data["runs"][-1]
    
    def get_flow_metrics(data):
        if not data or "flows" not in data or not data["flows"]:
            return None
        # Return flow 1 (primary)
        for f in data["flows"]:
            if f["flow_id"] == 1:
                return f
        return data["flows"][0]
        
    base_flow = get_flow_metrics(base_data)
    curr_flow = get_flow_metrics(adaptive_data)
    
    if not base_flow or not curr_flow:
        st.info("Flow-level metrics not found.")
        return
        
    metrics = ["Latency (ms)", "Loss (%)", "Throughput (Mbps)"]
    base_vals = [
        base_flow.get("latency_ms", 0), 
        base_flow.get("packet_loss_rate", 0) * 100, 
        base_flow.get("throughput_mbps", 0)
    ]
    curr_vals = [
        curr_flow.get("latency_ms", 0), 
        curr_flow.get("packet_loss_rate", 0) * 100, 
        curr_flow.get("throughput_mbps", 0)
    ]
    
    # Calculate improvements
    improvements = []
    for b, a, m in zip(base_vals, curr_vals, metrics):
        if b == 0: imp = 0
        else:
            if "Throughput" in m:
                imp = (a - b) / b * 100
            else:
                imp = (b - a) / b * 100
        improvements.append(imp)

    # Display improvement cards
    cols = st.columns(3)
    for i, (m, imp) in enumerate(zip(metrics, improvements)):
        color = te.COLORS["accent_3"] if imp >= 0 else te.COLORS["danger"]
        arrow = "▲" if imp >= 0 else "▼"
        icon = "📈" if imp >= 0 else "📉"
        with cols[i]:
            te.metric_card(
                title=f"{m} Delta",
                value=f"{arrow} {abs(imp):.1f}%",
                icon=icon,
                color=color,
                idx=i
            )

    st.markdown("<br>", unsafe_allow_html=True)

    fig = go.Figure(data=[
        go.Bar(name='Static (Base)', x=metrics, y=base_vals, marker_color=te.CHART_COLORS["muted"], opacity=0.8),
        go.Bar(name='Adaptive (AI)', x=metrics, y=curr_vals, marker_color=te.CHART_COLORS["primary"])
    ])
    
    layout = te.chart_theme()
    layout.update(
        barmode='group', height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_layout(layout)
    st.plotly_chart(fig, use_container_width=True)


def draw_live_telemetry_chart():
    """Render persistent live session telemetry trends from the JSONL log file."""
    st.markdown("---")
    st.markdown("### 🔴 Live Session Telemetry Trends")
    st.markdown(
        "<p style='color:var(--text-muted); font-size:0.85rem; margin-top:-0.5rem;'>"
        "Real-time data recorded from every Live Simulator step. Persists across page refreshes. "
        "Use the <b>🗑️ Clear Telemetry Log</b> button in the True LIVE Simulator tab to reset."
        "</p>",
        unsafe_allow_html=True,
    )

    records = load_live_log()

    if not records:
        st.info(
            "💡 No live telemetry recorded yet. "
            "Start the **⚡ True LIVE Simulator** tab, inject traffic, and press ▶️ Start."
        )
        return

    import pandas as pd

    df = pd.DataFrame(records)
    df = df.sort_values("timestamp").reset_index(drop=True)

    # ── Summary KPI Row ───────────────────────────────────────────────────────
    total_steps = len(df)
    peak_loss = df["avg_packet_loss_pct"].max()
    peak_thr = df["total_throughput_mbps"].max()
    peak_cong = df["peak_congestion_pct"].max()
    last_t = df["timestamp"].iloc[-1]

    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        te.metric_card("Steps Recorded", str(total_steps), icon="📊", color=te.COLORS["accent_1"], idx=10)
    with kpi_cols[1]:
        te.metric_card("Peak Loss", f"{peak_loss:.2f}%", icon="📉", color=te.COLORS["danger"], idx=11)
    with kpi_cols[2]:
        te.metric_card("Peak Throughput", f"{peak_thr:.1f} Mbps", icon="⚡", color=te.COLORS["success"], idx=12)
    with kpi_cols[3]:
        te.metric_card("Last Sim Time", f"{last_t:.0f} s", icon="⏱️", color=te.COLORS["accent_2"], idx=13)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Time-Series Chart ─────────────────────────────────────────────────────
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df["avg_packet_loss_pct"],
        name="Avg Packet Loss (%)",
        mode="lines+markers",
        line=dict(color=te.CHART_COLORS.get("danger", "#ef4444"), width=2),
        marker=dict(size=5),
        yaxis="y1",
    ))

    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df["avg_utilization_pct"],
        name="Network Load (%)",
        mode="lines+markers",
        line=dict(color=te.CHART_COLORS.get("primary", "#3b82f6"), width=2),
        marker=dict(size=5),
        yaxis="y1",
    ))

    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df["peak_congestion_pct"],
        name="Peak Congestion (%)",
        mode="lines+markers",
        line=dict(color=te.CHART_COLORS.get("warning", "#f59e0b"), width=2, dash="dot"),
        marker=dict(size=5),
        yaxis="y1",
    ))

    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df["total_throughput_mbps"],
        name="Total Throughput (Mbps)",
        mode="lines+markers",
        line=dict(color=te.CHART_COLORS.get("accent", "#00ff88"), width=2),
        marker=dict(size=5),
        yaxis="y2",
    ))

    layout = te.chart_theme()
    layout.update(
        height=440,
        xaxis=dict(title="Simulation Time (s)"),
        yaxis=dict(title="Percentage (%)", side="left", rangemode="tozero"),
        yaxis2=dict(
            title="Throughput (Mbps)",
            overlaying="y",
            side="right",
            showgrid=False,
            rangemode="tozero",
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_layout(layout)
    st.plotly_chart(fig, use_container_width=True)

    # ── Raw log download ──────────────────────────────────────────────────────
    import json
    raw_json = json.dumps(records, indent=2)
    st.download_button(
        label="📥 Download Live Telemetry Log (JSON)",
        data=raw_json,
        file_name="live_telemetry_log.json",
        mime="application/json",
        key="dl_live_log",
    )
