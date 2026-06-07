"""
CloudRouteAI — Theme Engine
============================
Centralized CSS injection, reusable UI components, chart theming,
and animation system for the Cyber Navy dashboard aesthetic.
"""

import streamlit as st
import streamlit.components.v1 as components


# ──────────────────────────────────────────────────────────────────
# Color Tokens
# ──────────────────────────────────────────────────────────────────
COLORS = {
    "bg_primary":   "#050d1a",
    "bg_surface":   "#0d1b2e",
    "bg_elevated":  "#132238",
    "accent_1":     "#00d4ff",   # electric cyan
    "accent_2":     "#7c3aed",   # neon violet
    "accent_3":     "#00ff88",   # cyber green
    "text_primary": "#e2e8f0",
    "text_muted":   "#64748b",
    "danger":       "#ef4444",
    "warning":      "#f59e0b",
    "success":      "#10b981",
    "info":         "#38bdf8",
}


# ──────────────────────────────────────────────────────────────────
# Global CSS Injection
# ──────────────────────────────────────────────────────────────────
def inject_global_css():
    """Inject the complete Cyber Navy CSS system into the Streamlit app."""
    st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@300;400;500;600;700;800&family=DM+Sans:wght@300;400;500;600;700&display=swap');

/* ── CSS Custom Properties ── */
:root {
    --bg-primary: #050d1a;
    --bg-surface: #0d1b2e;
    --bg-elevated: #132238;
    --accent-1: #00d4ff;
    --accent-2: #7c3aed;
    --accent-3: #00ff88;
    --text-primary: #e2e8f0;
    --text-muted: #64748b;
    --danger: #ef4444;
    --warning: #f59e0b;
    --success: #10b981;
    --font-display: 'Exo 2', sans-serif;
    --font-body: 'DM Sans', sans-serif;
}

/* ── Hide Streamlit Defaults ── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden !important;}

/* ── Global Body ── */
.stApp {
    background: linear-gradient(145deg, var(--bg-primary) 0%, #081425 50%, var(--bg-primary) 100%) !important;
    font-family: var(--font-body) !important;
    color: var(--text-primary) !important;
}
.main .block-container {
    padding-top: 1rem !important;
}

/* ── Typography ── */
h1, h2, h3, h4, h5, h6,
[data-testid="stHeadingWithActionElements"] {
    font-family: var(--font-display) !important;
    color: var(--text-primary) !important;
    font-weight: 700 !important;
    letter-spacing: 0.02em;
}
p, span, div, label {
    font-family: var(--font-body) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #070e1c 0%, var(--bg-surface) 60%, #081220 100%) !important;
    border-right: 1px solid rgba(0, 212, 255, 0.08) !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: var(--text-primary) !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(0, 212, 255, 0.1) !important;
}

/* ── Sidebar Breathing Accent Line ── */
[data-testid="stSidebar"]::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    background: linear-gradient(180deg, var(--accent-1), var(--accent-2), var(--accent-1));
    background-size: 100% 200%;
    animation: breathe 4s ease-in-out infinite;
    z-index: 999;
}

/* ── Tab Styling ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: rgba(13, 27, 46, 0.6) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 2px !important;
    border: 1px solid rgba(0, 212, 255, 0.08);
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    font-family: var(--font-display) !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    color: var(--text-muted) !important;
    border-radius: 8px !important;
    padding: 8px 16px !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover {
    color: var(--accent-1) !important;
    background: rgba(0, 212, 255, 0.06) !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: var(--accent-1) !important;
    background: rgba(0, 212, 255, 0.12) !important;
    box-shadow: 0 0 12px rgba(0, 212, 255, 0.15) !important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
    background-color: var(--accent-1) !important;
    height: 2px !important;
    border-radius: 2px !important;
}
[data-testid="stTabs"] [data-baseweb="tab-border"] {
    display: none !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, var(--accent-1) 0%, var(--accent-2) 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.6rem 1.2rem !important;
    font-family: var(--font-display) !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.03em !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 15px rgba(0, 212, 255, 0.2) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(0, 212, 255, 0.35) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}

/* ── Download Buttons ── */
.stDownloadButton > button {
    background: rgba(0, 212, 255, 0.1) !important;
    color: var(--accent-1) !important;
    border: 1px solid rgba(0, 212, 255, 0.3) !important;
    border-radius: 10px !important;
    font-family: var(--font-display) !important;
    font-weight: 600 !important;
    transition: all 0.3s !important;
}
.stDownloadButton > button:hover {
    background: rgba(0, 212, 255, 0.2) !important;
    box-shadow: 0 4px 15px rgba(0, 212, 255, 0.15) !important;
}

/* ── Selectbox / Slider / Inputs ── */
[data-testid="stSelectbox"] > div > div {
    background: var(--bg-surface) !important;
    border-color: rgba(0, 212, 255, 0.15) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
}
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
    background: var(--accent-1) !important;
    border-color: var(--accent-1) !important;
}

/* ── Metric Card ── */
.cn-metric-card {
    background: rgba(13, 27, 46, 0.6);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(0, 212, 255, 0.1);
    padding: 1.5rem;
    border-radius: 16px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    text-align: center;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    animation: slideUp 0.6s ease-out both;
    position: relative;
    overflow: hidden;
}
.cn-metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent-1), var(--accent-2));
    opacity: 0.8;
}
.cn-metric-card:hover {
    transform: translateY(-4px);
    border-color: rgba(0, 212, 255, 0.3);
    box-shadow: 0 16px 48px rgba(0, 212, 255, 0.12);
}
.cn-metric-icon {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
    filter: drop-shadow(0 0 6px rgba(0, 212, 255, 0.4));
}
.cn-metric-value {
    font-family: var(--font-display);
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(135deg, var(--accent-1), var(--accent-2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.3rem;
    animation: glowPulse 3s ease-in-out infinite;
}
.cn-metric-label {
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 600;
    font-family: var(--font-display);
}
.cn-metric-delta {
    font-size: 0.8rem;
    font-weight: 600;
    margin-top: 0.4rem;
}

/* ── Glass Panel ── */
.cn-glass-panel {
    background: rgba(13, 27, 46, 0.5);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(0, 212, 255, 0.08);
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
    animation: fadeIn 0.5s ease-out both;
}
.cn-glass-panel:hover {
    border-color: rgba(0, 212, 255, 0.15);
}

/* ── Nav Items ── */
.cn-nav-item {
    padding: 0.7rem 1rem;
    border-radius: 10px;
    margin-bottom: 0.3rem;
    color: var(--text-muted);
    font-size: 0.88rem;
    font-weight: 500;
    font-family: var(--font-display);
    display: flex;
    align-items: center;
    gap: 0.6rem;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    text-decoration: none !important;
}
.cn-nav-item:hover {
    background: rgba(0, 212, 255, 0.08);
    color: var(--accent-1);
    padding-left: 1.2rem;
}
.cn-nav-active {
    background: rgba(0, 212, 255, 0.12) !important;
    color: var(--accent-1) !important;
    border-left: 3px solid var(--accent-1);
    box-shadow: inset 0 0 20px rgba(0, 212, 255, 0.05);
}

/* ── Status Badges ── */
.cn-badge {
    padding: 0.25rem 0.7rem;
    border-radius: 9999px;
    font-size: 0.7rem;
    font-weight: 700;
    font-family: var(--font-display);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    display: inline-block;
}
.cn-badge-healthy { background: rgba(0, 255, 136, 0.1); color: var(--accent-3); border: 1px solid rgba(0, 255, 136, 0.3); }
.cn-badge-active  { background: rgba(0, 212, 255, 0.1); color: var(--accent-1); border: 1px solid rgba(0, 212, 255, 0.3); }
.cn-badge-alert   { background: rgba(245, 158, 11, 0.1); color: var(--warning); border: 1px solid rgba(245, 158, 11, 0.3); }
.cn-badge-danger  { background: rgba(239, 68, 68, 0.1); color: var(--danger); border: 1px solid rgba(239, 68, 68, 0.3); }

/* ── Gradient Divider ── */
.cn-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.2), transparent);
    border: none;
    margin: 1.5rem 0;
}

/* ── Scenario Card ── */
.cn-scenario-card {
    background: rgba(13, 27, 46, 0.4);
    padding: 1rem;
    border-radius: 12px;
    border: 1px solid rgba(0, 212, 255, 0.06);
    margin-bottom: 0.5rem;
    transition: all 0.25s;
    cursor: pointer;
}
.cn-scenario-card:hover {
    border-color: rgba(0, 212, 255, 0.25);
    background: rgba(13, 27, 46, 0.6);
}

/* ── Staggered Column Reveal ── */
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(1) { animation: slideUp 0.5s ease-out 0.0s both; }
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(2) { animation: slideUp 0.5s ease-out 0.1s both; }
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(3) { animation: slideUp 0.5s ease-out 0.2s both; }
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(4) { animation: slideUp 0.5s ease-out 0.3s both; }

/* ── Expander Styling ── */
[data-testid="stExpander"] {
    background: rgba(13, 27, 46, 0.4) !important;
    border: 1px solid rgba(0, 212, 255, 0.08) !important;
    border-radius: 12px !important;
}

/* ── Streamlit alerts ── */
[data-testid="stAlert"] {
    border-radius: 12px !important;
}

/* ── Horizontal Rules ── */
hr {
    border-color: rgba(0, 212, 255, 0.08) !important;
}

/* ══════════ ANIMATION KEYFRAMES ══════════ */

@keyframes slideUp {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
}

@keyframes glowPulse {
    0%, 100% { filter: drop-shadow(0 0 4px rgba(0, 212, 255, 0.3)); }
    50%      { filter: drop-shadow(0 0 12px rgba(0, 212, 255, 0.6)); }
}

@keyframes fadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
}

@keyframes breathe {
    0%, 100% { background-position: 0% 0%; opacity: 0.6; }
    50%      { background-position: 0% 100%; opacity: 1; }
}

</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────
# Reusable Components
# ──────────────────────────────────────────────────────────────────

def metric_card(title, value, icon="📊", color=None, idx=0):
    """Render a premium animated metric card."""
    delay = idx * 0.1
    accent = color or COLORS["accent_1"]
    st.markdown(f"""
    <div class="cn-metric-card" style="animation-delay: {delay}s; --card-accent: {accent};">
        <div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg, {accent}, var(--accent-2));opacity:0.9;"></div>
        <div class="cn-metric-icon">{icon}</div>
        <div class="cn-metric-value">{value}</div>
        <div class="cn-metric-label">{title}</div>
    </div>
    """, unsafe_allow_html=True)


def section_header(title, subtitle="", icon=""):
    """Render a glass-panel section header."""
    sub_html = f'<p style="color:var(--text-muted);margin:0.4rem 0 0 0;font-size:0.9rem;">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
    <div class="cn-glass-panel" style="margin-bottom:1.5rem;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <h2 style="margin:0;color:var(--accent-1);font-family:var(--font-display);">{icon} {title}</h2>
                {sub_html}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def divider():
    """Render a gradient accent divider."""
    st.markdown('<div class="cn-divider"></div>', unsafe_allow_html=True)


def hero_banner(title, subtitle, timestamp_label=""):
    """Full-width hero banner with animated grid background."""
    ts_html = ""
    if timestamp_label:
        ts_html = f"""
        <div style="background:rgba(0,212,255,0.08);border:1px solid rgba(0,212,255,0.2);
                    padding:0.5rem 1rem;border-radius:8px;text-align:right;">
            <span style="color:var(--text-muted);font-size:0.7rem;text-transform:uppercase;
                         font-weight:600;letter-spacing:0.08em;">Last Updated</span>
            <div style="color:var(--accent-1);font-size:1rem;font-weight:700;font-family:var(--font-display);">
                {timestamp_label}
            </div>
        </div>
        """

    components.html(f"""
    <div style="position:relative;background:linear-gradient(135deg,#050d1a 0%,#0d1b2e 50%,#081425 100%);
                border-radius:20px;padding:2.5rem 2rem;border:1px solid rgba(0,212,255,0.1);
                overflow:hidden;margin-bottom:1rem;box-shadow:0 8px 40px rgba(0,0,0,0.5);">
        <canvas id="gridCanvas" style="position:absolute;top:0;left:0;width:100%;height:100%;opacity:0.15;"></canvas>
        <div style="position:relative;z-index:1;display:flex;justify-content:space-between;align-items:center;">
            <div>
                <h1 style="margin:0;font-family:'Exo 2',sans-serif;font-size:2.2rem;font-weight:800;
                           background:linear-gradient(135deg,#00d4ff,#7c3aed);-webkit-background-clip:text;
                           -webkit-text-fill-color:transparent;letter-spacing:0.03em;">
                    {title}
                </h1>
                <p style="color:#64748b;margin:0.5rem 0 0 0;font-family:'DM Sans',sans-serif;font-size:1rem;">
                    {subtitle}
                </p>
            </div>
            {ts_html}
        </div>
    </div>
    <script>
    (function() {{
        const canvas = document.getElementById('gridCanvas');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        canvas.width = canvas.offsetWidth * 2;
        canvas.height = canvas.offsetHeight * 2;
        ctx.scale(2, 2);
        const w = canvas.offsetWidth, h = canvas.offsetHeight;
        const spacing = 30;
        let offset = 0;
        function draw() {{
            ctx.clearRect(0, 0, w, h);
            ctx.strokeStyle = 'rgba(0, 212, 255, 0.3)';
            ctx.lineWidth = 0.5;
            for (let x = offset % spacing; x < w; x += spacing) {{
                ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
            }}
            for (let y = offset % spacing; y < h; y += spacing) {{
                ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
            }}
            offset += 0.15;
            requestAnimationFrame(draw);
        }}
        draw();
    }})();
    </script>
    """, height=140)


def chart_theme():
    """Return a Plotly layout dict matching the Cyber Navy palette."""
    return dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,212,255,0.02)',
        font=dict(family="'DM Sans', sans-serif", color='#e2e8f0', size=12),
        xaxis=dict(
            gridcolor='rgba(0,212,255,0.06)',
            showline=False,
            zeroline=False,
            title_font=dict(family="'Exo 2', sans-serif", color='#64748b'),
        ),
        yaxis=dict(
            gridcolor='rgba(0,212,255,0.06)',
            showline=False,
            zeroline=False,
            title_font=dict(family="'Exo 2', sans-serif", color='#64748b'),
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(
            bgcolor='rgba(0,0,0,0)',
            font=dict(color='#94a3b8', family="'DM Sans', sans-serif"),
        ),
        hoverlabel=dict(
            bgcolor='#0d1b2e',
            bordercolor='rgba(0,212,255,0.3)',
            font=dict(color='#e2e8f0', family="'DM Sans', sans-serif"),
        ),
    )


# Chart trace colors for consistent palette
CHART_COLORS = {
    "primary":   "#00d4ff",
    "secondary": "#7c3aed",
    "success":   "#00ff88",
    "danger":    "#ef4444",
    "warning":   "#f59e0b",
    "info":      "#38bdf8",
    "muted":     "#334155",
}
