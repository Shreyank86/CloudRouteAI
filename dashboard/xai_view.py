"""
CloudRouteAI — Explainable AI (XAI) Dashboard View
==================================================
Renders the XAI explanation metrics, candidate path comparisons,
rejection analyses, traffic split breakdowns, and event risk alerts.
"""

import streamlit as st
import pandas as pd
from xai_module import get_offline_xai_metrics, get_live_xai_metrics


# ─────────────────────────────────────────────────────
def _progress_bar(label, value, color_gradient, explanation):
    """Premium glowing horizontal progress bar with text."""
    gradient_css = f"linear-gradient(90deg, {color_gradient[0]} 0%, {color_gradient[1]} 100%)"
    st.markdown(f"""
    <div style="background: rgba(13, 27, 46, 0.5); padding: 1.25rem; border-radius: 0.8rem;
                border: 1px solid rgba(0, 212, 255, 0.08); margin-bottom: 1rem;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);">
        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.5rem;">
            <span style="font-size: 0.9rem; color: var(--text-primary); font-weight: 600;
                         letter-spacing: 0.05em; text-transform: uppercase; font-family: var(--font-display);">{label}</span>
            <span style="font-size: 1.8rem; font-weight: 700; background: {gradient_css};
                         -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-family: var(--font-display);">{value:.1f}%</span>
        </div>
        <div style="background: rgba(5, 13, 26, 0.6); height: 8px; border-radius: 999px;
                     overflow: hidden; margin-bottom: 0.75rem;">
            <div style="background: {gradient_css}; width: {value}%; height: 100%;
                        border-radius: 999px; box-shadow: 0 0 8px {color_gradient[1]};"></div>
        </div>
        <div style="font-size: 0.85rem; color: var(--text-muted); line-height: 1.4;">
            {explanation}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────
# Main XAI Dashboard
# ──────────────────────────────────────────────────────────────────
def draw_xai_tab(sim):
    """Top-level entry point called from app.py under the XAI tab."""

    current_time = sim.time_step * 2.0
    import theme_engine as te

    te.section_header("Explainable AI (XAI) Center", "Observational layer — explains routing decisions in plain English. Does not influence the routing engine.", icon="🧠")

    st.markdown(f"""
    <div style="text-align: right; margin-top: -1rem; margin-bottom: 1.5rem;">
        <span style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; font-family: var(--font-display); font-weight: 600;">Simulation Time</span>
        <span style="color: var(--accent-1); font-size: 1.15rem; font-family: var(--font-display); font-weight: 700; margin-left: 0.5rem; background: rgba(0, 212, 255, 0.1); border: 1px solid rgba(0, 212, 255, 0.3); padding: 0.25rem 0.75rem; border-radius: 4px;">t = {current_time:.1f}s</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Flow selector ──
    st.markdown("### 📡 Active Live Traffic Flow Selector")
    flow_id = st.selectbox(
        "Select Traffic Flow to Explain",
        ["flow_1", "flow_2"],
        format_func=lambda x: f"Flow {x[-1]}  ({sim.flows.get(x, {}).get('src')} → {sim.flows.get(x, {}).get('dst')})",
        key="xai_flow_selector",
    )

    xai_data = get_live_xai_metrics(current_time, flow_id, sim)
    if not xai_data:
        st.warning("⚠️ **Awaiting Telemetry** — Start the Live Simulator and inject traffic first.")
        return

    # ── Historical time selector ──
    logs = sim.di_module.get_latest_logs(limit=100)
    flow_logs = [l for l in logs if l["flow_id"] == flow_id]
    if flow_logs:
        ts_options = sorted(set(l["timestamp"] for l in flow_logs), reverse=True)
        if len(ts_options) > 1:
            st.markdown("#### ⏱️ Decision Timeline")
            st.caption("Review past routing decisions for this flow.")
            sel_ts = st.select_slider(
                "View decision at time:",
                options=ts_options,
                value=ts_options[0],
                format_func=lambda t: f"t = {t:.0f}s",
                key="xai_time_slider",
            )
            if sel_ts != current_time:
                st.info(f"Showing cached metrics from **t = {sel_ts:.0f}s**. Live telemetry refreshes each step.")

    # ───────────────────────────────────────────────────
    # ROW 1: Active Route & Decision Summary
    # ───────────────────────────────────────────────────
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.markdown(f"""
        <div style="background: rgba(13, 27, 46, 0.5); padding: 1.5rem; border-radius: 1rem;
                    border: 1px solid rgba(0, 212, 255, 0.08); height: 100%;
                    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);">
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
                <span style="font-size: 1.2rem;">🛣️</span>
                <span style="font-size: 1.05rem; font-weight: 600; color: var(--text-primary); font-family: var(--font-display);">Selected Active Route</span>
            </div>
            <div style="background: rgba(5, 13, 26, 0.6); padding: 1rem; border-radius: 0.6rem;
                        border: 1px solid rgba(0, 212, 255, 0.3); font-family: var(--font-mono);
                        font-size: 1.15rem; font-weight: 700; color: var(--accent-1);
                        text-align: center; letter-spacing: 0.05em; margin-bottom: 1rem;
                        box-shadow: 0 0 15px rgba(0, 212, 255, 0.15);">
                {xai_data['selected_display_path']}
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
                <div style="background: rgba(5, 13, 26, 0.4); padding: 0.75rem; border-radius: 0.5rem;
                            text-align: center; border: 1px solid rgba(0, 212, 255, 0.05);">
                    <div style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; font-family: var(--font-display);">Confidence</div>
                    <div style="color: var(--accent-2); font-size: 1.25rem; font-weight: 700; font-family: var(--font-display);">{xai_data['confidence']:.0f}%</div>
                </div>
                <div style="background: rgba(5, 13, 26, 0.4); padding: 0.75rem; border-radius: 0.5rem;
                            text-align: center; border: 1px solid rgba(0, 212, 255, 0.05);">
                    <div style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; font-family: var(--font-display);">Sustainability</div>
                    <div style="color: var(--accent-3); font-size: 1.25rem; font-weight: 700; font-family: var(--font-display);">{xai_data['sustainability']:.0f}%</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="background: rgba(13, 27, 46, 0.5); padding: 1.5rem; border-radius: 1rem;
                    border: 1px solid rgba(0, 212, 255, 0.08); border-left: 5px solid var(--accent-3);
                    height: 100%; box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);">
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
                <span style="font-size: 1.2rem;">🎯</span>
                <span style="font-size: 1.05rem; font-weight: 600; color: var(--accent-3); font-family: var(--font-display);">Selection Summary Rationale</span>
            </div>
            <p style="font-size: 0.95rem; color: var(--text-primary); line-height: 1.6; margin: 0;">
                {xai_data['selection_reason']}
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ───────────────────────────────────────────────────
    # ROW 2: Confidence & Sustainability Meters
    # ───────────────────────────────────────────────────
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        _progress_bar("Decision Confidence Score", xai_data["confidence"],
                       ["#00d4ff", "#7c3aed"], xai_data["confidence_expl"])
    with m_col2:
        _progress_bar("Route Sustainability Index", xai_data["sustainability"],
                       ["#00ff88", "#00d4ff"], xai_data["sustainability_expl"])

    # ───────────────────────────────────────────────────
    # ROW 3: Traffic Split Explanation (NEW!)
    # ───────────────────────────────────────────────────
    if xai_data.get("traffic_split_explanation"):
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🔀 Traffic Split Breakdown")
        st.markdown(
            "<p style='color:var(--text-muted); font-size:0.8rem; margin-top:-0.5rem;'>"
            "Detailed view of how traffic is distributed across data centres and paths.</p>",
            unsafe_allow_html=True,
        )
        st.markdown(f"""
        <div style="background: rgba(13, 27, 46, 0.5); padding: 1.5rem; border-radius: 1rem;
                    border: 1px solid rgba(0, 212, 255, 0.08); border-left: 5px solid var(--warning);
                    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);">
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
                <span style="font-size: 1.2rem;">📊</span>
                <span style="font-size: 1.05rem; font-weight: 600; color: var(--warning); font-family: var(--font-display);">Multi-Path Distribution</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(xai_data["traffic_split_explanation"])

    # ───────────────────────────────────────────────────
    # ROW 4: Metric Contributions & Rejection Analysis
    # ───────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    c_col1, c_col2 = st.columns([1.1, 0.9])

    with c_col1:
        st.markdown("### 📊 Metric Contributions to Final Decision")
        st.markdown(
            "<p style='color:var(--text-muted); font-size:0.8rem; margin-top:-0.5rem;'>"
            "Decomposition of the routing cost parameters driving this selection.</p>",
            unsafe_allow_html=True,
        )

        for metric, pct in xai_data["contributions"].items():
            bar_color = "var(--accent-1)"
            if metric == "Congestion":
                bar_color = "var(--warning)"
            elif metric == "Future Risk":
                bar_color = "var(--danger)"
            elif metric == "Routing Cost":
                bar_color = "var(--accent-2)"

            st.markdown(f"""
            <div style="margin-bottom: 0.8rem;">
                <div style="display:flex; justify-content:space-between; font-size:0.85rem;
                            color:var(--text-primary); margin-bottom:0.25rem; font-family: var(--font-display);">
                    <span style="font-weight:600;">{metric}</span>
                    <span>{pct:.1f}%</span>
                </div>
                <div style="background: rgba(5, 13, 26, 0.6); height: 6px; border-radius: 999px; overflow: hidden;">
                    <div style="background: {bar_color}; width: {pct}%; height: 100%; border-radius: 999px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with c_col2:
        st.markdown(f"""
        <div style="background: rgba(13, 27, 46, 0.5); padding: 1.5rem; border-radius: 1rem;
                    border: 1px solid rgba(0, 212, 255, 0.08); border-left: 5px solid var(--danger);
                    height: 100%; box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);">
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
                <span style="font-size: 1.2rem;">🚫</span>
                <span style="font-size: 1.05rem; font-weight: 600; color: var(--danger); font-family: var(--font-display);">Rejected Path Rationale</span>
            </div>
            <p style="font-size: 0.95rem; color: var(--text-primary); line-height: 1.6; margin: 0;">
                {xai_data['rejected_reason']}
            </p>
        </div>
        """, unsafe_allow_html=True)

    # ───────────────────────────────────────────────────
    # ROW 5: Candidate Route Comparison Table
    # ───────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📋 Candidate Route Comparison")
    st.markdown(
        "<p style='color:var(--text-muted); font-size:0.8rem; margin-top:-0.5rem;'>"
        "Evaluations for all physical path candidates considered by the routing core.</p>",
        unsafe_allow_html=True,
    )

    table_rows = []
    for c in xai_data["candidates"]:
        is_sel = c["path"] == xai_data["selected_path"]
        bg_style = ("background: rgba(0, 212, 255, 0.05); border: 1px solid rgba(0, 212, 255, 0.15);"
                     if is_sel else "background: rgba(5, 13, 26, 0.2);")
        status_color = "var(--accent-3)" if is_sel else "var(--text-muted)"
        status_weight = "bold" if is_sel else "normal"
        sel_label = "✅ Selected" if is_sel else "❌ Bypassed"

        table_rows.append(f"""<tr style="{bg_style} border-bottom: 1px solid rgba(0,212,255,0.05);">
<td style="padding: 0.75rem 1rem; color: {status_color}; font-weight: {status_weight}; font-family: var(--font-display);">{sel_label}</td>
<td style="padding: 0.75rem 1rem; font-weight: 600; color: var(--text-primary); font-family: var(--font-display);">{c['name']}</td>
<td style="padding: 0.75rem 1rem; font-family: var(--font-mono); font-size: 0.85rem; color: var(--text-muted);">{c['display_path']}</td>
<td style="padding: 0.75rem 1rem; text-align: center; color: var(--text-primary);">{c['latency']} ms</td>
<td style="padding: 0.75rem 1rem; text-align: center; color: var(--text-primary);">{c['congestion']}%</td>
<td style="padding: 0.75rem 1rem; text-align: center; color: var(--text-primary);">{c['packet_loss']}%</td>
<td style="padding: 0.75rem 1rem; text-align: center; color: var(--warning);">{c['frs']:.2f}</td>
<td style="padding: 0.75rem 1rem; text-align: center; color: var(--danger); font-weight: 600;">+{c['penalty']:.0f}</td>
<td style="padding: 0.75rem 1rem; text-align: center; font-weight: bold; color: var(--accent-1); font-family: var(--font-display);">{c['final_score']:.1f}</td>
</tr>""")

    _header_style = 'padding: 1rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; font-family: var(--font-display);'
    html_table = f"""<div style="overflow-x: auto; border-radius: 0.75rem; border: 1px solid rgba(0,212,255,0.08);
box-shadow: 0 4px 20px rgba(0,0,0,0.25); background: rgba(13, 27, 46, 0.4);">
<table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.85rem;">
<thead>
<tr style="background: rgba(5, 13, 26, 0.85); border-bottom: 1px solid rgba(0, 212, 255, 0.15);">
<th style="{_header_style}">Selection</th>
<th style="{_header_style}">Route Name</th>
<th style="{_header_style}">Topology Path</th>
<th style="{_header_style} text-align: center;">Latency</th>
<th style="{_header_style} text-align: center;">Congestion</th>
<th style="{_header_style} text-align: center;">Loss</th>
<th style="{_header_style} text-align: center;">Future Risk</th>
<th style="{_header_style} text-align: center;">Penalty</th>
<th style="{_header_style} text-align: center;">Final Score</th>
</tr>
</thead>
<tbody>
{"".join(table_rows)}
</tbody>
</table>
</div>"""
    st.markdown(html_table, unsafe_allow_html=True)

    # ───────────────────────────────────────────────────
    # ROW 6: Future Event Impact Analysis
    # ───────────────────────────────────────────────────
    st.markdown("<br>### 📅 Context-Aware Event Impact", unsafe_allow_html=True)
    event = xai_data["event"]

    if event:
        severity_label = "Low"
        severity_color = "var(--accent-1)"
        if event["severity"] >= 0.8:
            severity_label = "Critical"
            severity_color = "var(--danger)"
        elif event["severity"] >= 0.5:
            severity_label = "Moderate"
            severity_color = "var(--warning)"

        status_label = "ACTIVE" if xai_data["event_active"] else "UPCOMING"
        status_color = "var(--danger)" if status_label == "ACTIVE" else "var(--warning)"

        st.markdown(f"""
        <div style="background: rgba(13, 27, 46, 0.5); padding: 1.5rem; border-radius: 1rem;
                    border: 1px solid rgba(0, 212, 255, 0.08); border-left: 5px solid {status_color};
                    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.25rem;">🚨</span>
                    <span style="font-weight: 700; color: var(--text-primary); font-size: 1.1rem; font-family: var(--font-display);">{event['type']} event detected</span>
                </div>
                <span style="background: rgba(239, 68, 68, 0.15); color: {status_color}; font-weight: bold;
                             font-size: 0.75rem; padding: 0.25rem 0.75rem; border-radius: 999px;
                             border: 1px solid {status_color}; letter-spacing: 0.05em; font-family: var(--font-display);">{status_label}</span>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
                <div style="background: rgba(5, 13, 26, 0.4); padding: 0.75rem; border-radius: 0.5rem;
                            border: 1px solid rgba(0, 212, 255, 0.05);">
                    <div style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; font-family: var(--font-display);">Severity</div>
                    <div style="color: {severity_color}; font-size: 1.1rem; font-weight: 700; font-family: var(--font-display);">{event['severity']:.2f} ({severity_label})</div>
                </div>
                <div style="background: rgba(5, 13, 26, 0.4); padding: 0.75rem; border-radius: 0.5rem;
                            border: 1px solid rgba(0, 212, 255, 0.05);">
                    <div style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; font-family: var(--font-display);">Time Info</div>
                    <div style="color: var(--text-primary); font-size: 1.1rem; font-weight: 700; font-family: var(--font-display);">
                        {'Active now' if xai_data['event_active'] else f'Starts in {xai_data["time_until_event"]:.1f}s'}
                    </div>
                </div>
                <div style="background: rgba(5, 13, 26, 0.4); padding: 0.75rem; border-radius: 0.5rem;
                            border: 1px solid rgba(0, 212, 255, 0.05);">
                    <div style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; font-family: var(--font-display);">Event Duration</div>
                    <div style="color: var(--text-primary); font-size: 1.1rem; font-weight: 700; font-family: var(--font-display);">{event['duration']:.1f} seconds</div>
                </div>
            </div>

            <p style="font-size: 0.9rem; color: var(--text-primary); line-height: 1.5; margin: 0 0 0.5rem 0;">
                <b>Description:</b> {event['description']}
            </p>
            <p style="font-size: 0.9rem; color: var(--text-muted); line-height: 1.5; margin: 0;">
                <b>XAI Risk Analysis:</b> The upcoming incident drives the Future Risk Score (FRS) of primary links to
                <b>{xai_data['frs']:.2f}</b>, injecting a cost penalty of <b>+{xai_data['penalty']:.0f}</b>.
                This forces the decision logic to switch routing priority in favor of alternate routes before queue buffer overflow occurs.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: rgba(0, 255, 136, 0.05); padding: 1.25rem; border-radius: 1rem;
                    border: 1px solid rgba(0, 255, 136, 0.2); display: flex; align-items: center;
                    gap: 0.75rem; box-shadow: 0 4px 20px rgba(0,0,0,0.15);">
            <span style="font-size: 1.5rem;">✅</span>
            <div>
                <div style="font-weight: 700; color: var(--accent-3); font-size: 0.95rem; font-family: var(--font-display);">Stable Network State</div>
                <div style="color: var(--text-muted); font-size: 0.85rem; margin-top: 0.1rem;">
                    No upcoming future risks or scheduled events detected in the observation window.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

