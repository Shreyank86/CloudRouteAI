import streamlit as st
import plotly.graph_objects as go
from dash_utils import load_processed_metrics

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
        color = "#10b981" if imp >= 0 else "#ef4444"
        arrow = "↑" if imp >= 0 else "↓"
        with cols[i]:
            st.markdown(f"""
            <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid {color}; padding: 1rem; border-radius: 0.5rem; text-align: center;">
                <div style="color: #94a3b8; font-size: 0.8rem; text-transform: uppercase;">{m} Delta</div>
                <div style="color: {color}; font-size: 1.5rem; font-weight: 700;">{arrow} {abs(imp):.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    fig = go.Figure(data=[
        go.Bar(name='Static (Base)', x=metrics, y=base_vals, marker_color='#1e293b', opacity=0.8),
        go.Bar(name='Adaptive (AI)', x=metrics, y=curr_vals, marker_color='#3b82f6')
    ])
    
    fig.update_layout(
        barmode='group', height=400,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8'),
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

