"""
CloudRouteAI — Enhanced Playback Movement Simulation
=====================================================
A high-fidelity visualization component supporting:
1. Slower, smoother packet animations.
2. Gradual congestion buildup.
3. Live timestamps and counters.
4. Interpolated path transitions.
"""

import streamlit as st
import streamlit.components.v1 as components
import json
import os

def draw_enhanced_movement_sim(current_time, routing_data, ml_data, runtime_data, playback_speed=1.0, height=700, is_playing=False):
    """Embeds an enhanced React-based movement simulation with playback features."""
    
    # Nodes and Links (3-DC Topology)
    nodes = [
        {"id": 0, "x": 100, "y": 150, "label": "SRV-A1", "dc": "DC-1 (Origin)"},
        {"id": 1, "x": 100, "y": 250, "label": "SRV-A2", "dc": "DC-1 (Origin)"},
        {"id": 2, "x": 300, "y": 200, "label": "CORE-1"},
        {"id": 3, "x": 500, "y": 200, "label": "CORE-2"},
        {"id": 4, "x": 700, "y": 200, "label": "CORE-3"},
        {"id": 5, "x": 900, "y": 150, "label": "DB-B1", "dc": "DC-3 (Cloud)"},
        {"id": 6, "x": 900, "y": 250, "label": "DB-B2", "dc": "DC-3 (Cloud)"},
        {"id": 7, "x": 1000, "y": 200, "label": "APP-X", "dc": "DC-3 (Cloud)"},
        {"id": 8, "x": 400, "y": 350, "label": "TX-1", "dc": "DC-2 (Transit)"},
        {"id": 9, "x": 600, "y": 350, "label": "TX-2", "dc": "DC-2 (Transit)"},
        {"id": 10, "x": 500, "y": 50, "label": "EXT-MON"},
    ]
    
    links = [
        (0,1), (1,2), (2,3), (3,4), (4,5), (5,6), (6,7),
        (2,8), (8,9), (9,4), (10,3)
    ]
    
    # Get active path and metrics for CURRENT state
    active_path = [0, 1, 2, 3, 4, 5, 6, 7]
    failed_links = []
    congested_links = []
    throughput = 0.0
    
    if routing_data and "decisions" in routing_data:
        latest = [d for d in routing_data["decisions"] if d["timestamp"] <= current_time]
        if latest: active_path = latest[-1].get("current_path", active_path)
            
    if ml_data:
        snap = next((s for s in ml_data.get("snapshots", []) if s["timestamp"] == current_time), None)
        if snap:
            for link in snap.get("links", []):
                if link["routing_cost"] >= 9999: failed_links.append([link["source"], link["destination"]])
                elif link["routing_cost"] > 100: congested_links.append([link["source"], link["destination"]])

    if runtime_data:
        snap = next((s for s in runtime_data.get("snapshots", []) if s["timestamp"] == current_time), None)
        if snap:
            throughput = sum(l.get("throughput_mbps", 0) for l in snap.get("links", []))

    sim_data = {
        "nodes": nodes,
        "links": [{"source": l[0], "target": l[1]} for l in links],
        "activePath": active_path,
        "failedLinks": failed_links,
        "congestedLinks": congested_links,
        "currentTime": current_time,
        "playbackSpeed": playback_speed,
        "throughput": throughput,
        "isPlaying": is_playing,
    }

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                margin: 0; padding: 0; background-color: #050d1a;
                font-family: 'DM Sans', sans-serif;
                overflow: hidden;
            }}
            .container {{
                width: 100%; height: 700px; position: relative;
                border-radius: 16px; border: 1px solid rgba(0, 212, 255, 0.08);
                box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
                box-sizing: border-box;
                background: linear-gradient(135deg, rgba(13, 27, 46, 0.5) 0%, rgba(5, 13, 26, 0.8) 100%);
            }}
            .header {{
                position: absolute; top: 24px; left: 24px; z-index: 10;
                display: flex; flex-direction: column; gap: 8px;
            }}
            .title-row {{
                display: flex; align-items: center; gap: 8px;
            }}
            .pulse-dot {{
                width: 12px; height: 12px; background-color: #00d4ff;
                border-radius: 50%; box-shadow: 0 0 12px #00d4ff;
                animation: pulse 2s infinite;
            }}
            @keyframes pulse {{
                0% {{ opacity: 1; }} 50% {{ opacity: 0.4; }} 100% {{ opacity: 1; }}
            }}
            .title-text {{
                color: #00d4ff; font-weight: bold; font-size: 14px;
                text-transform: uppercase; letter-spacing: 1px; margin: 0;
                font-family: 'Exo 2', sans-serif;
            }}
            .stats-row {{ display: flex; gap: 16px; margin-top: 8px; }}
            .stat-box {{
                background: rgba(13, 27, 46, 0.6); border: 1px solid rgba(0, 212, 255, 0.08);
                padding: 4px 8px; border-radius: 4px; font-size: 10px; color: #fff;
                font-family: 'Exo 2', sans-serif;
            }}
            .stat-box span.val {{ font-weight: bold; margin-left: 4px; }}
            .val-blue {{ color: #00d4ff; }}
            .val-red {{ color: #ef4444; }}
            .val-green {{ color: #00ff88; }}
            
            .speed-box {{
                position: absolute; top: 24px; right: 24px; z-index: 10;
                background: rgba(0, 212, 255, 0.1); border: 1px solid rgba(0, 212, 255, 0.3);
                padding: 4px 12px; border-radius: 99px; font-size: 10px;
                color: #00d4ff; font-weight: bold; font-family: 'Exo 2', sans-serif;
            }}

            .footer {{
                position: absolute; bottom: 24px; left: 24px; right: 24px;
                background: rgba(13, 27, 46, 0.85); backdrop-filter: blur(10px);
                padding: 12px; border-radius: 12px; border: 1px solid rgba(0, 212, 255, 0.08);
                display: flex; align-items: center; gap: 16px;
            }}
            .timeline-container {{ flex: 1; }}
            .timeline-header {{
                display: flex; justify-content: space-between; margin-bottom: 4px;
                font-size: 10px; font-weight: bold;
            }}
            .tl-title {{ color: rgba(255,255,255,0.4); text-transform: uppercase; letter-spacing: 1px; font-family: 'Exo 2', sans-serif; }}
            .tl-val {{ color: #00d4ff; font-family: monospace; }}
            .progress-bar-bg {{
                width: 100%; height: 4px; background: rgba(255,255,255,0.05);
                border-radius: 99px; overflow: hidden;
            }}
            .progress-bar-fill {{
                height: 100%; background: #00d4ff; box-shadow: 0 0 8px #00d4ff;
                transition: width 1s linear;
            }}

            /* SVG Styling */
            svg {{ width: 100%; height: 100%; }}
            .dc-label {{ font-size: 10px; font-weight: bold; opacity: 0.8; font-family: 'Exo 2', sans-serif; }}
            .node-circle {{ stroke-width: 2px; transition: all 0.3s; cursor: pointer; }}
            .node-circle:hover {{ transform: scale(1.15); transform-origin: center; }}
            .node-label {{ font-size: 9px; fill: #64748b; font-weight: bold; pointer-events: none; font-family: 'Exo 2', sans-serif; }}
            
            .packet {{
                fill: #00d4ff; filter: drop-shadow(0 0 8px #00d4ff);
            }}
            .packet.failed {{ fill: #ef4444; filter: drop-shadow(0 0 8px #ef4444); }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="title-row">
                    <div class="pulse-dot"></div>
                    <p class="title-text">Network Ops: Pure HTML Engine</p>
                </div>
                <div class="stats-row">
                    <div class="stat-box">THROUGHPUT<span class="val val-blue" id="ui-thru">0.00 Mbps</span></div>
                    <div class="stat-box">STATUS<span class="val" id="ui-status">OPTIMAL</span></div>
                </div>
            </div>
            
            <div class="speed-box" id="ui-speed">1.0x SPEED</div>
            
            <svg viewBox="0 0 1100 450" id="network-svg">
                <!-- DC Boundaries -->
                <rect x="50" y="80" width="150" height="240" rx="15" fill="rgba(0,212,255,0.02)" stroke="rgba(0,212,255,0.08)" stroke-dasharray="5,5" />
                <text x="125" y="70" text-anchor="middle" fill="#00d4ff" class="dc-label">DC-1 (ORIGIN)</text>

                <rect x="350" y="300" width="300" height="100" rx="15" fill="rgba(124,58,237,0.02)" stroke="rgba(124,58,237,0.08)" stroke-dasharray="5,5" />
                <text x="500" y="420" text-anchor="middle" fill="#7c3aed" class="dc-label">DC-2 (TRANSIT/BACKUP)</text>

                <rect x="850" y="80" width="200" height="240" rx="15" fill="rgba(0,255,136,0.02)" stroke="rgba(0,255,136,0.08)" stroke-dasharray="5,5" />
                <text x="950" y="70" text-anchor="middle" fill="#00ff88" class="dc-label">DC-3 (DESTINATION)</text>

                <g id="links-layer"></g>
                <g id="active-path-layer"></g>
                <g id="packets-layer"></g>
                <g id="nodes-layer"></g>
            </svg>

            <div class="footer">
                <div class="timeline-container">
                    <div class="timeline-header">
                        <span class="tl-title">Simulated Timeline</span>
                        <span class="tl-val" id="ui-time">0.0 / 20.0s</span>
                    </div>
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill" id="ui-progress" style="width: 0%;"></div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            // Inject Python Data
            const data = {json.dumps(sim_data)};
            
            // UI Updates
            document.getElementById('ui-thru').textContent = data.throughput.toFixed(2) + ' Mbps';
            const statusEl = document.getElementById('ui-status');
            if (data.failedLinks.length > 0) {{
                statusEl.textContent = 'DEGRADED';
                statusEl.className = 'val val-red';
            }} else {{
                statusEl.textContent = 'OPTIMAL';
                statusEl.className = 'val val-green';
            }}
            document.getElementById('ui-speed').textContent = data.playbackSpeed.toFixed(1) + 'x SPEED';
            document.getElementById('ui-time').textContent = data.currentTime.toFixed(1) + ' / 20.0s';
            document.getElementById('ui-progress').style.width = ((data.currentTime / 20) * 100) + '%';

            // Draw Network
            const svgNS = "http://www.w3.org/2000/svg";
            
            // 1. Draw Links
            const linksLayer = document.getElementById('links-layer');
            data.links.forEach((link, i) => {{
                const s = data.nodes.find(n => n.id === link.source);
                const t = data.nodes.find(n => n.id === link.target);
                if(!s || !t) return;
                
                const isFailed = data.failedLinks.some(fl => fl[0] === link.source && fl[1] === link.target);
                const isCongested = data.congestedLinks.some(cl => cl[0] === link.source && cl[1] === link.target);
                
                const line = document.createElementNS(svgNS, 'line');
                line.setAttribute('x1', s.x); line.setAttribute('y1', s.y);
                line.setAttribute('x2', t.x); line.setAttribute('y2', t.y);
                
                if (isFailed) {{
                    line.setAttribute('stroke', '#ef4444');
                    line.setAttribute('stroke-width', '4');
                    line.setAttribute('stroke-dasharray', '8,4');
                }} else if (isCongested) {{
                    line.setAttribute('stroke', '#f59e0b');
                    line.setAttribute('stroke-width', '3');
                }} else {{
                    line.setAttribute('stroke', 'rgba(0, 212, 255, 0.1)');
                    line.setAttribute('stroke-width', '2');
                }}
                linksLayer.appendChild(line);
            }});

            // 2. Active Path
            const activePathLayer = document.getElementById('active-path-layer');
            const activeCoords = data.activePath.map(id => data.nodes.find(n => n.id === id)).filter(Boolean);
            let pathString = "";
            
            if (activeCoords.length > 1) {{
                pathString = "M " + activeCoords.map(p => p.x + " " + p.y).join(" L ");
                
                const pathLine = document.createElementNS(svgNS, 'polyline');
                pathLine.setAttribute('points', activeCoords.map(p => p.x + "," + p.y).join(" "));
                pathLine.setAttribute('fill', 'none');
                pathLine.setAttribute('stroke', '#00d4ff');
                pathLine.setAttribute('stroke-width', '6');
                pathLine.setAttribute('stroke-opacity', '0.2');
                activePathLayer.appendChild(pathLine);
            }}

            // 3. Draw Nodes
            const nodesLayer = document.getElementById('nodes-layer');
            data.nodes.forEach(node => {{
                const g = document.createElementNS(svgNS, 'g');
                
                const circle = document.createElementNS(svgNS, 'circle');
                circle.setAttribute('cx', node.x);
                circle.setAttribute('cy', node.y);
                circle.setAttribute('r', '15');
                
                // Color nodes based on roles
                let nodeColor = "#132238";
                let nodeStroke = "#00d4ff";
                if (node.id === 0 || node.id === 1) {{
                    nodeColor = "#00d4ff";
                    nodeStroke = "#38bdf8";
                }} else if (node.id >= 5 && node.id <= 7) {{
                    nodeColor = "#00ff88";
                    nodeStroke = "#34d399";
                }} else if (node.id === 8 || node.id === 9) {{
                    nodeColor = "#7c3aed";
                    nodeStroke = "#a78bfa";
                }} else if (node.id === 10) {{
                    nodeColor = "#f59e0b";
                    nodeStroke = "#fb923c";
                }}
                
                circle.setAttribute('fill', nodeColor);
                circle.setAttribute('stroke', nodeStroke);
                circle.setAttribute('stroke-width', '2');
                circle.setAttribute('class', 'node-circle');
                
                const text = document.createElementNS(svgNS, 'text');
                text.setAttribute('x', node.x);
                text.setAttribute('y', node.y);
                text.setAttribute('text-anchor', 'middle');
                text.setAttribute('dy', '.3em');
                text.setAttribute('class', 'node-label');
                text.textContent = node.label;
                
                g.appendChild(circle);
                g.appendChild(text);
                nodesLayer.appendChild(g);
            }});

            // 4. Particle Animation Engine (Vanilla JS)
            const packetsLayer = document.getElementById('packets-layer');
            if (pathString) {{
                // Create an invisible SVG path element to use getPointAtLength()
                const invisPath = document.createElementNS(svgNS, 'path');
                invisPath.setAttribute('d', pathString);
                const pathLength = invisPath.getTotalLength();
                
                const duration = 5000 / data.playbackSpeed; // ms to travel full path
                const spawnInterval = 600 / data.playbackSpeed; // ms between spawns
                
                const packets = [];
                let lastSpawnTime = 0;
                
                function animate(time) {{
                    if (!data.isPlaying) {{
                        lastSpawnTime = time; // Prevent bursting when unpaused
                        requestAnimationFrame(animate);
                        return;
                    }}
                    
                    // Spawn new packet
                    if (time - lastSpawnTime > spawnInterval) {{
                        const circle = document.createElementNS(svgNS, 'circle');
                        circle.setAttribute('r', '4');
                        circle.setAttribute('class', data.failedLinks.length > 0 ? 'packet failed' : 'packet');
                        packetsLayer.appendChild(circle);
                        
                        packets.push({{
                            element: circle,
                            startTime: time
                        }});
                        lastSpawnTime = time;
                    }}
                    
                    // Update existing packets
                    for (let i = packets.length - 1; i >= 0; i--) {{
                        const p = packets[i];
                        const elapsed = time - p.startTime;
                        const progress = elapsed / duration;
                        
                        if (progress >= 1) {{
                            packetsLayer.removeChild(p.element);
                            packets.splice(i, 1);
                        }} else {{
                            const point = invisPath.getPointAtLength(progress * pathLength);
                            p.element.setAttribute('cx', point.x);
                            p.element.setAttribute('cy', point.y);
                        }}
                    }}
                    
                    requestAnimationFrame(animate);
                }}
                
                requestAnimationFrame(animate);
            }}
        </script>
    </body>
    </html>
    """

    
    components.html(html_template, height=height)
