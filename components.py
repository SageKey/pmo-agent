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


GANTT_ROW_STEP = 42      # px per row in the chart (and HTML info panel)
GANTT_TOP_PAD = 48       # px reserved above first row for legend/axis
GANTT_BOTTOM_PAD = 32    # px reserved below last row for axis


def gantt_chart(
    projects: list,
    color_by: str = "priority",
    group_by: str = "none",
    sort_by: str = "start",
    date_range: tuple = None,
) -> dict:
    """World-class Gantt chart with today line, progress overlay, milestones,
    grouping, and clickable bars. Returns a dict with the Altair chart plus
    ordered row metadata so the caller can render a matching info panel.

    Returns:
        {
            "chart": alt.LayerChart,          # gantt without y-axis labels
            "rows": list[dict],               # ordered row metadata
            "row_step": int,                  # px per row
            "top_pad": int, "bottom_pad": int,
            "total_height": int,
        }
    """
    from datetime import date, timedelta

    priority_weight = {"Highest": 0, "High": 1, "Medium": 2, "Low": 3}

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
    rows = []
    for p in projects:
        if not p.start_date or not p.end_date:
            continue
        pct = p.pct_complete or 0.0
        duration = (p.end_date - p.start_date).days or 1
        progress_days = int(duration * max(0.0, min(1.0, pct)))
        progress_end = p.start_date + timedelta(days=progress_days)
        overdue = (p.end_date < today and pct < 1.0)
        group = _group_value(p)
        label = f"{p.id}: {p.name}"
        rows.append({
            "ID": p.id,
            "Project": label,
            "Group": group,
            "Start": pd.to_datetime(p.start_date),
            "End": pd.to_datetime(p.end_date),
            "ProgressEnd": pd.to_datetime(progress_end),
            "Priority": p.priority or "Unknown",
            "Health": (p.health or "Unknown").title(),
            "Portfolio": getattr(p, "portfolio", None) or "Unassigned",
            "PM": p.pm or "—",
            "PctComplete": pct,
            "PctLabel": f"{pct:.0%}",
            "Overdue": overdue,
            "URL": f"?project={p.id}",
            "_priority_rank": priority_weight.get(p.priority, 4),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return None

    # Sort: group first (if any), then by chosen sort
    sort_cols = []
    if group_by != "none":
        sort_cols.append("Group")
    if sort_by == "start":
        sort_cols.append("Start")
    elif sort_by == "end":
        sort_cols.append("End")
    elif sort_by == "priority":
        sort_cols += ["_priority_rank", "Start"]
    elif sort_by == "name":
        sort_cols.append("Project")
    df = df.sort_values(sort_cols).reset_index(drop=True)

    # Build ordered y-axis labels (prepend group when grouping)
    if group_by != "none":
        df["RowLabel"] = df["Group"] + "  •  " + df["Project"]
    else:
        df["RowLabel"] = df["Project"]
    row_order = list(df["RowLabel"])

    # Color encoding
    if color_by == "priority":
        color_enc = alt.Color(
            "Priority:N",
            scale=alt.Scale(
                domain=["Highest", "High", "Medium", "Low", "Unknown"],
                range=[RED, "#E67E22", BLUE, GRAY, LIGHT_GRAY]),
            legend=alt.Legend(title=None, orient="top", labelFontSize=11))
    elif color_by == "health":
        color_enc = alt.Color(
            "Health:N",
            scale=alt.Scale(
                domain=["Green", "Yellow", "Red", "Unknown"],
                range=[GREEN, YELLOW, RED, GRAY]),
            legend=alt.Legend(title=None, orient="top", labelFontSize=11))
    else:  # portfolio
        color_enc = alt.Color(
            "Portfolio:N",
            legend=alt.Legend(title=None, orient="top", labelFontSize=11))

    # Shared tooltip
    tooltip = [
        alt.Tooltip("Project:N", title="Project"),
        alt.Tooltip("Portfolio:N", title="Portfolio"),
        alt.Tooltip("Priority:N"),
        alt.Tooltip("Health:N"),
        alt.Tooltip("PM:N", title="PM"),
        alt.Tooltip("Start:T", title="Start", format="%b %d, %Y"),
        alt.Tooltip("End:T", title="End", format="%b %d, %Y"),
        alt.Tooltip("PctLabel:N", title="% Complete"),
    ]

    # X-axis domain (time range filter)
    if date_range:
        x_scale = alt.Scale(domain=[
            pd.to_datetime(date_range[0]).isoformat(),
            pd.to_datetime(date_range[1]).isoformat(),
        ])
    else:
        x_scale = alt.Undefined

    # Chart sizing locked to GANTT_ROW_STEP so HTML info panel aligns exactly
    n = len(df)
    bar_height = int(GANTT_ROW_STEP * 0.6)  # ~25 px
    total_height = GANTT_TOP_PAD + (n * GANTT_ROW_STEP) + GANTT_BOTTOM_PAD

    # Y-axis: labels HIDDEN — task info rendered by caller in left panel
    y_enc = alt.Y(
        "RowLabel:N",
        sort=row_order,
        title=None,
        scale=alt.Scale(paddingInner=0.25, paddingOuter=0.1),
        axis=alt.Axis(labels=False, ticks=False, domain=False,
                      grid=True, gridOpacity=0.25),
    )

    # X-axis — single clean bottom axis. All layers share the same x/x2 with
    # explicit title=None so no concatenated "StartProgressEnd" title artifact.
    def _x(field="Start:T", orient="bottom", grid=True):
        return alt.X(
            field,
            title=None,
            scale=x_scale,
            axis=alt.Axis(
                labelFontSize=11, format="%b %Y",
                tickCount="month", grid=grid, gridOpacity=0.35,
                domain=False, labelPadding=6, orient=orient,
                labelColor="#4A5A6E",
            ),
        )
    x_enc = _x()

    layers = []

    # Background bar — full duration, muted
    bars_bg = alt.Chart(df).mark_bar(
        cornerRadius=5, height=bar_height, opacity=0.32, clip=True,
    ).encode(
        y=y_enc, x=x_enc,
        x2=alt.X2("End:T", title=""),
        color=color_enc,
        href=alt.Href("URL:N"),
        tooltip=tooltip,
    )
    layers.append(bars_bg)

    # Progress overlay — start → progress_end, full opacity
    progress_df = df[df["PctComplete"] > 0]
    if not progress_df.empty:
        bars_progress = alt.Chart(progress_df).mark_bar(
            cornerRadius=5, height=bar_height, clip=True,
        ).encode(
            y=alt.Y("RowLabel:N", sort=row_order, title=None,
                    axis=alt.Axis(labels=False, ticks=False, domain=False)),
            x=alt.X("Start:T", title=None, scale=x_scale,
                    axis=alt.Axis(labels=False, ticks=False, domain=False)),
            x2=alt.X2("ProgressEnd:T", title=""),
            color=color_enc,
            href=alt.Href("URL:N"),
            tooltip=tooltip,
        )
        layers.append(bars_progress)

    # Overdue outline — red stroke on bars past end date & not complete
    overdue_df = df[df["Overdue"]]
    if not overdue_df.empty:
        overdue_outline = alt.Chart(overdue_df).mark_bar(
            cornerRadius=5, height=bar_height, clip=True,
            fillOpacity=0, stroke=RED, strokeWidth=2.5,
        ).encode(
            y=alt.Y("RowLabel:N", sort=row_order, title=None,
                    axis=alt.Axis(labels=False, ticks=False, domain=False)),
            x=alt.X("Start:T", title=None, scale=x_scale,
                    axis=alt.Axis(labels=False, ticks=False, domain=False)),
            x2=alt.X2("End:T", title=""),
            tooltip=tooltip,
            href=alt.Href("URL:N"),
        )
        layers.append(overdue_outline)

    # Start & end milestone diamonds
    start_points = alt.Chart(df).mark_point(
        shape="diamond", size=85, filled=True, color=NAVY,
        opacity=0.9, clip=True,
    ).encode(
        y=alt.Y("RowLabel:N", sort=row_order, title=None,
                axis=alt.Axis(labels=False, ticks=False, domain=False)),
        x=alt.X("Start:T", title=None, scale=x_scale,
                axis=alt.Axis(labels=False, ticks=False, domain=False)),
        tooltip=tooltip,
    )
    end_points = alt.Chart(df).mark_point(
        shape="diamond", size=85, filled=True, color=NAVY,
        opacity=0.9, clip=True,
    ).encode(
        y=alt.Y("RowLabel:N", sort=row_order, title=None,
                axis=alt.Axis(labels=False, ticks=False, domain=False)),
        x=alt.X("End:T", title=None, scale=x_scale,
                axis=alt.Axis(labels=False, ticks=False, domain=False)),
        tooltip=tooltip,
    )
    layers += [start_points, end_points]

    # % Complete text — rendered at bar end when > 0
    pct_df = df[df["PctComplete"] > 0]
    if not pct_df.empty:
        pct_labels = alt.Chart(pct_df).mark_text(
            align="left", baseline="middle", dx=10, fontSize=11,
            fontWeight="bold", color=NAVY, clip=True,
        ).encode(
            y=alt.Y("RowLabel:N", sort=row_order, title=None,
                    axis=alt.Axis(labels=False, ticks=False, domain=False)),
            x=alt.X("End:T", title=None, scale=x_scale,
                    axis=alt.Axis(labels=False, ticks=False, domain=False)),
            text="PctLabel:N",
        )
        layers.append(pct_labels)

    # Today line + label
    today_df = pd.DataFrame({"date": [pd.to_datetime(today)]})
    today_rule = alt.Chart(today_df).mark_rule(
        color=RED, strokeWidth=2.5, strokeDash=[6, 4],
    ).encode(
        x=alt.X("date:T", title=None, scale=x_scale,
                axis=alt.Axis(labels=False, ticks=False, domain=False)),
    )
    today_label = alt.Chart(today_df).mark_text(
        text="TODAY", align="center", dy=-6,
        fontSize=11, fontWeight="bold", color=RED,
    ).encode(
        x=alt.X("date:T", title=None, scale=x_scale,
                axis=alt.Axis(labels=False, ticks=False, domain=False)),
        y=alt.value(0),
    )
    layers += [today_rule, today_label]

    chart = alt.layer(*layers).properties(
        height=total_height,
        padding={"left": 6, "right": 18, "top": 4, "bottom": 4},
    ).configure_view(strokeWidth=0).configure_axis(
        labelColor="#4A5A6E", titleColor=NAVY,
    )

    # Info rows for the caller's left panel
    info_rows = []
    for _, r in df.iterrows():
        info_rows.append({
            "id": r["ID"],
            "name": r["Project"].split(": ", 1)[1] if ": " in r["Project"] else r["Project"],
            "group": r["Group"],
            "pm": r["PM"],
            "priority": r["Priority"],
            "health": r["Health"],
            "pct": r["PctLabel"],
            "start": r["Start"].strftime("%b %d"),
            "end": r["End"].strftime("%b %d"),
        })

    return {
        "chart": chart,
        "rows": info_rows,
        "row_step": GANTT_ROW_STEP,
        "top_pad": GANTT_TOP_PAD,
        "bottom_pad": GANTT_BOTTOM_PAD,
        "total_height": total_height,
        "grouped": group_by != "none",
    }


def gantt_info_panel_html(result: dict) -> str:
    """Build the left-side task info panel that aligns row-by-row with the
    Gantt chart returned by gantt_chart()."""
    row_step = result["row_step"]
    top_pad = result["top_pad"]
    bottom_pad = result["bottom_pad"]
    grouped = result.get("grouped", False)

    css_grid = (
        "display:grid; "
        "grid-template-columns: 54px 1fr 44px; "
        "column-gap:8px; align-items:center; "
        f"height:{row_step}px; "
        "padding:0 10px; "
        "border-bottom:1px solid #EEF1F5; "
        "text-decoration:none; color:#1B3A5C; "
        "font-size:11.5px; line-height:1.15; "
        "transition:background 0.15s;"
    )
    hover_js = "this.style.background='#F4F6F9'"
    unhover_js = "this.style.background=''"

    # Header strip sits inside top_pad (flush with chart top)
    html = [
        f'<div style="padding-top:{top_pad - 22}px;">',
        '<div style="display:grid; grid-template-columns:54px 1fr 44px; '
        'column-gap:8px; padding:0 10px 6px 10px; font-size:10px; '
        'font-weight:700; color:#6C757D; text-transform:uppercase; '
        'letter-spacing:0.06em; border-bottom:2px solid #C5CDD8;">'
        '<div>ID</div><div>Project</div><div style="text-align:right;">%</div>'
        '</div>',
    ]

    prev_group = None
    for r in result["rows"]:
        if grouped and r["group"] != prev_group:
            # Group header row — occupies one row slot
            html.append(
                f'<div style="height:{row_step}px; display:flex; '
                f'align-items:center; padding:0 10px; font-size:11px; '
                f'font-weight:700; color:#1B3A5C; background:#EEF2F7; '
                f'text-transform:uppercase; letter-spacing:0.04em; '
                f'border-bottom:1px solid #C5CDD8;">{r["group"]}</div>'
            )
            prev_group = r["group"]
        html.append(
            f'<a href="?project={r["id"]}" target="_self" '
            f'style="{css_grid}" '
            f'onmouseover="{hover_js}" onmouseout="{unhover_js}" '
            f'title="{r["name"]} — PM: {r["pm"]}, {r["priority"]} priority, '
            f'{r["start"]} → {r["end"]}">'
            f'<div style="font-weight:700; color:#1565C0;">{r["id"]}</div>'
            f'<div style="overflow:hidden; text-overflow:ellipsis; '
            f'white-space:nowrap;">{r["name"]}</div>'
            f'<div style="text-align:right; font-weight:600; color:#4A5A6E;">'
            f'{r["pct"]}</div>'
            f'</a>'
        )

    html.append(f'<div style="height:{bottom_pad}px;"></div>')
    html.append('</div>')
    return "".join(html)


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
