"""
Reusable UI components for the ETE PMO Executive Dashboard.
KPI cards, charts, styled tables, and custom CSS.
"""

import altair as alt
import pandas as pd
import streamlit as st


# ---------------------------------------------------------------------------
# Color Palette
# ---------------------------------------------------------------------------
NAVY = "#1B3A5C"
BLUE = "#4A90D9"
LIGHT_BG = "#F8F9FA"
CARD_BG = "#FFFFFF"
GREEN = "#28A745"
YELLOW = "#FFC107"
RED = "#DC3545"
GRAY = "#6C757D"
LIGHT_GRAY = "#E9ECEF"

STATUS_COLORS = {"GREEN": GREEN, "YELLOW": YELLOW, "RED": RED}

ROLE_DISPLAY = {
    "pm": "PM",
    "ba": "Business Analyst",
    "functional": "Functional",
    "technical": "Technical",
    "developer": "Developer",
    "infrastructure": "Infrastructure",
    "dba": "DBA",
    "wms": "WMS Consultant",
}

ROLE_ORDER = ["pm", "ba", "functional", "technical", "developer",
              "infrastructure", "dba", "wms"]

PRIORITY_COLORS = {
    "Highest": RED,
    "High": "#E67E22",
    "Medium": BLUE,
    "Low": GRAY,
}


# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
def inject_css():
    """Inject executive-quality CSS into the Streamlit app."""
    st.markdown("""
    <style>
        /* Hide hamburger menu and footer */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* Typography */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        /* Page background */
        .stApp {
            background-color: #F8F9FA;
        }

        /* Tighter main content padding so wide visuals (Gantt) fill the viewport */
        .main .block-container,
        [data-testid="stMainBlockContainer"] {
            padding-left: 1.25rem !important;
            padding-right: 1.25rem !important;
            max-width: 100% !important;
        }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #1B3A5C;
        }
        [data-testid="stSidebar"] * {
            color: #E0E8F0 !important;
        }
        [data-testid="stSidebar"] .stRadio label {
            font-size: 0.95rem;
            padding: 0.3rem 0;
        }
        [data-testid="stSidebar"] hr {
            border-color: rgba(255,255,255,0.15) !important;
        }

        /* KPI card styling */
        .kpi-card {
            background: #FFFFFF;
            border-radius: 12px;
            padding: 1rem 1.25rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            border-left: 4px solid #4A90D9;
            margin-bottom: 0.5rem;
            min-height: 80px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .kpi-card.green {
            border-left: 4px solid #28A745;
            background: linear-gradient(135deg, #f0faf2 0%, #FFFFFF 40%);
        }
        .kpi-card.yellow {
            border-left: 4px solid #FFC107;
            background: linear-gradient(135deg, #fffbf0 0%, #FFFFFF 40%);
        }
        .kpi-card.red {
            border-left: 4px solid #DC3545;
            background: linear-gradient(135deg, #fef2f2 0%, #FFFFFF 40%);
        }
        .kpi-card.navy { border-left-color: #1B3A5C; }
        .kpi-clickable {
            transition: box-shadow 0.15s ease, transform 0.15s ease;
        }
        .kpi-clickable:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transform: translateY(-2px);
        }
        .kpi-label {
            font-size: 0.7rem;
            font-weight: 600;
            color: #6C757D;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.2rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .kpi-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: #1B3A5C;
            line-height: 1.2;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .kpi-delta {
            font-size: 0.75rem;
            margin-top: 0.2rem;
        }
        .kpi-delta.positive { color: #28A745; }
        .kpi-delta.negative { color: #DC3545; }

        /* Flex KPI row — responsive card container */
        .kpi-flex-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            margin-bottom: 1rem;
        }
        .kpi-flex-row .kpi-card {
            flex: 1;
            min-width: 140px;
            margin-bottom: 0;
        }

        /* Section headers */
        .section-header {
            font-size: 1.15rem;
            font-weight: 600;
            color: #1B3A5C;
            margin: 1.5rem 0 0.75rem 0;
            padding-bottom: 0.4rem;
            border-bottom: 2px solid #E9ECEF;
        }

        /* Status badges */
        .badge {
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }
        .badge-green { background: #D4EDDA; color: #155724; }
        .badge-yellow { background: #FFF3CD; color: #856404; }
        .badge-red { background: #F8D7DA; color: #721C24; }
        .badge-gray { background: #E9ECEF; color: #495057; }

        /* Clean container */
        .clean-container {
            background: #FFFFFF;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            margin-bottom: 1rem;
        }

        /* Metric overrides */
        [data-testid="stMetricValue"] {
            font-size: 1.8rem !important;
            font-weight: 700 !important;
            color: #1B3A5C !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.8rem !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
        }

        /* Dataframe styling */
        [data-testid="stDataFrame"] {
            border-radius: 8px;
            overflow: hidden;
        }

        /* Responsive KPI cards for smaller screens */
        @media (max-width: 1200px) {
            .kpi-card {
                padding: 0.75rem 1rem;
                min-height: 70px;
            }
            .kpi-value {
                font-size: 1.3rem;
            }
            .kpi-flex-row .kpi-card {
                min-width: 120px;
            }
            [data-testid="stMetricValue"] {
                font-size: 1.4rem !important;
            }
            [data-testid="stMetricLabel"] {
                font-size: 0.72rem !important;
            }
        }
        @media (max-width: 900px) {
            .kpi-card {
                padding: 0.6rem 0.75rem;
                min-height: 60px;
            }
            .kpi-value {
                font-size: 1.1rem;
            }
            .kpi-label {
                font-size: 0.65rem;
            }
            .kpi-flex-row .kpi-card {
                min-width: 100px;
            }
            [data-testid="stMetricValue"] {
                font-size: 1.2rem !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# KPI Cards
# ---------------------------------------------------------------------------
def kpi_card(label: str, value, color: str = "navy", delta: str = None):
    """Render a styled KPI card (use inside st.columns or on its own)."""
    delta_html = ""
    if delta:
        css_class = "positive" if not delta.startswith("-") else "negative"
        delta_html = f'<div class="kpi-delta {css_class}">{delta}</div>'
    st.markdown(
        f'<div class="kpi-card {color}">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'{delta_html}</div>',
        unsafe_allow_html=True,
    )


def kpi_row(items: list):
    """Render a responsive flex row of KPI cards.

    items: list of dicts with keys:
        label, value, color (optional), delta (optional),
        href (optional) — makes the card a clickable link
    """
    cards = []
    for item in items:
        label = item["label"]
        value = item["value"]
        color = item.get("color", "navy")
        delta = item.get("delta")
        href = item.get("href")
        delta_html = ""
        if delta:
            css_class = "positive" if not str(delta).startswith("-") else "negative"
            delta_html = f'<div class="kpi-delta {css_class}">{delta}</div>'
        inner = (
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div>'
            f'{delta_html}'
        )
        if href:
            cards.append(
                f'<a href="{href}" target="_self" class="kpi-card kpi-clickable {color}"'
                f' style="text-decoration:none; color:inherit; cursor:pointer;">'
                f'{inner}</a>'
            )
        else:
            cards.append(f'<div class="kpi-card {color}">{inner}</div>')
    st.markdown(
        '<div class="kpi-flex-row">' + ''.join(cards) + '</div>',
        unsafe_allow_html=True,
    )


def kpi_bar_row(items: list):
    """Render a flex row of KPI cards each with an integrated progress bar.

    items: list of dicts with keys:
        label, value, pct (0-1 float), color (optional), bar_color (optional),
        subtitle (optional)
    """
    cards = []
    for item in items:
        label = item["label"]
        value = item["value"]
        pct = item.get("pct", 0)
        color = item.get("color", "navy")
        bar_color = item.get("bar_color")
        subtitle = item.get("subtitle", "")

        _BORDER_MAP = {
            "green": "#28A745", "yellow": "#FFC107", "red": "#DC3545", "navy": "#1B3A5C",
        }
        border = _BORDER_MAP.get(color, "#1B3A5C")
        if not bar_color:
            bar_color = border

        sub_html = ""
        if subtitle:
            sub_html = (
                f'<div style="font-size:0.7rem; color:#6C757D; margin-top:0.15rem;">'
                f'{subtitle}</div>'
            )

        pct_clamped = max(0, min(pct, 1.0))
        cards.append(
            f'<div class="kpi-card {color}">'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div>'
            f'{sub_html}'
            f'<div style="height:6px; background:#E9ECEF; border-radius:3px;'
            f' overflow:hidden; margin-top:0.4rem;">'
            f'<div style="width:{pct_clamped*100:.0f}%; height:100%;'
            f' background:{bar_color}; border-radius:3px;"></div>'
            f'</div></div>'
        )
    st.markdown(
        '<div class="kpi-flex-row">' + ''.join(cards) + '</div>',
        unsafe_allow_html=True,
    )


def summary_banner(items: list, pills: list = None):
    """Render a full-width summary card with pills and inline metrics.

    pills: list of dicts with keys: label, style (CSS), icon (optional)
    items: list of dicts with keys: label, value
    """
    pill_html = ""
    if pills:
        pill_parts = []
        for p in pills:
            icon = p.get("icon", "")
            icon_html = f"{icon} " if icon else ""
            pill_parts.append(
                f'<span style="{p["style"]} display:inline-block; padding:0.3rem 0.75rem;'
                f' border-radius:20px; font-size:0.8rem; font-weight:600;">'
                f'{icon_html}{p["label"]}</span>'
            )
        pill_html = (
            '<div style="display:flex; flex-wrap:wrap; align-items:center;'
            ' gap:0.6rem; margin-bottom:1rem;">'
            + ''.join(pill_parts) + '</div>'
        )

    metric_parts = []
    for item in items:
        metric_parts.append(
            f'<div style="min-width:100px;">'
            f'<div style="font-size:0.7rem; font-weight:600; color:#6C757D;'
            f' text-transform:uppercase; letter-spacing:0.05em;">{item["label"]}</div>'
            f'<div style="font-size:1.35rem; font-weight:700; color:#1B3A5C;">'
            f'{item["value"]}</div></div>'
        )

    metrics_html = (
        '<div style="display:flex; flex-wrap:wrap; gap:1.5rem;">'
        + ''.join(metric_parts) + '</div>'
    )

    st.markdown(
        '<div style="background:#FFFFFF; border-radius:12px; padding:1.25rem 1.5rem;'
        ' box-shadow:0 1px 3px rgba(0,0,0,0.08); margin-bottom:1rem;">'
        + pill_html + metrics_html + '</div>',
        unsafe_allow_html=True,
    )


def progress_card(label: str, value: str, pct: float, bar_color: str = None,
                  subtitle: str = ""):
    """Single progress-bar KPI card (for use inside st.columns)."""
    if not bar_color:
        bar_color = "#1B3A5C"
    pct_clamped = max(0, min(pct, 1.0))
    sub_html = ""
    if subtitle:
        sub_html = (
            f'<div style="font-size:0.7rem; color:#6C757D; margin-top:0.15rem;">'
            f'{subtitle}</div>'
        )
    st.markdown(
        f'<div class="kpi-card navy">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'{sub_html}'
        f'<div style="height:6px; background:#E9ECEF; border-radius:3px;'
        f' overflow:hidden; margin-top:0.4rem;">'
        f'<div style="width:{pct_clamped*100:.0f}%; height:100%;'
        f' background:{bar_color}; border-radius:3px;"></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def section_header(text: str):
    """Render a styled section header."""
    st.markdown(f'<div class="section-header">{text}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Status Helpers
# ---------------------------------------------------------------------------
def status_color(status: str) -> str:
    """Map GREEN/YELLOW/RED to hex color."""
    return STATUS_COLORS.get(status, GRAY)


def status_badge_html(status: str) -> str:
    """Return HTML for a colored status badge."""
    if not status:
        return '<span class="badge badge-gray">N/A</span>'
    label = health_label(status)
    if label in ("On Track", "Complete"):
        return f'<span class="badge badge-green">{status}</span>'
    elif label in ("At Risk", "Needs Spec"):
        return f'<span class="badge badge-yellow">{status}</span>'
    elif label == "Needs Help":
        return f'<span class="badge badge-red">{status}</span>'
    return f'<span class="badge badge-gray">{status}</span>'


def util_color(pct: float) -> str:
    """Return GREEN/YELLOW/RED based on utilization thresholds."""
    if pct >= 1.0:
        return RED
    elif pct >= 0.80:
        return YELLOW
    return GREEN


def util_status(pct: float) -> str:
    if pct >= 1.0:
        return "RED"
    elif pct >= 0.80:
        return "YELLOW"
    return "GREEN"


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def utilization_bar_chart(utilization: dict) -> alt.Chart:
    """Horizontal bar chart of role utilization with threshold coloring."""
    rows = []
    for role_key in ROLE_ORDER:
        if role_key not in utilization:
            continue
        u = utilization[role_key]
        pct = u["utilization_pct"]
        if pct == float("inf"):
            pct = 2.0  # Cap for display
        rows.append({
            "Role": ROLE_DISPLAY.get(role_key, role_key),
            "Utilization": round(pct, 3),
            "Status": u["status"],
            "Supply": round(u["supply_hrs_week"], 1),
            "Demand": round(u["demand_hrs_week"], 1),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return None

    chart = alt.Chart(df).mark_bar(cornerRadiusEnd=4).encode(
        y=alt.Y("Role:N", sort=list(df["Role"]), title=None,
                axis=alt.Axis(labelFontSize=12, labelFontWeight=500)),
        x=alt.X("Utilization:Q", title="Utilization %",
                axis=alt.Axis(format=".0%", labelFontSize=11),
                scale=alt.Scale(domain=[0, max(1.0, df["Utilization"].max() * 1.15)])),
        color=alt.Color("Status:N",
                        scale=alt.Scale(domain=["GREEN", "YELLOW", "RED"],
                                        range=[GREEN, YELLOW, RED]),
                        legend=None),
        tooltip=[
            alt.Tooltip("Role:N"),
            alt.Tooltip("Utilization:Q", format=".0%"),
            alt.Tooltip("Supply:Q", title="Supply hrs/wk"),
            alt.Tooltip("Demand:Q", title="Demand hrs/wk"),
        ],
    ).properties(height=max(200, len(rows) * 40))

    # Add 80% and 100% threshold rules
    rules = alt.Chart(pd.DataFrame([
        {"threshold": 0.80, "label": "80%"},
        {"threshold": 1.00, "label": "100%"},
    ])).mark_rule(strokeDash=[4, 4], strokeWidth=1.5).encode(
        x="threshold:Q",
        color=alt.value(GRAY),
    )

    return (chart + rules).configure_view(strokeWidth=0)


from models import clean_health  # noqa: E402


def health_label(health: str) -> str:
    """Normalize a health string to a clean display label."""
    if not health:
        return "Unknown"
    h = health.upper().strip()
    if "ON TRACK" in h:
        return "On Track"
    elif "AT RISK" in h or "YELLOW" in h:
        return "At Risk"
    elif "NEEDS HELP" in h or "CRITICAL" in h or "RED" in h and "NOT" not in h:
        return "Needs Help"
    elif "POSTPONED" in h:
        return "Postponed"
    elif "COMPLETE" in h:
        return "Complete"
    elif "NOT STARTED" in h:
        return "Not Started"
    elif "NEEDS" in h and "FUNC" in h:
        return "Needs Func Spec"
    elif "NEEDS" in h and "TECH" in h:
        return "Needs Tech Spec"
    elif "NEEDS" in h:
        return "Needs Spec"
    return health.strip()


HEALTH_COLOR_MAP = {
    "On Track": GREEN,
    "At Risk": YELLOW,
    "Needs Help": RED,
    "Postponed": GRAY,
    "Complete": GREEN,
    "Not Started": LIGHT_GRAY,
    "Needs Func Spec": YELLOW,
    "Needs Tech Spec": YELLOW,
    "Needs Spec": YELLOW,
    "Unknown": LIGHT_GRAY,
}


def health_donut(projects: list) -> alt.Chart:
    """Donut chart of project health distribution."""
    health_counts = {}
    for p in projects:
        label = health_label(p.health)
        health_counts[label] = health_counts.get(label, 0) + 1

    df = pd.DataFrame([
        {"Health": k, "Count": v}
        for k, v in health_counts.items()
    ])
    if df.empty:
        return None

    domain = list(health_counts.keys())
    range_colors = [HEALTH_COLOR_MAP.get(d, GRAY) for d in domain]

    selection = alt.selection_point(fields=["Health"])

    chart = alt.Chart(df).mark_arc(innerRadius=50, outerRadius=90, cornerRadius=3).encode(
        theta=alt.Theta("Count:Q"),
        color=alt.Color("Health:N",
                        scale=alt.Scale(domain=domain, range=range_colors),
                        legend=alt.Legend(title=None, orient="none",
                                         direction="horizontal",
                                         labelFontSize=11, columns=3,
                                         symbolSize=80,
                                         legendX=40, legendY=210)),
        opacity=alt.condition(selection, alt.value(1.0), alt.value(0.6)),
        tooltip=["Health:N", "Count:Q"],
    ).add_params(
        selection,
    ).properties(
        height=250,
        width=300,
        autosize=alt.AutoSizeParams(type="pad", contains="padding"),
    ).configure_view(strokeWidth=0)

    return chart


def supply_demand_chart(utilization: dict) -> alt.Chart:
    """Grouped bar chart: supply vs demand by role."""
    rows = []
    for role_key in ROLE_ORDER:
        if role_key not in utilization:
            continue
        u = utilization[role_key]
        label = ROLE_DISPLAY.get(role_key, role_key)
        rows.append({"Role": label, "Metric": "Supply", "Hours/Week": round(u["supply_hrs_week"], 1)})
        rows.append({"Role": label, "Metric": "Demand", "Hours/Week": round(u["demand_hrs_week"], 1)})

    df = pd.DataFrame(rows)
    if df.empty:
        return None

    role_labels = [ROLE_DISPLAY.get(r, r) for r in ROLE_ORDER if r in utilization]

    chart = alt.Chart(df).mark_bar(cornerRadiusEnd=3).encode(
        x=alt.X("Role:N", sort=role_labels, title=None,
                axis=alt.Axis(labelFontSize=11, labelAngle=-30)),
        y=alt.Y("Hours/Week:Q", title="Hours / Week",
                axis=alt.Axis(labelFontSize=11)),
        color=alt.Color("Metric:N",
                        scale=alt.Scale(domain=["Supply", "Demand"],
                                        range=[BLUE, "#E67E22"]),
                        legend=alt.Legend(title=None, orient="top")),
        xOffset="Metric:N",
        tooltip=["Role:N", "Metric:N", "Hours/Week:Q"],
    ).properties(height=350)

    return chart.configure_view(strokeWidth=0)


def render_gantt_html(
    projects: list,
    color_by: str = "priority",
    group_by: str = "none",
    sort_by: str = "start",
    date_range: tuple = None,
) -> str:
    """Pure HTML/CSS Gantt chart — world-class layout with perfect row
    alignment, month header, today line, progress overlay, milestone diamonds,
    clickable rows, and responsive width.

    Returns a complete HTML string to be rendered via st.markdown(
        unsafe_allow_html=True).
    """
    import html as html_mod
    from datetime import date, timedelta

    if not projects:
        return '<div style="padding:2rem; color:#6C757D;">No projects to display.</div>'

    priority_weight = {"Highest": 0, "High": 1, "Medium": 2, "Low": 3}
    priority_color = {
        "Highest": "#DC3545", "High": "#E67E22",
        "Medium": "#4A90D9", "Low": "#94A3B8",
        "Unknown": "#CBD5E1",
    }
    health_color = {
        "Green": "#28A745", "Yellow": "#FFC107",
        "Red": "#DC3545", "Unknown": "#94A3B8",
    }
    # Deterministic palette for portfolios
    portfolio_palette = [
        "#4A90D9", "#E67E22", "#28A745", "#8E44AD", "#16A085",
        "#D35400", "#2980B9", "#C0392B", "#27AE60", "#7F8C8D",
    ]

    def _group_value(p):
        if group_by == "portfolio":
            return getattr(p, "portfolio", None) or "Unassigned"
        if group_by == "pm":
            return p.pm or "Unassigned"
        if group_by == "priority":
            return p.priority or "Unknown"
        if group_by == "health":
            return (p.health or "Unknown").title()
        return ""

    today = date.today()

    # --- Build row records ---
    rows = []
    for p in projects:
        if not p.start_date or not p.end_date:
            continue
        pct = max(0.0, min(1.0, p.pct_complete or 0.0))
        priority = p.priority or "Unknown"
        health = (p.health or "Unknown").title()
        portfolio = getattr(p, "portfolio", None) or "Unassigned"
        rows.append({
            "id": p.id,
            "name": p.name,
            "group": _group_value(p),
            "start": p.start_date,
            "end": p.end_date,
            "pct": pct,
            "priority": priority,
            "health": health,
            "portfolio": portfolio,
            "pm": p.pm or "—",
            "overdue": (p.end_date < today and pct < 1.0),
            "_priority_rank": priority_weight.get(priority, 4),
        })

    if not rows:
        return '<div style="padding:2rem; color:#6C757D;">No scheduled projects.</div>'

    # --- Sort ---
    sort_keys = []
    if group_by != "none":
        sort_keys.append(lambda r: r["group"])
    if sort_by == "start":
        sort_keys.append(lambda r: r["start"])
    elif sort_by == "end":
        sort_keys.append(lambda r: r["end"])
    elif sort_by == "priority":
        sort_keys += [lambda r: r["_priority_rank"], lambda r: r["start"]]
    elif sort_by == "name":
        sort_keys.append(lambda r: r["name"])

    from functools import cmp_to_key

    def _cmp(a, b):
        for k in sort_keys:
            av, bv = k(a), k(b)
            if av < bv:
                return -1
            if av > bv:
                return 1
        return 0
    rows.sort(key=cmp_to_key(_cmp))

    # --- Determine date range ---
    if date_range:
        range_start = date_range[0]
        range_end = date_range[1]
    else:
        range_start = min(r["start"] for r in rows) - timedelta(days=7)
        range_end = max(r["end"] for r in rows) + timedelta(days=7)
    # Clamp range_start to start-of-month for clean month header
    range_start = date(range_start.year, range_start.month, 1)
    # Extend range_end to end-of-month
    next_m = (date(range_end.year, range_end.month, 1)
              + timedelta(days=32)).replace(day=1)
    range_end = next_m - timedelta(days=1)
    total_days = max(1, (range_end - range_start).days + 1)

    def pct(d):
        """Convert a date to a percentage of the range width."""
        if d < range_start:
            return 0.0
        if d > range_end:
            return 100.0
        return ((d - range_start).days / total_days) * 100.0

    # --- Build month header segments ---
    months = []
    cursor = date(range_start.year, range_start.month, 1)
    while cursor <= range_end:
        next_cursor = (cursor + timedelta(days=32)).replace(day=1)
        m_start = max(cursor, range_start)
        m_end = min(next_cursor - timedelta(days=1), range_end)
        left = pct(m_start)
        right = pct(m_end) + (1 / total_days) * 100  # include last day
        months.append({
            "label": cursor.strftime("%b"),
            "year_label": cursor.strftime("%Y"),
            "left": left,
            "width": right - left,
            "is_q_start": cursor.month in (1, 4, 7, 10),
        })
        cursor = next_cursor

    # --- Color resolver ---
    portfolio_color_map = {}
    unique_portfolios = sorted({r["portfolio"] for r in rows})
    for i, pf in enumerate(unique_portfolios):
        portfolio_color_map[pf] = portfolio_palette[i % len(portfolio_palette)]

    def _bar_color(r):
        if color_by == "priority":
            return priority_color.get(r["priority"], priority_color["Unknown"])
        if color_by == "health":
            return health_color.get(r["health"], health_color["Unknown"])
        return portfolio_color_map.get(r["portfolio"], "#4A90D9")

    # --- Legend ---
    if color_by == "priority":
        legend_items = [("Highest", priority_color["Highest"]),
                        ("High", priority_color["High"]),
                        ("Medium", priority_color["Medium"]),
                        ("Low", priority_color["Low"])]
    elif color_by == "health":
        legend_items = [("On Track", health_color["Green"]),
                        ("At Risk", health_color["Yellow"]),
                        ("Critical", health_color["Red"])]
    else:
        legend_items = [(pf, portfolio_color_map[pf])
                        for pf in unique_portfolios]

    legend_html = ''.join(
        f'<span style="display:inline-flex; align-items:center; '
        f'margin-right:14px; font-size:11px; color:#4A5A6E; '
        f'font-weight:500;">'
        f'<span style="display:inline-block; width:12px; height:12px; '
        f'background:{color}; border-radius:3px; margin-right:5px;"></span>'
        f'{html_mod.escape(label)}</span>'
        for label, color in legend_items
    )

    # --- CSS (scoped via unique class) ---
    # CRITICAL: no leading whitespace on lines — st.markdown treats 4+ space
    # indented blocks as code. Use st.html() to render to be safe.
    ROW_H = 38
    HEADER_H = 56
    INFO_COL_W = 320  # px fixed left info panel

    import textwrap as _tw
    css = _tw.dedent(f"""\
<style>
.gantt-wrap {{ font-family:'Inter',-apple-system,sans-serif; border-radius:10px; background:#FFFFFF; box-shadow:0 1px 3px rgba(0,0,0,0.06); overflow:hidden; border:1px solid #E8ECF1; }}
.gantt-toolbar {{ display:flex; align-items:center; justify-content:space-between; padding:10px 16px; background:#F8FAFC; border-bottom:1px solid #E8ECF1; }}
.gantt-legend {{ font-size:11px; }}
.gantt-grid {{ display:grid; grid-template-columns:{INFO_COL_W}px 1fr; }}
.gantt-info-head {{ display:grid; grid-template-columns:58px 1fr 42px; align-items:center; gap:8px; padding:0 12px; height:{HEADER_H}px; background:#F8FAFC; border-bottom:2px solid #C5CDD8; font-size:10px; font-weight:700; color:#6C757D; text-transform:uppercase; letter-spacing:0.06em; }}
.gantt-info-head > div:last-child {{ text-align:right; }}
.gantt-month-head {{ position:relative; height:{HEADER_H}px; background:#F8FAFC; border-bottom:2px solid #C5CDD8; border-left:1px solid #E8ECF1; }}
.gantt-month {{ position:absolute; top:0; bottom:0; border-right:1px solid #E8ECF1; display:flex; flex-direction:column; align-items:center; justify-content:center; font-size:11px; font-weight:600; color:#4A5A6E; }}
.gantt-month-year {{ font-size:9px; font-weight:500; color:#94A3B8; text-transform:uppercase; letter-spacing:0.05em; }}
.gantt-month.q-start {{ border-left:2px solid #C5CDD8; }}
.gantt-info-body, .gantt-timeline-body {{ position:relative; }}
.gantt-timeline-body {{ border-left:1px solid #E8ECF1; }}
.gantt-row-info {{ display:grid; grid-template-columns:58px 1fr 42px; align-items:center; gap:8px; padding:0 12px; height:{ROW_H}px; border-bottom:1px solid #F1F4F8; text-decoration:none; color:#1B3A5C; font-size:12px; transition:background 0.12s; }}
.gantt-row-info:hover {{ background:#EEF2F7; }}
.gantt-row-info:nth-child(odd) {{ background:#FAFBFD; }}
.gantt-row-info:nth-child(odd):hover {{ background:#EEF2F7; }}
.gantt-row-id {{ font-weight:700; color:#1565C0; font-size:11px; }}
.gantt-row-name {{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-weight:500; }}
.gantt-row-pct {{ text-align:right; font-weight:600; color:#4A5A6E; font-size:11px; font-variant-numeric:tabular-nums; }}
.gantt-row-timeline {{ position:relative; height:{ROW_H}px; border-bottom:1px solid #F1F4F8; }}
.gantt-row-timeline:nth-child(odd) {{ background:#FAFBFD; }}
.gantt-group-info, .gantt-group-timeline {{ height:{ROW_H}px; background:#EEF2F7; border-bottom:1px solid #C5CDD8; border-top:1px solid #C5CDD8; display:flex; align-items:center; padding:0 12px; font-size:11px; font-weight:700; color:#1B3A5C; text-transform:uppercase; letter-spacing:0.05em; }}
.gantt-bar {{ position:absolute; top:50%; transform:translateY(-50%); height:22px; border-radius:5px; opacity:0.35; cursor:pointer; transition:opacity 0.15s, transform 0.15s; }}
.gantt-bar:hover {{ opacity:0.6; }}
.gantt-progress {{ position:absolute; top:50%; transform:translateY(-50%); height:22px; border-radius:5px; cursor:pointer; transition:filter 0.15s; }}
.gantt-progress:hover {{ filter:brightness(1.1); }}
.gantt-bar-overdue {{ position:absolute; top:50%; transform:translateY(-50%); height:22px; border:2px solid #DC3545; border-radius:5px; pointer-events:none; box-shadow:0 0 0 2px rgba(220,53,69,0.15); }}
.gantt-diamond {{ position:absolute; top:50%; width:9px; height:9px; background:#1B3A5C; transform:translate(-50%,-50%) rotate(45deg); pointer-events:none; }}
.gantt-pct-label {{ position:absolute; top:50%; transform:translateY(-50%); font-size:10px; font-weight:700; color:#1B3A5C; padding-left:6px; pointer-events:none; white-space:nowrap; }}
.gantt-today-line {{ position:absolute; top:0; bottom:0; width:0; border-left:2px dashed #DC3545; pointer-events:none; z-index:5; }}
.gantt-today-label {{ position:absolute; top:4px; transform:translateX(-50%); background:#DC3545; color:white; font-size:9px; font-weight:700; padding:1px 6px; border-radius:3px; letter-spacing:0.05em; pointer-events:none; z-index:6; }}
.gantt-grid-line {{ position:absolute; top:0; bottom:0; width:1px; background:#F1F4F8; pointer-events:none; }}
.gantt-grid-line.q-line {{ background:#E0E6ED; }}
</style>
""")

    # --- Build toolbar (legend) ---
    toolbar = f'<div class="gantt-toolbar"><div class="gantt-legend">{legend_html}</div></div>'

    # --- Build month header ---
    month_cells = []
    for m in months:
        q_cls = " q-start" if m["is_q_start"] else ""
        month_cells.append(
            f'<div class="gantt-month{q_cls}" '
            f'style="left:{m["left"]:.3f}%; width:{m["width"]:.3f}%;">'
            f'<div>{m["label"]}</div>'
            f'<div class="gantt-month-year">{m["year_label"]}</div>'
            f'</div>'
        )
    month_head_html = (
        '<div class="gantt-month-head">'
        + ''.join(month_cells)
        + '</div>'
    )

    info_head = (
        '<div class="gantt-info-head">'
        '<div>ID</div><div>Project</div><div>%</div>'
        '</div>'
    )

    # --- Build body rows (info panel + timeline) ---
    # We render two parallel columns inside the grid so rows align perfectly.
    info_rows_html = []
    timeline_rows_html = []
    prev_group = None
    for r in rows:
        if group_by != "none" and r["group"] != prev_group:
            info_rows_html.append(
                f'<div class="gantt-group-info">{html_mod.escape(r["group"])}</div>'
            )
            timeline_rows_html.append('<div class="gantt-group-timeline"></div>')
            prev_group = r["group"]

        # Info row
        pct_label = f"{int(round(r['pct'] * 100))}%"
        # Tooltip via title attr — quotes escaped, no newlines (they break
        # attribute parsing in some renderers). Use · separators.
        tooltip = html_mod.escape(
            f'{r["id"]}: {r["name"]}  ·  '
            f'PM: {r["pm"]}  ·  '
            f'{r["priority"]} priority  ·  '
            f'Health: {r["health"]}  ·  '
            f'{r["start"].strftime("%b %d, %Y")} → {r["end"].strftime("%b %d, %Y")}  ·  '
            f'{pct_label} complete',
            quote=True,
        )
        info_rows_html.append(
            f'<a class="gantt-row-info" href="?project={r["id"]}" target="_self" '
            f'title="{tooltip}">'
            f'<div class="gantt-row-id">{r["id"]}</div>'
            f'<div class="gantt-row-name">{html_mod.escape(r["name"])}</div>'
            f'<div class="gantt-row-pct">{pct_label}</div>'
            f'</a>'
        )

        # Timeline row
        bar_left = pct(r["start"])
        bar_right = pct(r["end"] + timedelta(days=1))
        bar_width = max(0.3, bar_right - bar_left)  # min visible width
        progress_width = bar_width * r["pct"]
        color = _bar_color(r)

        bar_html_parts = [
            f'<a href="?project={r["id"]}" target="_self" '
            f'title="{tooltip}" style="position:absolute; inset:0; '
            f'text-decoration:none; display:block;">',
            f'<div class="gantt-bar" '
            f'style="left:{bar_left:.3f}%; width:{bar_width:.3f}%; '
            f'background:{color};"></div>',
        ]
        if r["pct"] > 0:
            bar_html_parts.append(
                f'<div class="gantt-progress" '
                f'style="left:{bar_left:.3f}%; width:{progress_width:.3f}%; '
                f'background:{color};"></div>'
            )
        if r["overdue"]:
            bar_html_parts.append(
                f'<div class="gantt-bar-overdue" '
                f'style="left:{bar_left:.3f}%; width:{bar_width:.3f}%;"></div>'
            )
        # Milestone diamonds
        bar_html_parts.append(
            f'<div class="gantt-diamond" style="left:{bar_left:.3f}%;"></div>'
        )
        bar_html_parts.append(
            f'<div class="gantt-diamond" style="left:{bar_right:.3f}%;"></div>'
        )
        # % label at bar end (only when progress > 0)
        if r["pct"] > 0:
            bar_html_parts.append(
                f'<div class="gantt-pct-label" style="left:{bar_right:.3f}%;">'
                f'{pct_label}</div>'
            )
        bar_html_parts.append('</a>')

        timeline_rows_html.append(
            f'<div class="gantt-row-timeline">'
            + ''.join(bar_html_parts)
            + '</div>'
        )

    # --- Grid lines and today marker in timeline body ---
    today_left = pct(today) if range_start <= today <= range_end else None
    today_marker_html = ''
    if today_left is not None:
        today_marker_html = (
            f'<div class="gantt-today-line" style="left:{today_left:.3f}%;"></div>'
            f'<div class="gantt-today-label" style="left:{today_left:.3f}%;">TODAY</div>'
        )

    # Month vertical grid lines (inside the timeline body, behind bars)
    grid_lines_html = ''.join(
        f'<div class="gantt-grid-line'
        f'{" q-line" if m["is_q_start"] else ""}" '
        f'style="left:{m["left"]:.3f}%;"></div>'
        for m in months if m["left"] > 0
    )

    # Wrap the timeline body with grid lines and today marker as overlay
    timeline_body_html = (
        '<div class="gantt-timeline-body" style="position:relative;">'
        + grid_lines_html
        + ''.join(timeline_rows_html)
        + today_marker_html
        + '</div>'
    )
    info_body_html = (
        '<div class="gantt-info-body">'
        + ''.join(info_rows_html)
        + '</div>'
    )

    # --- Assemble ---
    html = (
        css
        + '<div class="gantt-wrap">'
        + toolbar
        + '<div class="gantt-grid">'
        + info_head
        + month_head_html
        + info_body_html
        + timeline_body_html
        + '</div></div>'
    )
    return html


def capacity_heatmap(heatmap_df: pd.DataFrame) -> alt.Chart:
    """Role x Week heatmap from the pre-computed DataFrame."""
    if heatmap_df.empty:
        return None

    # Melt to long format
    df_long = heatmap_df.melt(id_vars=["Role"], var_name="Week", value_name="Utilization")

    # Classify utilization into status buckets
    def _status(val):
        if val <= 0:
            return "None"
        elif val < 0.8:
            return "Green"
        elif val < 1.0:
            return "Yellow"
        else:
            return "Red"

    df_long["Status"] = df_long["Utilization"].apply(_status)

    # Only draw cells that have utilization > 0
    df_active = df_long[df_long["Utilization"] > 0]

    chart = alt.Chart(df_active).mark_rect(cornerRadius=2).encode(
        x=alt.X("Week:N", title=None,
                axis=alt.Axis(labelFontSize=9, labelAngle=-45)),
        y=alt.Y("Role:N", title=None,
                sort=["PM", "BA", "FUNCTIONAL", "TECHNICAL", "DEVELOPER",
                      "INFRASTRUCTURE", "DBA", "WMS"],
                axis=alt.Axis(labelFontSize=11)),
        color=alt.Color("Status:N",
                        scale=alt.Scale(
                            domain=["Green", "Yellow", "Red"],
                            range=[GREEN, YELLOW, RED],
                        ),
                        legend=alt.Legend(title="Utilization",
                                         symbolType="square",
                                         labelExpr="datum.label === 'Green' ? 'Under 80%' : datum.label === 'Yellow' ? '80–99%' : 'Over 100%'")),
        tooltip=[
            alt.Tooltip("Role:N"),
            alt.Tooltip("Week:N"),
            alt.Tooltip("Utilization:Q", format=".0%"),
        ],
    ).properties(height=280)

    return chart.configure_view(strokeWidth=0)


# ---------------------------------------------------------------------------
# Finance Gate
# ---------------------------------------------------------------------------
def is_finance_user() -> bool:
    """Check if the current user has finance access.
    On Streamlit Cloud, checks email against FINANCE_USERS secret.
    Locally (no auth), defaults to True for development.
    """
    try:
        finance_users = st.secrets.get("FINANCE_USERS", [])
    except Exception:
        # No secrets configured (local dev) — grant access
        return True

    if not finance_users:
        return True  # No restriction configured

    # Get logged-in user email from Streamlit Cloud
    try:
        user_email = st.context.headers.get("X-Forwarded-User", "")
    except Exception:
        user_email = ""

    if not user_email:
        return True  # Local development, no auth

    return user_email.lower() in [e.lower() for e in finance_users]
