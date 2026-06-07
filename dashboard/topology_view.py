import streamlit as st
import networkx as nx
import plotly.graph_objects as go
from dash_utils import PRIMARY_LINKS, ALT_LINKS, ALL_LINKS, to_display, get_all_costs_at_timestamp
import theme_engine as te

def draw_topology(timestamp, routing_data, ml_data):
    """Render the network topology using Plotly and NetworkX with premium aesthetics."""
    
    # 1. Build Graph
    G = nx.Graph()
    G.add_edges_from(ALL_LINKS)
    
    # Static node positions for consistent layout
    pos = {
        1: (0, 0),
        2: (1, 0),
        3: (2, 0),
        4: (3, 0),
        5: (4, 0),
        6: (5, 0),
        7: (6, 0),
        8: (7, 0),
        9: (2.5, -1),
        10: (3.5, -1),
        11: (3, 1)
    }
    
    # 2. Extract state at timestamp
    costs = get_all_costs_at_timestamp(ml_data, timestamp)
    
    # Find active path from routing data
    active_path_0_idx = [0, 1, 2, 3, 4, 5, 6, 7] # default
    if routing_data and "decisions" in routing_data:
        for dec in routing_data["decisions"]:
            if dec["timestamp"] <= timestamp:
                active_path_0_idx = dec.get("current_path", active_path_0_idx)
                if dec.get("rerouted") and dec["timestamp"] == timestamp:
                    active_path_0_idx = dec["dijkstra_best_path"]
                    
    active_path = to_display(active_path_0_idx)
    active_edges = list(zip(active_path[:-1], active_path[1:]))
    active_edges = [tuple(sorted(e)) for e in active_edges]
    
    # 3. Create Edge Traces
    edge_traces = []
    
    for edge in G.edges():
        u, v = edge
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        
        c1 = costs.get((u-1, v-1), 10.0)
        c2 = costs.get((v-1, u-1), 10.0)
        cost = max(c1, c2)
        
        color = 'rgba(0, 212, 255, 0.15)' # Default idle edge
        width = 2
        dash = 'solid'
        opacity = 0.6
        
        is_active = tuple(sorted(edge)) in active_edges
        
        if cost > 9000:
            color = te.COLORS["danger"] # Red for failure
            dash = 'dash'
            width = 3
        elif cost > 100:
            color = te.COLORS["warning"] # Orange for congestion
            width = 4
        else:
            color = 'rgba(0, 255, 136, 0.3)' # Green for healthy idle
            
        if is_active:
            color = te.COLORS["accent_1"] if cost < 9000 else te.COLORS["danger"]
            width = 8
            opacity = 1.0
            
        edge_trace = go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            line=dict(width=width, color=color, dash=dash),
            hoverinfo='text',
            mode='lines',
            opacity=opacity,
            text=f"Link {u}-{v}<br>Cost: {cost:.2f}<br>{'ACTIVE' if is_active else 'IDLE'}"
        )
        edge_traces.append(edge_trace)

    # 4. Create Node Trace
    node_x = []
    node_y = []
    node_text = []
    node_colors = []
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(f"<b>Node {node}</b>")
        
        # Color nodes based on role
        if node == 1: node_colors.append(te.COLORS["accent_1"]) # Source
        elif node == 8: node_colors.append(te.COLORS["accent_3"]) # Destination
        elif node == 11: node_colors.append(te.COLORS["warning"]) # Congestion source
        else: node_colors.append(te.COLORS["bg_elevated"]) # Router

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=[f"Node {n}" for n in G.nodes()],
        textposition="bottom center",
        textfont=dict(color=te.COLORS["text_muted"], size=10, family="var(--font-body)"),
        marker=dict(
            showscale=False,
            color=node_colors,
            size=35,
            line=dict(color='rgba(0, 212, 255, 0.6)', width=2),
            symbol='circle'
        )
    )

    # 5. Render Figure
    layout = te.chart_theme()
    layout.update(
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20,l=20,r=20,t=20),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=500,
        clickmode='event+select'
    )
    fig = go.Figure(data=edge_traces + [node_trace], layout=go.Layout(layout))
                    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # Premium Legend
    cols = st.columns(4)
    with cols[0]: st.markdown(f'<div style="display:flex; align-items:center; gap:0.5rem;"><div style="width:12px; height:12px; background:{te.COLORS["accent_1"]}; border-radius:2px; box-shadow: 0 0 6px {te.COLORS["accent_1"]};"></div><span style="font-size:0.8rem; color:var(--text-muted); font-family:var(--font-display);">Active Path</span></div>', unsafe_allow_html=True)
    with cols[1]: st.markdown(f'<div style="display:flex; align-items:center; gap:0.5rem;"><div style="width:12px; height:12px; background:{te.COLORS["accent_3"]}; border-radius:2px; box-shadow: 0 0 6px {te.COLORS["accent_3"]};"></div><span style="font-size:0.8rem; color:var(--text-muted); font-family:var(--font-display);">Healthy Link</span></div>', unsafe_allow_html=True)
    with cols[2]: st.markdown(f'<div style="display:flex; align-items:center; gap:0.5rem;"><div style="width:12px; height:12px; background:{te.COLORS["warning"]}; border-radius:2px; box-shadow: 0 0 6px {te.COLORS["warning"]};"></div><span style="font-size:0.8rem; color:var(--text-muted); font-family:var(--font-display);">Congested Link</span></div>', unsafe_allow_html=True)
    with cols[3]: st.markdown(f'<div style="display:flex; align-items:center; gap:0.5rem;"><div style="width:12px; height:12px; background:{te.COLORS["danger"]}; border-radius:2px; box-shadow: 0 0 6px {te.COLORS["danger"]};"></div><span style="font-size:0.8rem; color:var(--text-muted); font-family:var(--font-display);">Failed Link</span></div>', unsafe_allow_html=True)


