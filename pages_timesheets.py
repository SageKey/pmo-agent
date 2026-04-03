"""Vendor Timesheets page for the ETE PMO Dashboard.

Provides timesheet entry, review, approval workflow, and invoice tracking
for Synnergie vendor consultants.

Tabs:
  1. Timesheet Entry — consultants enter daily hours
  2. Monthly Review — manager view of all submitted timesheets
  3. Approvals — approval workflow (draft → submitted → approved)
  4. Invoices — monthly invoice tracking and reconciliation
  5. Approved Work — work authorization register
"""

from collections import defaultdict
from datetime import date, datetime, timedelta

import altair as alt
import pandas as pd
import streamlit as st

from components import kpi_card, section_header, is_finance_user, NAVY
from sqlite_connector import SQLiteConnector
from data_layer import DB_PATH


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _get_connector() -> SQLiteConnector:
    return SQLiteConnector(DB_PATH)


def _month_options(year: int) -> list[str]:
    """Generate YYYY-MM options for a year, up to current month if current year."""
    today = date.today()
    months = []
    for m in range(1, 13):
        if year == today.year and m > today.month:
            break
        months.append(f"{year}-{m:02d}")
    return list(reversed(months))  # Most recent first


def _week_dates(ref_date: date) -> list[date]:
    """Return Mon–Sun dates for the week containing ref_date."""
    monday = ref_date - timedelta(days=ref_date.weekday())
    return [monday + timedelta(days=i) for i in range(7)]


# ---------------------------------------------------------------------------
# Tab: Timesheet Entry
# ---------------------------------------------------------------------------

def _render_entry_tab(consultants: list[dict]):
    """Timesheet entry form — consultant selects name, enters daily hours."""

    if not consultants:
        st.info("No vendor consultants configured. Import data first.")
        return

    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        consultant_names = [c["name"] for c in consultants]
        selected_name = st.selectbox("Consultant", consultant_names, key="_ts_consultant")
        selected = next((c for c in consultants if c["name"] == selected_name), None)

    with col2:
        entry_date = st.date_input("Week of", value=date.today(), key="_ts_date")

    with col3:
        st.markdown("<div style='height: 1.8rem'></div>", unsafe_allow_html=True)
        billing_label = f"{selected['billing_type']}"
        if selected and selected["hourly_rate"] > 0:
            billing_label += f" @ ${selected['hourly_rate']:.0f}/hr"
        st.markdown(f"""<div style="padding:0.5rem 0.75rem; background:#F0F4F8;
            border-radius:8px; font-size:0.85rem; color:#5A6A7E;">
            Billing: <strong>{billing_label}</strong>
        </div>""", unsafe_allow_html=True)

    if not selected:
        return

    # Load existing entries for the selected week
    week = _week_dates(entry_date)
    week_start = week[0].isoformat()
    week_end = week[-1].isoformat()

    connector = _get_connector()
    try:
        all_entries = connector.read_timesheets(consultant_id=selected["id"])
    finally:
        connector.close()

    existing = {e["entry_date"]: e for e in all_entries
                if week_start <= e["entry_date"] <= week_end}

    st.markdown("<div style='height: 0.75rem'></div>", unsafe_allow_html=True)
    section_header(f"Week: {week[0].strftime('%b %d')} – {week[-1].strftime('%b %d, %Y')}")

    # Show existing entries for this week in a table
    week_entries = [e for e in all_entries
                    if week_start <= e["entry_date"] <= week_end]

    if week_entries:
        rows = []
        total_hrs = 0
        for e in sorted(week_entries, key=lambda x: (x["entry_date"], x.get("project_key", ""))):
            d = date.fromisoformat(e["entry_date"])
            rows.append({
                "Date": d.strftime("%a %b %d"),
                "Project Key": e.get("project_key") or "—",
                "Project": (e.get("project_name") or "General Support")[:40],
                "Task": (e.get("task_description") or "")[:50],
                "Type": e.get("work_type", ""),
                "Hours": e["hours"],
                "_id": e["id"],
            })
            total_hrs += e["hours"]

        df = pd.DataFrame(rows)

        # Week summary KPIs
        project_hrs = sum(e["hours"] for e in week_entries if e.get("work_type") == "Project")
        support_hrs = sum(e["hours"] for e in week_entries if e.get("work_type") == "Support")

        kc1, kc2, kc3 = st.columns(3)
        with kc1:
            kpi_card("Week Total", f"{total_hrs:.0f}h", "navy")
        with kc2:
            kpi_card("Project", f"{project_hrs:.0f}h", "navy")
        with kc3:
            kpi_card("Support", f"{support_hrs:.0f}h", "navy")

        st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)

        # Display table
        display_df = df.drop(columns=["_id"])
        st.dataframe(display_df, hide_index=True, use_container_width=True)

    else:
        st.caption("No entries for this week yet.")

    # --- Add New Entry Form ---
    st.markdown("<div style='height: 0.75rem'></div>", unsafe_allow_html=True)
    with st.expander("Add Time Entry", expanded=not bool(week_entries)):
        with st.form("ts_entry_form", clear_on_submit=True):
            fc1, fc2 = st.columns(2)
            with fc1:
                new_date = st.date_input("Date", value=entry_date, key="_ts_new_date")
                work_type = st.selectbox("Work Type", ["Project", "Support"], key="_ts_work_type")
                hours = st.number_input("Hours", min_value=0.0, max_value=24.0,
                                        value=8.0, step=0.5, key="_ts_hours")

            with fc2:
                project_key = st.text_input("Project Key (Jira)", placeholder="SSE-526",
                                            key="_ts_proj_key")
                project_name = st.text_input("Project Name",
                                             placeholder="Changes to AR Aging Report",
                                             key="_ts_proj_name")
                task_desc = st.text_input("Task / Description",
                                          placeholder="Development, Testing, etc.",
                                          key="_ts_task")

            notes = st.text_input("Notes (optional)", key="_ts_notes")

            submitted = st.form_submit_button("Save Entry", use_container_width=True,
                                              type="primary")
            if submitted and hours > 0:
                connector = _get_connector()
                try:
                    err = connector.save_timesheet_entry({
                        "consultant_id": selected["id"],
                        "entry_date": new_date.isoformat(),
                        "project_key": project_key.strip() or None,
                        "project_name": project_name.strip() or None,
                        "task_description": task_desc.strip() or None,
                        "work_type": work_type,
                        "hours": hours,
                        "notes": notes.strip() or None,
                    })
                finally:
                    connector.close()

                if err:
                    st.error(err)
                else:
                    st.success(f"Saved {hours}h for {new_date.strftime('%b %d')}")
                    st.cache_data.clear()
                    st.rerun()


# ---------------------------------------------------------------------------
# Tab: Monthly Review
# ---------------------------------------------------------------------------

def _render_review_tab(consultants: list[dict]):
    """Monthly review — manager view of all timesheets."""

    today = date.today()
    col1, col2 = st.columns([2, 4])
    with col1:
        month_options = _month_options(today.year)
        selected_month = st.selectbox("Month", month_options,
                                      index=0, key="_review_month")

    connector = _get_connector()
    try:
        summary = connector.get_timesheet_summary(month=selected_month)
        entries = connector.read_timesheets(month=selected_month)
    finally:
        connector.close()

    if not summary:
        st.info(f"No timesheet data for {selected_month}.")
        return

    # --- KPI Summary ---
    total_hrs = sum(s["total_hours"] for s in summary)
    project_hrs = sum(s["project_hours"] for s in summary)
    support_hrs = sum(s["support_hours"] for s in summary)
    tm_cost = sum(s["tm_cost"] for s in summary)

    kc1, kc2, kc3, kc4 = st.columns(4)
    with kc1:
        kpi_card("Total Hours", f"{total_hrs:,.0f}", "navy")
    with kc2:
        kpi_card("Project Hours", f"{project_hrs:,.0f}", "navy")
    with kc3:
        kpi_card("Support Hours", f"{support_hrs:,.0f}", "navy")
    with kc4:
        kpi_card("T&M Cost", f"${tm_cost:,.0f}", "navy")

    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

    # --- Consultant Summary Table ---
    section_header("Consultant Summary")

    html = """<table style="width:100%; border-collapse:collapse; font-size:0.85rem;">
    <thead><tr style="border-bottom:2px solid #C5CDD8; color:#5A6A7E; text-transform:uppercase; font-size:0.75rem; letter-spacing:0.03em;">
        <th style="text-align:left; padding:0.4rem 0.5rem;">Consultant</th>
        <th style="text-align:left; padding:0.4rem 0.5rem;">Billing</th>
        <th style="text-align:right; padding:0.4rem 0.5rem;">Project Hrs</th>
        <th style="text-align:right; padding:0.4rem 0.5rem;">Support Hrs</th>
        <th style="text-align:right; padding:0.4rem 0.5rem;">Total Hrs</th>
        <th style="text-align:right; padding:0.4rem 0.5rem;">T&M Cost</th>
    </tr></thead><tbody>"""

    for s in summary:
        rate_str = f"${s['hourly_rate']:.0f}/hr" if s["hourly_rate"] > 0 else "—"
        billing = f"{s['billing_type']} {rate_str}" if s["hourly_rate"] > 0 else s["billing_type"]
        cost_str = f"${s['tm_cost']:,.0f}" if s["tm_cost"] > 0 else "—"

        html += f"""<tr style="border-bottom:1px solid #E8ECF1;">
            <td style="padding:0.45rem 0.5rem; font-weight:500;">{s['name']}</td>
            <td style="padding:0.45rem 0.5rem;">{billing}</td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">{s['project_hours']:.0f}</td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">{s['support_hours']:.0f}</td>
            <td style="padding:0.45rem 0.5rem; text-align:right; font-weight:600;">{s['total_hours']:.0f}</td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">{cost_str}</td>
        </tr>"""

    # Totals row
    html += f"""<tr style="border-top:2px solid #C5CDD8; font-weight:700;">
        <td style="padding:0.45rem 0.5rem;" colspan="2">TOTAL</td>
        <td style="padding:0.45rem 0.5rem; text-align:right;">{project_hrs:.0f}</td>
        <td style="padding:0.45rem 0.5rem; text-align:right;">{support_hrs:.0f}</td>
        <td style="padding:0.45rem 0.5rem; text-align:right;">{total_hrs:.0f}</td>
        <td style="padding:0.45rem 0.5rem; text-align:right;">${tm_cost:,.0f}</td>
    </tr>"""

    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)

    # --- Hours Distribution Chart ---
    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
    section_header("Hours by Consultant")

    chart_rows = []
    for s in summary:
        chart_rows.append({"Consultant": s["name"], "Type": "Project", "Hours": s["project_hours"]})
        chart_rows.append({"Consultant": s["name"], "Type": "Support", "Hours": s["support_hours"]})

    chart_df = pd.DataFrame(chart_rows)
    chart = alt.Chart(chart_df).mark_bar(
        cornerRadiusTopRight=4, cornerRadiusBottomRight=4
    ).encode(
        y=alt.Y("Consultant:N", title=None, sort="-x",
                axis=alt.Axis(labelFontSize=12)),
        x=alt.X("Hours:Q", title="Hours", stack="zero",
                axis=alt.Axis(labelFontSize=11)),
        color=alt.Color("Type:N", scale=alt.Scale(
            domain=["Project", "Support"],
            range=["#1B3A5C", "#8BA4C4"]
        ), legend=alt.Legend(orient="top", title=None)),
        tooltip=[
            alt.Tooltip("Consultant:N"),
            alt.Tooltip("Type:N"),
            alt.Tooltip("Hours:Q", format=".0f"),
        ],
    ).properties(height=max(len(summary) * 45, 200))

    st.altair_chart(chart, use_container_width=True)

    # --- Project breakdown ---
    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
    section_header("Hours by Project")

    project_hours = defaultdict(lambda: {"project": 0.0, "support": 0.0})
    for e in entries:
        key = e.get("project_key") or "General Support"
        name = e.get("project_name") or "General Support"
        label = f"{key}: {name}" if key != "General Support" else name
        wt = e.get("work_type", "Support")
        if wt == "Project":
            project_hours[label]["project"] += e["hours"]
        else:
            project_hours[label]["support"] += e["hours"]

    proj_rows = []
    for label, hrs in sorted(project_hours.items(), key=lambda x: -(x[1]["project"] + x[1]["support"])):
        total = hrs["project"] + hrs["support"]
        proj_rows.append({
            "Project": label[:60],
            "Project Hrs": hrs["project"],
            "Support Hrs": hrs["support"],
            "Total": total,
        })

    if proj_rows:
        proj_df = pd.DataFrame(proj_rows)
        st.dataframe(proj_df, hide_index=True, use_container_width=True,
                     column_config={
                         "Project Hrs": st.column_config.NumberColumn(format="%.0f"),
                         "Support Hrs": st.column_config.NumberColumn(format="%.0f"),
                         "Total": st.column_config.NumberColumn(format="%.0f"),
                     })


# ---------------------------------------------------------------------------
# Tab: Approvals
# ---------------------------------------------------------------------------

def _render_approvals_tab(consultants: list[dict]):
    """Monthly approval workflow."""

    today = date.today()
    month_options = _month_options(today.year)
    selected_month = st.selectbox("Month", month_options, index=0, key="_appr_month")

    connector = _get_connector()
    try:
        summary = connector.get_timesheet_summary(month=selected_month)
        approvals = connector.read_approvals(month=selected_month)
    finally:
        connector.close()

    if not summary:
        st.info(f"No timesheet data for {selected_month}.")
        return

    approval_map = {a["consultant_id"]: a for a in approvals}

    section_header(f"Approval Status — {selected_month}")

    html = """<table style="width:100%; border-collapse:collapse; font-size:0.85rem;">
    <thead><tr style="border-bottom:2px solid #C5CDD8; color:#5A6A7E; text-transform:uppercase; font-size:0.75rem;">
        <th style="text-align:left; padding:0.4rem 0.5rem;">Consultant</th>
        <th style="text-align:right; padding:0.4rem 0.5rem;">Hours</th>
        <th style="text-align:left; padding:0.4rem 0.5rem;">Status</th>
        <th style="text-align:left; padding:0.4rem 0.5rem;">Vendor Approval</th>
        <th style="text-align:left; padding:0.4rem 0.5rem;">ETE Approval</th>
    </tr></thead><tbody>"""

    status_colors = {
        "draft": "#6C757D", "submitted": "#F39C12", "approved": "#27AE60",
    }

    for s in summary:
        appr = approval_map.get(s["consultant_id"], {})
        status = appr.get("status", "draft")
        color = status_colors.get(status, "#6C757D")

        vendor_appr = "Approved" if appr.get("vendor_approved") else "Pending"
        vendor_by = appr.get("vendor_approved_by", "")
        ete_appr = "Approved" if appr.get("ete_approved") else "Pending"
        ete_by = appr.get("ete_approved_by", "")

        html += f"""<tr style="border-bottom:1px solid #E8ECF1;">
            <td style="padding:0.45rem 0.5rem; font-weight:500;">{s['name']}</td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">{s['total_hours']:.0f}</td>
            <td style="padding:0.45rem 0.5rem;"><span style="color:{color}; font-weight:600; text-transform:uppercase;">{status}</span></td>
            <td style="padding:0.45rem 0.5rem;">{vendor_appr}{f' ({vendor_by})' if vendor_by else ''}</td>
            <td style="padding:0.45rem 0.5rem;">{ete_appr}{f' ({ete_by})' if ete_by else ''}</td>
        </tr>"""

    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)

    # --- Approve All Button ---
    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

    pending = [s for s in summary if not approval_map.get(s["consultant_id"], {}).get("ete_approved")]
    if pending:
        bc1, bc2, bc3 = st.columns([2, 2, 2])
        with bc1:
            approver_name = st.text_input("Your Name", value="Brett Anderson",
                                          key="_appr_name")
        with bc2:
            st.markdown("<div style='height: 1.8rem'></div>", unsafe_allow_html=True)
            if st.button(f"Approve All ({len(pending)})", key="_appr_all",
                        use_container_width=True, type="primary"):
                connector = _get_connector()
                try:
                    for s in pending:
                        connector.save_approval({
                            "consultant_id": s["consultant_id"],
                            "month": selected_month,
                            "total_hours": s["total_hours"],
                            "status": "approved",
                            "vendor_approved": 1,
                            "vendor_approved_by": "Sarath Yeturu",
                            "vendor_approved_at": datetime.now().isoformat(),
                            "ete_approved": 1,
                            "ete_approved_by": approver_name,
                            "ete_approved_at": datetime.now().isoformat(),
                        })
                finally:
                    connector.close()
                st.success(f"Approved {len(pending)} timesheets for {selected_month}.")
                st.rerun()
    else:
        st.success(f"All timesheets approved for {selected_month}.")


# ---------------------------------------------------------------------------
# Tab: Invoices
# ---------------------------------------------------------------------------

def _render_invoices_tab():
    """Invoice tracking and reconciliation."""

    today = date.today()

    connector = _get_connector()
    try:
        invoices = connector.read_invoices(year=today.year)
        year_summary = connector.get_timesheet_summary(year=today.year)
    finally:
        connector.close()

    # --- KPIs ---
    total_invoiced = sum(i["total_amount"] for i in invoices)
    total_msa = sum(i["msa_amount"] for i in invoices)
    total_tm = sum(i["tm_amount"] for i in invoices)
    total_paid = sum(i["total_amount"] for i in invoices if i["paid"])

    kc1, kc2, kc3, kc4 = st.columns(4)
    with kc1:
        kpi_card(f"FY{today.year} Invoiced", f"${total_invoiced:,.0f}", "navy")
    with kc2:
        kpi_card("MSA Fees", f"${total_msa:,.0f}", "navy")
    with kc3:
        kpi_card("T&M Charges", f"${total_tm:,.0f}", "navy")
    with kc4:
        outstanding = total_invoiced - total_paid
        color = "red" if outstanding > 0 else "green"
        kpi_card("Outstanding", f"${outstanding:,.0f}", color)

    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

    # --- Invoice List ---
    section_header(f"FY{today.year} Invoices")

    if invoices:
        html = """<table style="width:100%; border-collapse:collapse; font-size:0.85rem;">
        <thead><tr style="border-bottom:2px solid #C5CDD8; color:#5A6A7E; text-transform:uppercase; font-size:0.75rem;">
            <th style="text-align:left; padding:0.4rem 0.5rem;">Month</th>
            <th style="text-align:left; padding:0.4rem 0.5rem;">Invoice #</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">MSA</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">T&M</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">Total</th>
            <th style="text-align:left; padding:0.4rem 0.5rem;">Status</th>
            <th style="text-align:left; padding:0.4rem 0.5rem;">Notes</th>
        </tr></thead><tbody>"""

        for inv in invoices:
            month_label = inv["month"]
            try:
                m_date = date.fromisoformat(inv["month"] + "-01")
                month_label = m_date.strftime("%B %Y")
            except Exception:
                pass

            paid_badge = '<span style="color:#27AE60; font-weight:600;">PAID</span>' if inv["paid"] else '<span style="color:#E74C3C; font-weight:600;">UNPAID</span>'
            notes = (inv.get("notes") or "")[:60]

            html += f"""<tr style="border-bottom:1px solid #E8ECF1;">
                <td style="padding:0.45rem 0.5rem; font-weight:500;">{month_label}</td>
                <td style="padding:0.45rem 0.5rem;">{inv.get('invoice_number') or '—'}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right;">${inv['msa_amount']:,.0f}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right;">${inv['tm_amount']:,.0f}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right; font-weight:600;">${inv['total_amount']:,.0f}</td>
                <td style="padding:0.45rem 0.5rem;">{paid_badge}</td>
                <td style="padding:0.45rem 0.5rem; font-size:0.78rem; color:#5A6A7E;">{notes}</td>
            </tr>"""

        html += "</tbody></table>"
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.info("No invoices recorded yet.")

    # --- Add Invoice ---
    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
    with st.expander("Record New Invoice"):
        with st.form("invoice_form", clear_on_submit=True):
            ic1, ic2 = st.columns(2)
            with ic1:
                inv_month = st.text_input("Month (YYYY-MM)", placeholder="2026-04",
                                          key="_inv_month")
                msa_amt = st.number_input("MSA Amount ($)", value=50000, step=1000,
                                          key="_inv_msa")
                tm_amt = st.number_input("T&M Amount ($)", value=0, step=100,
                                         key="_inv_tm")
            with ic2:
                inv_num = st.text_input("Invoice Number", key="_inv_num")
                recv_date = st.date_input("Received Date", value=date.today(),
                                          key="_inv_recv")
                inv_notes = st.text_input("Notes", key="_inv_notes")

            if st.form_submit_button("Save Invoice", use_container_width=True):
                if inv_month and len(inv_month) == 7:
                    connector = _get_connector()
                    try:
                        err = connector.save_invoice({
                            "month": inv_month,
                            "msa_amount": msa_amt,
                            "tm_amount": tm_amt,
                            "total_amount": msa_amt + tm_amt,
                            "invoice_number": inv_num or None,
                            "received_date": recv_date.isoformat(),
                            "paid": 0,
                            "notes": inv_notes or None,
                        })
                    finally:
                        connector.close()
                    if err:
                        st.error(err)
                    else:
                        st.success("Invoice recorded.")
                        st.rerun()
                else:
                    st.error("Enter month in YYYY-MM format.")


# ---------------------------------------------------------------------------
# Tab: Approved Work
# ---------------------------------------------------------------------------

def _render_approved_work_tab():
    """Approved Work register — what work has been authorized."""

    connector = _get_connector()
    try:
        work_items = connector.read_approved_work()
    finally:
        connector.close()

    if work_items:
        # Summary KPIs
        n_capex = sum(1 for w in work_items if w.get("work_classification") == "CapEx")
        n_support = sum(1 for w in work_items if w.get("work_classification") == "Support")
        n_pending = sum(1 for w in work_items if not w.get("approved_date"))

        kc1, kc2, kc3, kc4 = st.columns(4)
        with kc1:
            kpi_card("Total Items", len(work_items), "navy")
        with kc2:
            kpi_card("CapEx", n_capex, "navy")
        with kc3:
            kpi_card("Support", n_support, "navy")
        with kc4:
            color = "yellow" if n_pending > 0 else "green"
            kpi_card("Pending Approval", n_pending, color)

        st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

        # Table
        html = """<table style="width:100%; border-collapse:collapse; font-size:0.85rem;">
        <thead><tr style="border-bottom:2px solid #C5CDD8; color:#5A6A7E; text-transform:uppercase; font-size:0.75rem;">
            <th style="text-align:left; padding:0.4rem 0.5rem;">Jira Key</th>
            <th style="text-align:left; padding:0.4rem 0.5rem;">Title</th>
            <th style="text-align:left; padding:0.4rem 0.5rem;">Type</th>
            <th style="text-align:left; padding:0.4rem 0.5rem;">Classification</th>
            <th style="text-align:left; padding:0.4rem 0.5rem;">Approved</th>
            <th style="text-align:left; padding:0.4rem 0.5rem;">By</th>
        </tr></thead><tbody>"""

        for w in work_items:
            jira_key = w.get("jira_key") or "—"
            jira_url = f"https://etedevops.atlassian.net/browse/{jira_key}"
            jira_link = f'<a href="{jira_url}" target="_blank" style="color:#1565C0; text-decoration:none; font-weight:500;">{jira_key}</a>' if jira_key != "—" else "—"

            title = (w.get("title") or "")[:55]
            wtype = w.get("work_type") or "—"
            classification = w.get("work_classification") or "—"
            cls_color = "#1565C0" if classification == "CapEx" else "#5A6A7E"

            approved_date = w.get("approved_date")
            if approved_date:
                try:
                    approved_str = date.fromisoformat(approved_date).strftime("%b %d, %Y")
                except Exception:
                    approved_str = approved_date
            else:
                approved_str = '<span style="color:#E74C3C; font-weight:600;">PENDING</span>'

            approver = w.get("approver") or "—"
            notes = w.get("notes") or ""

            html += f"""<tr style="border-bottom:1px solid #E8ECF1;" title="{notes}">
                <td style="padding:0.45rem 0.5rem;">{jira_link}</td>
                <td style="padding:0.45rem 0.5rem;">{title}</td>
                <td style="padding:0.45rem 0.5rem;">{wtype}</td>
                <td style="padding:0.45rem 0.5rem; color:{cls_color}; font-weight:500;">{classification}</td>
                <td style="padding:0.45rem 0.5rem;">{approved_str}</td>
                <td style="padding:0.45rem 0.5rem;">{approver}</td>
            </tr>"""

        html += "</tbody></table>"
        st.markdown(html, unsafe_allow_html=True)

    else:
        st.info("No approved work items. Import data or add items manually.")

    # --- Add Work Item ---
    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
    with st.expander("Add Work Authorization"):
        with st.form("aw_form", clear_on_submit=True):
            ac1, ac2 = st.columns(2)
            with ac1:
                jira_key = st.text_input("Jira Key", placeholder="SSE-526", key="_aw_jira")
                title = st.text_input("Title / Description", key="_aw_title")
                work_type = st.selectbox("Work Type",
                                         ["Project", "Enhancement", "Break/Fix", "Bug"],
                                         key="_aw_type")
            with ac2:
                classification = st.selectbox("Classification", ["CapEx", "Support"],
                                              key="_aw_class")
                approver = st.text_input("Approver", value="Brett Anderson",
                                         key="_aw_approver")
                approved_date = st.date_input("Approved Date", value=date.today(),
                                              key="_aw_date")

            notes = st.text_input("Notes", key="_aw_notes")

            if st.form_submit_button("Save", use_container_width=True):
                if title:
                    connector = _get_connector()
                    try:
                        err = connector.save_approved_work({
                            "jira_key": jira_key.strip() or None,
                            "title": title.strip(),
                            "work_type": work_type,
                            "work_classification": classification,
                            "approved_date": approved_date.isoformat(),
                            "approver": approver.strip() or None,
                            "notes": notes.strip() or None,
                        })
                    finally:
                        connector.close()
                    if err:
                        st.error(err)
                    else:
                        st.success("Work item saved.")
                        st.rerun()
                else:
                    st.error("Title is required.")


# ---------------------------------------------------------------------------
# Main Render
# ---------------------------------------------------------------------------

def render(data: dict, utilization: dict, person_demand: list):
    """Render the Vendor Timesheets page."""

    if not is_finance_user():
        st.warning("You do not have permission to view timesheet data.")
        return

    st.markdown(f"""
    <div style="font-size:1.6rem; font-weight:700; color:{NAVY}; margin-bottom:0.25rem;">
        Vendor Timesheets
    </div>
    <div style="font-size:0.85rem; color:#5A6A7E; margin-bottom:1rem;">
        Synnergie team time tracking, approvals, and invoice management
    </div>
    """, unsafe_allow_html=True)

    # Load consultants once
    connector = _get_connector()
    try:
        consultants = connector.read_vendor_consultants()
    finally:
        connector.close()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Time Entry", "Monthly Review", "Approvals",
        "Invoices", "Approved Work",
    ])

    with tab1:
        _render_entry_tab(consultants)

    with tab2:
        _render_review_tab(consultants)

    with tab3:
        _render_approvals_tab(consultants)

    with tab4:
        _render_invoices_tab()

    with tab5:
        _render_approved_work_tab()
