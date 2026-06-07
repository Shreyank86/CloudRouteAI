"""
CloudRouteAI — Interactive Topology Lab
========================================
Vis.js-powered interactive network topology embedded in Streamlit.
Provides React Flow-like drag, zoom, and click interactions.
"""

import streamlit as st
import streamlit.components.v1 as components
from dash_utils import PRIMARY_LINKS, ALT_LINKS, ALL_LINKS, get_all_costs_at_timestamp, to_display


def draw_topology_lab(timestamp, routing_data, ml_data, runtime_data):
    """Render an interactive vis.js network topology lab."""

    # Extract state at timestamp
    costs = get_all_costs_at_timestamp(ml_data, timestamp)

    # Find active path
    active_path_0_idx = [0, 1, 2, 3, 4, 5, 6, 7]
    if routing_data and "decisions" in routing_data:
        for dec in routing_data["decisions"]:
            if dec["timestamp"] <= timestamp:
                active_path_0_idx = dec.get("current_path", active_path_0_idx)
                if dec.get("rerouted") and dec["timestamp"] == timestamp:
                    active_path_0_idx = dec.get("dijkstra_best_path", active_path_0_idx)

    active_path = to_display(active_path_0_idx)
    active_edges = set()
    for i in range(len(active_path) - 1):
        active_edges.add((min(active_path[i], active_path[i+1]), max(active_path[i], active_path[i+1])))

    # Classify scenario
    classified = "normal"
    if ml_data:
        classified = ml_data.get("classified_scenario", "normal")

    # Get link metrics for tooltips
    link_metrics = {}
    if runtime_data and "snapshots" in runtime_data:
        snap = next((s for s in runtime_data["snapshots"] if s["timestamp"] == timestamp),
                     runtime_data["snapshots"][-1] if runtime_data["snapshots"] else None)
        if snap:
            for lk in snap.get("links", []):
                link_metrics[(lk["source"]+1, lk["destination"]+1)] = lk

    # Build node data
    node_labels = {
        1: "SOURCE",
        2: "ROUTER_02",
        3: "JUNCTION",
        4: "PRIMARY_04",
        5: "ROUTER_05",
        6: "ROUTER_06",
        7: "ROUTER_07",
        8: "DESTINATION",
        9: "ALT_ROUTE_09",
        10: "ALT_ROUTE_10",
        11: "CONG_SOURCE",
    }

    node_types = {
        1: "source",
        2: "router",
        3: "junction",
        4: "router",
        5: "router",
        6: "router",
        7: "router",
        8: "destination",
        9: "alternate",
        10: "alternate",
        11: "congestion",
    }

    # Positions (vis.js uses pixel coords)
    positions = {
        1:  {"x": -400, "y": 0},
        2:  {"x": -250, "y": 0},
        3:  {"x": -100, "y": 0},
        4:  {"x":   50, "y": 0},
        5:  {"x":  200, "y": 0},
        6:  {"x":  350, "y": 0},
        7:  {"x":  500, "y": 0},
        8:  {"x":  650, "y": 0},
        9:  {"x":  -50, "y": 200},
        10: {"x":  100, "y": 200},
        11: {"x":   50, "y": -200},
    }

    # Build JSON for vis.js
    nodes_json = []
    for nid in range(1, 12):
        ntype = node_types[nid]
        label = node_labels[nid]

        if ntype == "source":
            color = {"background": "#00d4ff", "border": "#38bdf8", "highlight": {"background": "#00d4ff", "border": "#00d4ff"}}
            icon_char = "📡"
            shape = "dot"
        elif ntype == "destination":
            color = {"background": "#00ff88", "border": "#34d399", "highlight": {"background": "#00ff88", "border": "#00ff88"}}
            icon_char = "☁️"
            shape = "dot"
        elif ntype == "junction":
            color = {"background": "#38bdf8", "border": "#22d3ee", "highlight": {"background": "#38bdf8", "border": "#38bdf8"}}
            icon_char = "🔀"
            shape = "dot"
        elif ntype == "alternate":
            color = {"background": "#7c3aed", "border": "#a78bfa", "highlight": {"background": "#7c3aed", "border": "#7c3aed"}}
            icon_char = "🔄"
            shape = "dot"
        elif ntype == "congestion":
            color = {"background": "#f59e0b", "border": "#fb923c", "highlight": {"background": "#f59e0b", "border": "#f59e0b"}}
            icon_char = "⚡"
            shape = "dot"
        else:
            color = {"background": "#132238", "border": "#00d4ff", "highlight": {"background": "#132238", "border": "#00d4ff"}}
            icon_char = "🖥️"
            shape = "dot"

        # Override for failure scenario
        if classified == "failure" and nid == 4:
            color = {"background": "#ef4444", "border": "#f87171", "highlight": {"background": "#ef4444", "border": "#ef4444"}}
            label = "FAILED_04"

        nodes_json.append({
            "id": nid,
            "label": f"N{nid}\\n{label}",
            "x": positions[nid]["x"],
            "y": positions[nid]["y"],
            "color": color,
            "shape": shape,
            "size": 28 if ntype in ["source", "destination", "junction"] else 22,
            "font": {"color": "#e2e8f0", "size": 11, "face": "Exo 2, DM Sans, sans-serif"},
            "borderWidth": 2,
            "shadow": {"enabled": True, "color": color["background"], "size": 15, "x": 0, "y": 0},
            "title": f"<b>Node {nid}</b><br>Type: {ntype.upper()}<br>{icon_char}",
        })

    edges_json = []
    for u, v in ALL_LINKS:
        c1 = costs.get((u-1, v-1), 10.0)
        c2 = costs.get((v-1, u-1), 10.0)
        cost = max(c1, c2)

        edge_key = (min(u, v), max(u, v))
        is_active = edge_key in active_edges

        # Determine edge color
        if cost > 9000:
            edge_color = "#ef4444"
            dashes = True
            width = 2
        elif cost > 100:
            edge_color = "#f59e0b"
            dashes = False
            width = 3
        else:
            edge_color = "rgba(0, 255, 136, 0.3)"
            dashes = False
            width = 1

        if is_active:
            edge_color = "#00d4ff" if cost < 9000 else "#ef4444"
            width = 5
            dashes = False

        # Tooltip with metrics
        metrics_info = link_metrics.get((u, v), {})
        thru = metrics_info.get("throughput_mbps", 0)
        loss = metrics_info.get("packet_loss", 0) * 100
        delay = metrics_info.get("delay_ms", 0)

        edges_json.append({
            "from": u,
            "to": v,
            "color": {"color": edge_color, "highlight": "#00d4ff", "opacity": 1.0 if is_active else 0.5},
            "width": width,
            "dashes": dashes,
            "smooth": {"type": "curvedCW", "roundness": 0.1} if (u, v) in [(3, 9), (10, 5)] else False,
            "title": f"<b>Link {u} → {v}</b><br>Cost: {cost:.1f}<br>Throughput: {thru:.2f} Mbps<br>Loss: {loss:.1f}%<br>Delay: {delay:.1f}ms<br>{'🟢 ACTIVE' if is_active else '⚪ IDLE'}",
            "arrows": {"to": {"enabled": True, "scaleFactor": 0.5}},
        })

    import json
    nodes_str = json.dumps(nodes_json)
    edges_str = json.dumps(edges_json)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://unpkg.com/vis-network@9.1.6/standalone/umd/vis-network.min.js"></script>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ background: transparent; overflow: hidden; font-family: 'DM Sans', sans-serif; }}
            #network-container {{
                width: 100%;
                height: 520px;
                background: rgba(5, 13, 26, 0.6);
                border: 1px solid rgba(0, 212, 255, 0.08);
                border-radius: 16px;
                position: relative;
            }}
            #controls {{
                position: absolute;
                bottom: 16px;
                left: 16px;
                display: flex;
                flex-direction: column;
                gap: 6px;
                z-index: 10;
            }}
            #controls button {{
                width: 36px;
                height: 36px;
                background: rgba(13, 27, 46, 0.9);
                border: 1px solid rgba(0, 212, 255, 0.15);
                border-radius: 8px;
                color: #64748b;
                font-size: 18px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s;
                backdrop-filter: blur(10px);
            }}
            #controls button:hover {{
                background: rgba(0, 212, 255, 0.2);
                border-color: #00d4ff;
                color: #e2e8f0;
            }}
            #legend {{
                position: absolute;
                top: 16px;
                right: 16px;
                background: rgba(13, 27, 46, 0.85);
                backdrop-filter: blur(12px);
                border: 1px solid rgba(0, 212, 255, 0.08);
                border-radius: 12px;
                padding: 14px 18px;
                z-index: 10;
                font-size: 11px;
                color: #64748b;
            }}
            .legend-item {{
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 6px;
                font-family: 'Exo 2', sans-serif;
            }}
            .legend-dot {{
                width: 10px;
                height: 10px;
                border-radius: 50%;
                flex-shrink: 0;
            }}
            #node-info {{
                position: absolute;
                bottom: 16px;
                right: 16px;
                background: rgba(13, 27, 46, 0.9);
                backdrop-filter: blur(12px);
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 12px;
                padding: 14px 18px;
                z-index: 10;
                font-size: 12px;
                color: #e2e8f0;
                display: none;
                min-width: 180px;
            }}
            #node-info h4 {{ color: #00d4ff; margin-bottom: 6px; font-size: 13px; font-family: 'Exo 2', sans-serif; }}
            #node-info .metric {{ display: flex; justify-content: space-between; margin-bottom: 3px; }}
            #node-info .metric-label {{ color: #64748b; }}
            #node-info .metric-val {{ font-weight: 600; }}
        </style>
    </head>
    <body>
        <div id="network-container">
            <div id="controls">
                <button onclick="network.moveTo({{scale: network.getScale() * 1.3}})" title="Zoom In">+</button>
                <button onclick="network.moveTo({{scale: network.getScale() / 1.3}})" title="Zoom Out">−</button>
                <button onclick="network.fit({{animation: true}})" title="Fit to Screen">⊙</button>
            </div>
            <div id="legend">
                <div class="legend-item"><div class="legend-dot" style="background:#00d4ff"></div> Source Node</div>
                <div class="legend-item"><div class="legend-dot" style="background:#00ff88"></div> Destination / Cloud</div>
                <div class="legend-item"><div class="legend-dot" style="background:#7c3aed"></div> Alternate Route</div>
                <div class="legend-item"><div class="legend-dot" style="background:#ef4444"></div> Failed / Critical</div>
                <div class="legend-item"><div class="legend-dot" style="background:#f59e0b"></div> Congestion Source</div>
                <div class="legend-item"><div class="legend-dot" style="background:#132238; border: 1px solid #00d4ff"></div> Router Node</div>
            </div>
            <div id="node-info">
                <h4 id="ni-title">Node Info</h4>
                <div class="metric"><span class="metric-label">Type</span><span class="metric-val" id="ni-type">—</span></div>
                <div class="metric"><span class="metric-label">Connections</span><span class="metric-val" id="ni-conn">—</span></div>
                <div class="metric"><span class="metric-label">Status</span><span class="metric-val" id="ni-status">—</span></div>
            </div>
        </div>

        <script>
            var nodes = new vis.DataSet({nodes_str});
            var edges = new vis.DataSet({edges_str});
            var container = document.getElementById('network-container');
            var data = {{ nodes: nodes, edges: edges }};
            var options = {{
                physics: {{ enabled: false }},
                interaction: {{
                    dragNodes: true,
                    dragView: true,
                    zoomView: true,
                    hover: true,
                    tooltipDelay: 150,
                    navigationButtons: false,
                    keyboard: false,
                }},
                nodes: {{
                    borderWidthSelected: 3,
                    chosen: true,
                }},
                edges: {{
                    chosen: true,
                    hoverWidth: 2,
                }},
            }};
            var network = new vis.Network(container, data, options);

            // Node type mapping
            var nodeTypes = {{}};
            var nodeLabels = {{}};
            {nodes_str}.forEach(function(n) {{
                nodeLabels[n.id] = n.label.split('\\n')[1] || '';
            }});

            network.on("click", function(params) {{
                var infoBox = document.getElementById('node-info');
                if (params.nodes.length > 0) {{
                    var nodeId = params.nodes[0];
                    var connEdges = network.getConnectedEdges(nodeId);
                    document.getElementById('ni-title').textContent = 'Node ' + nodeId;
                    document.getElementById('ni-type').textContent = nodeLabels[nodeId] || 'ROUTER';
                    document.getElementById('ni-conn').textContent = connEdges.length + ' links';
                    document.getElementById('ni-status').textContent = '● ONLINE';
                    document.getElementById('ni-status').style.color = '#10b981';
                    infoBox.style.display = 'block';
                }} else {{
                    infoBox.style.display = 'none';
                }}
            }});

            // Fit on load
            network.once('afterDrawing', function() {{
                network.fit({{ animation: false }});
            }});
        </script>
    </body>
    </html>
    """

    components.html(html_content, height=540, scrolling=False)
