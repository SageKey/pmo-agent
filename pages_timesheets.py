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
        sorted_entries = sorted(week_entries, key=lambda x: (x["entry_date"], x.get("project_key", "")))
        total_hrs = sum(e["hours"] for e in week_entries)
        project_hrs = sum(e["hours"] for e in week_entries if e.get("work_type") == "Project")
        support_hrs = sum(e["hours"] for e in week_entries if e.get("work_type") == "Support")

        # Week summary KPIs
        kc1, kc2, kc3 = st.columns(3)
        with kc1:
            kpi_card("Week Total", f"{total_hrs:.0f}h", "navy")
        with kc2:
            kpi_card("Project", f"{project_hrs:.0f}h", "navy")
        with kc3:
            kpi_card("Support", f"{support_hrs:.0f}h", "navy")

        st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)

        # Interactive entries table with edit/delete
        editing_id = st.session_state.get("_ts_editing_id")

        for e in sorted_entries:
            d = date.fromisoformat(e["entry_date"])
            eid = e["id"]
            proj_label = e.get("project_key") or "—"
            proj_name = (e.get("project_name") or "General Support")[:40]
            task = (e.get("task_description") or "")[:45]
            wtype = e.get("work_type", "Support")
            hrs = e["hours"]

            if editing_id == eid:
                # --- Inline Edit Mode ---
                with st.container():
                    st.markdown(f"""<div style="font-size:0.78rem; color:#5A6A7E; margin-bottom:0.25rem; font-weight:600;">
                        Editing: {d.strftime('%a %b %d')} — {proj_label}
                    </div>""", unsafe_allow_html=True)
                    with st.form(f"edit_{eid}", clear_on_submit=False):
                        ec1, ec2 = st.columns(2)
                        with ec1:
                            edit_date = st.date_input("Date", value=d, key=f"_ed_date_{eid}")
                            edit_type = st.selectbox("Work Type", ["Project", "Support"],
                                                     index=0 if wtype == "Project" else 1,
                                                     key=f"_ed_type_{eid}")
                            edit_hours = st.number_input("Hours", min_value=0.0, max_value=24.0,
                                                         value=float(hrs), step=0.5,
                                                         key=f"_ed_hrs_{eid}")
                        with ec2:
                            edit_pkey = st.text_input("Project Key",
                                                      value=e.get("project_key") or "",
                                                      key=f"_ed_pkey_{eid}")
                            edit_pname = st.text_input("Project Name",
                                                       value=e.get("project_name") or "",
                                                       key=f"_ed_pname_{eid}")
                            edit_task = st.text_input("Task",
                                                      value=e.get("task_description") or "",
                                                      key=f"_ed_task_{eid}")
                        edit_notes = st.text_input("Notes",
                                                    value=e.get("notes") or "",
                                                    key=f"_ed_notes_{eid}")

                        sc1, sc2 = st.columns(2)
                        with sc1:
                            save = st.form_submit_button("Save Changes", use_container_width=True,
                                                         type="primary")
                        with sc2:
                            cancel = st.form_submit_button("Cancel", use_container_width=True)

                        if save:
                            connector = _get_connector()
                            try:
                                err = connector.save_timesheet_entry({
                                    "id": eid,
                                    "consultant_id": selected["id"],
                                    "entry_date": edit_date.isoformat(),
                                    "project_key": edit_pkey.strip() or None,
                                    "project_name": edit_pname.strip() or None,
                                    "task_description": edit_task.strip() or None,
                                    "work_type": edit_type,
                                    "hours": edit_hours,
                                    "notes": edit_notes.strip() or None,
                                })
                            finally:
                                connector.close()
                            if err:
                                st.error(err)
                            else:
                                st.session_state["_ts_editing_id"] = None
                                st.cache_data.clear()
                                st.rerun()
                        if cancel:
                            st.session_state["_ts_editing_id"] = None
                            st.rerun()
            else:
                # --- Display Row ---
                rc1, rc2, rc3, rc4, rc5, rc6, rc7 = st.columns([1.3, 1, 2.2, 2.5, 0.8, 0.6, 0.6])
                with rc1:
                    st.markdown(f"<div style='font-size:0.85rem; padding:0.3rem 0; font-weight:500;'>{d.strftime('%a %b %d')}</div>", unsafe_allow_html=True)
                with rc2:
                    st.markdown(f"<div style='font-size:0.85rem; padding:0.3rem 0; color:#1565C0;'>{proj_label}</div>", unsafe_allow_html=True)
                with rc3:
                    st.markdown(f"<div style='font-size:0.83rem; padding:0.3rem 0; color:#5A6A7E;'>{proj_name}</div>", unsafe_allow_html=True)
                with rc4:
                    st.markdown(f"<div style='font-size:0.83rem; padding:0.3rem 0; color:#5A6A7E;'>{task}</div>", unsafe_allow_html=True)
                with rc5:
                    st.markdown(f"<div style='font-size:0.85rem; padding:0.3rem 0; font-weight:600;'>{hrs:.1f}h</div>", unsafe_allow_html=True)
                with rc6:
                    if st.button("Edit", key=f"_edit_{eid}", use_container_width=True):
                        st.session_state["_ts_editing_id"] = eid
                        st.rerun()
                with rc7:
                    if st.button("Del", key=f"_del_{eid}", use_container_width=True):
                        st.session_state["_ts_confirm_delete"] = eid
                        st.rerun()

                # Delete confirmation
                if st.session_state.get("_ts_confirm_delete") == eid:
                    st.warning(f"Delete {d.strftime('%b %d')} — {proj_label} ({hrs}h)?")
                    dc1, dc2, dc3 = st.columns([1, 1, 4])
                    with dc1:
                        if st.button("Yes, delete", key=f"_del_yes_{eid}",
                                     use_container_width=True, type="primary"):
                            connector = _get_connector()
                            try:
                                connector.delete_timesheet_entry(eid)
                            finally:
                                connector.close()
                            st.session_state.pop("_ts_confirm_delete", None)
                            st.cache_data.clear()
                            st.rerun()
                    with dc2:
                        if st.button("Cancel", key=f"_del_no_{eid}",
                                     use_container_width=True):
                            st.session_state.pop("_ts_confirm_delete", None)
                            st.rerun()

        # Divider before add form
        st.markdown("<hr style='border:none; border-top:1px solid #E8ECF1; margin:0.75rem 0;'>",
                    unsafe_allow_html=True)

    else:
        st.caption("No entries for this week yet.")

    # --- Add New Entry Form ---
    st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
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

    MSA_MONTHLY_FEE = 50000.0
    BLENDED_RATE = 65.0

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

    # --- Compute MSA vs T&M splits ---
    total_hrs = sum(s["total_hours"] for s in summary)
    project_hrs = sum(s["project_hours"] for s in summary)
    support_hrs = sum(s["support_hours"] for s in summary)

    msa_hrs = sum(s["total_hours"] for s in summary if s["billing_type"] == "MSA")
    tm_hrs = sum(s["total_hours"] for s in summary if s["billing_type"] == "T&M")
    tm_cost = sum(s["total_hours"] * s["hourly_rate"]
                  for s in summary if s["billing_type"] == "T&M")
    work_value = total_hrs * BLENDED_RATE
    total_cost = MSA_MONTHLY_FEE + tm_cost
    msa_effective_rate = MSA_MONTHLY_FEE / msa_hrs if msa_hrs > 0 else 0

    # --- Top-level KPIs ---
    kc1, kc2, kc3, kc4, kc5 = st.columns(5)
    with kc1:
        kpi_card("Total Hours", f"{total_hrs:,.0f}", "navy")
    with kc2:
        kpi_card("MSA Hours", f"{msa_hrs:,.0f}", "navy")
    with kc3:
        kpi_card("T&M Hours", f"{tm_hrs:,.0f}", "navy")
    with kc4:
        kpi_card("T&M Cost", f"${tm_cost:,.0f}", "navy")
    with kc5:
        kpi_card("Total Cost", f"${total_cost:,.0f}", "navy")

    st.markdown("<div style='height: 1.25rem'></div>", unsafe_allow_html=True)

    # ==================================================================
    # MSA Utilization Analysis
    # ==================================================================
    section_header("MSA Utilization")

    msa_members = [s for s in summary if s["billing_type"] == "MSA"]
    msa_work_value = msa_hrs * BLENDED_RATE

    mu1, mu2, mu3, mu4 = st.columns(4)
    with mu1:
        kpi_card("MSA Fee", f"${MSA_MONTHLY_FEE:,.0f}", "navy")
    with mu2:
        kpi_card("Work Value", f"${msa_work_value:,.0f}",
                 "green" if msa_work_value >= MSA_MONTHLY_FEE else "red")
    with mu3:
        roi_pct = (msa_work_value / MSA_MONTHLY_FEE * 100) if MSA_MONTHLY_FEE > 0 else 0
        color = "green" if roi_pct >= 100 else ("yellow" if roi_pct >= 80 else "red")
        kpi_card("MSA ROI", f"{roi_pct:.0f}%", color)
    with mu4:
        color = "green" if msa_effective_rate <= BLENDED_RATE else ("yellow" if msa_effective_rate <= 80 else "red")
        kpi_card("Effective Rate", f"${msa_effective_rate:.0f}/hr", color)

    # MSA insight text
    if msa_work_value >= MSA_MONTHLY_FEE:
        delta = msa_work_value - MSA_MONTHLY_FEE
        st.markdown(f"""<div style="font-size:0.85rem; color:#27AE60; margin:0.5rem 0 0.75rem 0;">
            The MSA delivered <strong>${msa_work_value:,.0f}</strong> of work value
            for a <strong>${MSA_MONTHLY_FEE:,.0f}</strong> fee —
            saving <strong>${delta:,.0f}</strong> vs. hourly billing at ${BLENDED_RATE:.0f}/hr.
        </div>""", unsafe_allow_html=True)
    else:
        delta = MSA_MONTHLY_FEE - msa_work_value
        st.markdown(f"""<div style="font-size:0.85rem; color:#E74C3C; margin:0.5rem 0 0.75rem 0;">
            MSA work value (<strong>${msa_work_value:,.0f}</strong>) is below the
            <strong>${MSA_MONTHLY_FEE:,.0f}</strong> fee — <strong>${delta:,.0f}</strong>
            gap. Consider shifting more work to MSA resources.
        </div>""", unsafe_allow_html=True)

    # MSA member breakdown
    if msa_members:
        html = """<table style="width:100%; border-collapse:collapse; font-size:0.85rem;">
        <thead><tr style="border-bottom:2px solid #C5CDD8; color:#5A6A7E; text-transform:uppercase; font-size:0.75rem;">
            <th style="text-align:left; padding:0.4rem 0.5rem;">MSA Consultant</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">Project Hrs</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">Support Hrs</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">Total Hrs</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">Work Value</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">Share of MSA</th>
        </tr></thead><tbody>"""

        for s in msa_members:
            wv = s["total_hours"] * BLENDED_RATE
            share = (s["total_hours"] / msa_hrs * 100) if msa_hrs > 0 else 0
            html += f"""<tr style="border-bottom:1px solid #E8ECF1;">
                <td style="padding:0.45rem 0.5rem; font-weight:500;">{s['name']}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right;">{s['project_hours']:.0f}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right;">{s['support_hours']:.0f}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right; font-weight:600;">{s['total_hours']:.0f}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right;">${wv:,.0f}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right;">{share:.0f}%</td>
            </tr>"""

        html += f"""<tr style="border-top:2px solid #C5CDD8; font-weight:700;">
            <td style="padding:0.45rem 0.5rem;">MSA TOTAL</td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">{sum(s['project_hours'] for s in msa_members):.0f}</td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">{sum(s['support_hours'] for s in msa_members):.0f}</td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">{msa_hrs:.0f}</td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">${msa_work_value:,.0f}</td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">100%</td>
        </tr>"""

        html += "</tbody></table>"
        st.markdown(html, unsafe_allow_html=True)

    st.markdown("<div style='height: 1.25rem'></div>", unsafe_allow_html=True)

    # ==================================================================
    # T&M Cost Detail
    # ==================================================================
    section_header("T&M Cost Detail")

    tm_members = [s for s in summary if s["billing_type"] == "T&M"]
    if tm_members:
        html = """<table style="width:100%; border-collapse:collapse; font-size:0.85rem;">
        <thead><tr style="border-bottom:2px solid #C5CDD8; color:#5A6A7E; text-transform:uppercase; font-size:0.75rem;">
            <th style="text-align:left; padding:0.4rem 0.5rem;">T&M Consultant</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">Rate</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">Project Hrs</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">Support Hrs</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">Total Hrs</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">Cost</th>
        </tr></thead><tbody>"""

        for s in tm_members:
            cost = s["total_hours"] * s["hourly_rate"]
            html += f"""<tr style="border-bottom:1px solid #E8ECF1;">
                <td style="padding:0.45rem 0.5rem; font-weight:500;">{s['name']}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right;">${s['hourly_rate']:.0f}/hr</td>
                <td style="padding:0.45rem 0.5rem; text-align:right;">{s['project_hours']:.0f}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right;">{s['support_hours']:.0f}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right; font-weight:600;">{s['total_hours']:.0f}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right; font-weight:600;">${cost:,.0f}</td>
            </tr>"""

        html += f"""<tr style="border-top:2px solid #C5CDD8; font-weight:700;">
            <td style="padding:0.45rem 0.5rem;" colspan="2">T&M TOTAL</td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">{sum(s['project_hours'] for s in tm_members):.0f}</td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">{sum(s['support_hours'] for s in tm_members):.0f}</td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">{tm_hrs:.0f}</td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">${tm_cost:,.0f}</td>
        </tr>"""

        html += "</tbody></table>"
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.caption("No T&M hours this month.")

    # --- Monthly Cost Summary Bar ---
    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
    section_header("Monthly Cost Breakdown")

    msa_frac = MSA_MONTHLY_FEE / total_cost if total_cost > 0 else 0
    tm_frac = tm_cost / total_cost if total_cost > 0 else 0
    st.markdown(f"""
    <div style="position: relative; background: #E8ECF1; border-radius: 8px; height: 32px; overflow: hidden; margin-bottom: 0.25rem;">
        <div style="position: absolute; top: 0; left: 0; height: 100%;
                    width: {msa_frac*100:.1f}%; background: #1B3A5C;
                    border-radius: 8px 0 0 8px;"></div>
        <div style="position: absolute; top: 0; left: {msa_frac*100:.1f}%; height: 100%;
                    width: {tm_frac*100:.1f}%; background: #4A90D9;
                    border-radius: 0 8px 8px 0;"></div>
    </div>
    <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #5A6A7E; margin-top: 0.25rem;">
        <span><span style="color:#1B3A5C;">&#9632;</span> MSA: ${MSA_MONTHLY_FEE:,.0f} ({msa_frac*100:.0f}%)</span>
        <span><span style="color:#4A90D9;">&#9632;</span> T&M: ${tm_cost:,.0f} ({tm_frac*100:.0f}%)</span>
        <span>Total: ${total_cost:,.0f}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 1.25rem'></div>", unsafe_allow_html=True)

    # --- Hours Distribution Chart ---
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

    # --- Project breakdown with ETE mapping ---
    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
    section_header("Hours by Project")

    # Load SSE → ETE mapping lookup
    connector = _get_connector()
    try:
        mapping_lookup = connector.get_mapping_lookup()
    finally:
        connector.close()

    project_hours = defaultdict(lambda: {"project": 0.0, "support": 0.0, "ete": ""})
    for e in entries:
        key = e.get("project_key") or "General Support"
        name = e.get("project_name") or "General Support"
        label = f"{key}: {name}" if key != "General Support" else name
        wt = e.get("work_type", "Support")
        if wt == "Project":
            project_hours[label]["project"] += e["hours"]
        else:
            project_hours[label]["support"] += e["hours"]
        # Attach ETE mapping
        if key in mapping_lookup:
            m = mapping_lookup[key]
            project_hours[label]["ete"] = f"{m['ete_project_id']}: {m['ete_project_name']}"

    proj_rows = []
    for label, hrs in sorted(project_hours.items(), key=lambda x: -(x[1]["project"] + x[1]["support"])):
        total = hrs["project"] + hrs["support"]
        proj_rows.append({
            "SSE Task": label[:50],
            "ETE Project": hrs["ete"] or "Unmapped",
            "Project Hrs": hrs["project"],
            "Support Hrs": hrs["support"],
            "Total": total,
        })

    if proj_rows:
        proj_df = pd.DataFrame(proj_rows)
        n_unmapped = sum(1 for r in proj_rows if r["ETE Project"] == "Unmapped")
        if n_unmapped > 0:
            st.markdown(f"""<div style="font-size:0.83rem; color:#5A6A7E; margin-bottom:0.5rem;
                padding:0.5rem 0.75rem; background:#FFF8E1; border-left:3px solid #F39C12; border-radius:4px;">
                <strong>{n_unmapped}</strong> SSE task(s) not yet mapped to an ETE project.
                Use the <strong>Project Mapping</strong> tab to link them.
            </div>""", unsafe_allow_html=True)

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
    """Invoice tracking with reconciliation against timesheets."""

    MSA_MONTHLY_FEE = 50000.0
    today = date.today()

    connector = _get_connector()
    try:
        invoices = connector.read_invoices(year=today.year)
        year_summary = connector.get_timesheet_summary(year=today.year)
    finally:
        connector.close()

    # --- YTD KPIs ---
    total_invoiced = sum(i["total_amount"] for i in invoices)
    total_msa = sum(i["msa_amount"] for i in invoices)
    total_tm_invoiced = sum(i["tm_amount"] for i in invoices)
    total_paid = sum(i["total_amount"] for i in invoices if i["paid"])
    outstanding = total_invoiced - total_paid

    kc1, kc2, kc3, kc4 = st.columns(4)
    with kc1:
        kpi_card(f"FY{today.year} Invoiced", f"${total_invoiced:,.0f}", "navy")
    with kc2:
        kpi_card("MSA Fees", f"${total_msa:,.0f}", "navy")
    with kc3:
        kpi_card("T&M Invoiced", f"${total_tm_invoiced:,.0f}", "navy")
    with kc4:
        color = "red" if outstanding > 0 else "green"
        kpi_card("Outstanding", f"${outstanding:,.0f}", color)

    st.markdown("<div style='height: 1.25rem'></div>", unsafe_allow_html=True)

    # ==================================================================
    # Invoice Reconciliation
    # ==================================================================
    section_header(f"FY{today.year} Invoice Reconciliation")

    if invoices:
        # Build per-month timesheet T&M totals for comparison
        month_ts_tm = {}
        for inv in invoices:
            m = inv["month"]
            connector = _get_connector()
            try:
                m_summary = connector.get_timesheet_summary(month=m)
            finally:
                connector.close()
            calc_tm = sum(s["total_hours"] * s["hourly_rate"]
                          for s in m_summary if s["billing_type"] == "T&M")
            calc_hrs = sum(s["total_hours"] for s in m_summary if s["billing_type"] == "T&M")
            month_ts_tm[m] = {"calc_tm": calc_tm, "calc_hrs": calc_hrs, "detail": m_summary}

        # Reconciliation table
        html = """<table style="width:100%; border-collapse:collapse; font-size:0.85rem;">
        <thead><tr style="border-bottom:2px solid #C5CDD8; color:#5A6A7E; text-transform:uppercase; font-size:0.75rem;">
            <th style="text-align:left; padding:0.4rem 0.5rem;">Month</th>
            <th style="text-align:left; padding:0.4rem 0.5rem;">Invoice #</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">MSA</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">T&M Invoiced</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">T&M Calculated</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">Variance</th>
            <th style="text-align:right; padding:0.4rem 0.5rem;">Total</th>
            <th style="text-align:left; padding:0.4rem 0.5rem;">Status</th>
        </tr></thead><tbody>"""

        total_calc_tm = 0
        total_variance = 0

        for inv in invoices:
            m = inv["month"]
            try:
                m_date = date.fromisoformat(m + "-01")
                month_label = m_date.strftime("%B %Y")
            except Exception:
                month_label = m

            ts_data = month_ts_tm.get(m, {"calc_tm": 0, "calc_hrs": 0})
            calc_tm = ts_data["calc_tm"]
            variance = inv["tm_amount"] - calc_tm
            total_calc_tm += calc_tm
            total_variance += variance

            # Variance coloring
            if abs(variance) < 1:
                var_color = "#27AE60"
                var_icon = "&#10003;"
            elif abs(variance) <= 500:
                var_color = "#F39C12"
                var_icon = "&#9888;"
            else:
                var_color = "#E74C3C"
                var_icon = "&#9888;"

            paid_badge = '<span style="color:#27AE60; font-weight:600;">PAID</span>' if inv["paid"] else '<span style="color:#E74C3C; font-weight:600;">UNPAID</span>'

            var_str = f"${variance:+,.0f}" if variance != 0 else "$0"

            html += f"""<tr style="border-bottom:1px solid #E8ECF1;">
                <td style="padding:0.45rem 0.5rem; font-weight:500;">{month_label}</td>
                <td style="padding:0.45rem 0.5rem;">{inv.get('invoice_number') or '—'}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right;">${inv['msa_amount']:,.0f}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right;">${inv['tm_amount']:,.0f}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right;">${calc_tm:,.0f}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right; color:{var_color}; font-weight:600;">{var_icon} {var_str}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right; font-weight:600;">${inv['total_amount']:,.0f}</td>
                <td style="padding:0.45rem 0.5rem;">{paid_badge}</td>
            </tr>"""

        # Totals row
        total_var_color = "#27AE60" if abs(total_variance) < 1 else ("#F39C12" if abs(total_variance) <= 500 else "#E74C3C")
        total_var_str = f"${total_variance:+,.0f}" if total_variance != 0 else "$0"
        html += f"""<tr style="border-top:2px solid #C5CDD8; font-weight:700;">
            <td style="padding:0.45rem 0.5rem;" colspan="2">YTD TOTAL</td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">${total_msa:,.0f}</td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">${total_tm_invoiced:,.0f}</td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">${total_calc_tm:,.0f}</td>
            <td style="padding:0.45rem 0.5rem; text-align:right; color:{total_var_color};">{total_var_str}</td>
            <td style="padding:0.45rem 0.5rem; text-align:right;">${total_invoiced:,.0f}</td>
            <td></td>
        </tr>"""

        html += "</tbody></table>"
        st.markdown(html, unsafe_allow_html=True)

        # --- Per-consultant drill-down for the most recent invoice ---
        st.markdown("<div style='height: 1.25rem'></div>", unsafe_allow_html=True)
        latest = invoices[0]
        latest_m = latest["month"]
        try:
            latest_label = date.fromisoformat(latest_m + "-01").strftime("%B %Y")
        except Exception:
            latest_label = latest_m

        ts_detail = month_ts_tm.get(latest_m, {}).get("detail", [])
        tm_detail = [s for s in ts_detail if s["billing_type"] == "T&M"]

        if tm_detail:
            section_header(f"T&M Detail — {latest_label}")

            html = """<table style="width:100%; border-collapse:collapse; font-size:0.85rem;">
            <thead><tr style="border-bottom:2px solid #C5CDD8; color:#5A6A7E; text-transform:uppercase; font-size:0.75rem;">
                <th style="text-align:left; padding:0.4rem 0.5rem;">Consultant</th>
                <th style="text-align:right; padding:0.4rem 0.5rem;">Rate</th>
                <th style="text-align:right; padding:0.4rem 0.5rem;">Hours</th>
                <th style="text-align:right; padding:0.4rem 0.5rem;">Calculated Cost</th>
            </tr></thead><tbody>"""

            detail_total_hrs = 0
            detail_total_cost = 0
            for s in tm_detail:
                cost = s["total_hours"] * s["hourly_rate"]
                detail_total_hrs += s["total_hours"]
                detail_total_cost += cost
                html += f"""<tr style="border-bottom:1px solid #E8ECF1;">
                    <td style="padding:0.45rem 0.5rem; font-weight:500;">{s['name']}</td>
                    <td style="padding:0.45rem 0.5rem; text-align:right;">${s['hourly_rate']:.0f}/hr</td>
                    <td style="padding:0.45rem 0.5rem; text-align:right;">{s['total_hours']:.0f}</td>
                    <td style="padding:0.45rem 0.5rem; text-align:right; font-weight:600;">${cost:,.0f}</td>
                </tr>"""

            variance = latest["tm_amount"] - detail_total_cost
            var_color = "#27AE60" if abs(variance) < 1 else "#E74C3C"
            var_str = f"${variance:+,.0f}" if variance != 0 else "$0"

            html += f"""<tr style="border-top:2px solid #C5CDD8; font-weight:700;">
                <td style="padding:0.45rem 0.5rem;" colspan="2">T&M TOTAL</td>
                <td style="padding:0.45rem 0.5rem; text-align:right;">{detail_total_hrs:.0f}</td>
                <td style="padding:0.45rem 0.5rem; text-align:right;">${detail_total_cost:,.0f}</td>
            </tr>
            <tr style="font-weight:700;">
                <td style="padding:0.45rem 0.5rem;" colspan="3">Invoice T&M Amount</td>
                <td style="padding:0.45rem 0.5rem; text-align:right;">${latest['tm_amount']:,.0f}</td>
            </tr>
            <tr style="font-weight:700;">
                <td style="padding:0.45rem 0.5rem; color:{var_color};" colspan="3">Variance</td>
                <td style="padding:0.45rem 0.5rem; text-align:right; color:{var_color};">{var_str}</td>
            </tr>"""

            html += "</tbody></table>"
            st.markdown(html, unsafe_allow_html=True)

            if abs(variance) > 0:
                st.markdown(f"""<div style="font-size:0.83rem; color:#5A6A7E; margin-top:0.5rem; padding:0.5rem 0.75rem; background:#FFF8E1; border-left:3px solid #F39C12; border-radius:4px;">
                    Variance of <strong>{var_str}</strong> between invoice and timesheets.
                    Verify consultant hours and rates match the invoice line items.
                </div>""", unsafe_allow_html=True)

    else:
        st.info("No invoices recorded yet. Add an invoice to begin reconciliation.")

    # --- Add Invoice ---
    st.markdown("<div style='height: 1.25rem'></div>", unsafe_allow_html=True)
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
# Tab: Project Mapping (SSE → ETE)
# ---------------------------------------------------------------------------

def _render_mapping_tab(data: dict):
    """SSE → ETE project mapping management."""

    connector = _get_connector()
    try:
        mappings = connector.read_project_mappings()
        unmapped = connector.get_unmapped_sse_keys()
        projects = connector.read_portfolio()
    finally:
        connector.close()

    # ETE project options for dropdowns
    ete_options = [""] + [f"{p.id}: {p.name}" for p in sorted(projects, key=lambda p: p.id)]
    ete_id_map = {f"{p.id}: {p.name}": p.id for p in projects}

    # --- Summary KPIs ---
    total_sse = len(mappings) + len(unmapped)
    n_mapped = len(mappings)
    n_unmapped = len(unmapped)
    unmapped_hrs = sum(u["total_hours"] for u in unmapped)
    coverage_pct = (n_mapped / total_sse * 100) if total_sse > 0 else 0

    kc1, kc2, kc3, kc4 = st.columns(4)
    with kc1:
        kpi_card("SSE Tasks", total_sse, "navy")
    with kc2:
        color = "green" if coverage_pct >= 80 else ("yellow" if coverage_pct >= 50 else "red")
        kpi_card("Mapped", f"{n_mapped} ({coverage_pct:.0f}%)", color)
    with kc3:
        color = "green" if n_unmapped == 0 else ("yellow" if n_unmapped <= 5 else "red")
        kpi_card("Unmapped", n_unmapped, color)
    with kc4:
        kpi_card("Unmapped Hours", f"{unmapped_hrs:,.0f}h", "navy")

    st.markdown("<div style='height: 1.25rem'></div>", unsafe_allow_html=True)

    # ==================================================================
    # Unmapped SSE Keys — Priority Action
    # ==================================================================
    if unmapped:
        section_header("Unmapped SSE Tasks")
        st.markdown("""<div style="font-size:0.83rem; color:#5A6A7E; margin-bottom:0.75rem;">
            These SSE Jira keys appear in timesheets but are not linked to any ETE portfolio project.
            Map them below to enable cross-project reporting.
        </div>""", unsafe_allow_html=True)

        for u in unmapped:
            sse_key = u["project_key"]
            proj_name = (u.get("project_name") or "")[:50]
            hrs = u["total_hours"]
            entries = u["entry_count"]

            with st.container():
                mc1, mc2, mc3, mc4 = st.columns([1.5, 2.5, 3, 1])
                with mc1:
                    st.markdown(f"""<div style="font-size:0.85rem; font-weight:600; color:#1565C0;
                        padding:0.4rem 0;">{sse_key}</div>""", unsafe_allow_html=True)
                with mc2:
                    st.markdown(f"""<div style="font-size:0.83rem; color:#5A6A7E;
                        padding:0.4rem 0;">{proj_name}</div>""", unsafe_allow_html=True)
                with mc3:
                    selected_ete = st.selectbox(
                        "ETE Project", ete_options,
                        key=f"_map_ete_{sse_key}",
                        label_visibility="collapsed",
                    )
                with mc4:
                    if st.button("Map", key=f"_map_btn_{sse_key}",
                                 use_container_width=True, type="primary"):
                        ete_id = ete_id_map.get(selected_ete)
                        if ete_id:
                            connector = _get_connector()
                            try:
                                err = connector.save_project_mapping({
                                    "sse_key": sse_key,
                                    "ete_project_id": ete_id,
                                    "sse_title": proj_name,
                                    "relationship": "subtask",
                                })
                            finally:
                                connector.close()
                            if err:
                                st.error(err)
                            else:
                                st.cache_data.clear()
                                st.rerun()
                        else:
                            st.error("Select an ETE project first.")

                st.markdown(f"""<div style="font-size:0.75rem; color:#8A9AB5;
                    margin:-0.25rem 0 0.25rem 0;">{entries} entries | {hrs:.0f} hours</div>""",
                    unsafe_allow_html=True)

        st.markdown("<div style='height: 1.25rem'></div>", unsafe_allow_html=True)

    # ==================================================================
    # Current Mappings Table
    # ==================================================================
    section_header("Current Mappings")

    if mappings:
        # Group by ETE project for a board-ready view
        ete_groups = defaultdict(list)
        for m in mappings:
            ete_label = f"{m['ete_project_id']}: {m.get('ete_project_name') or 'Unknown'}" if m.get("ete_project_id") else "No ETE Link"
            ete_groups[ete_label].append(m)

        html = """<table style="width:100%; border-collapse:collapse; font-size:0.85rem;">
        <thead><tr style="border-bottom:2px solid #C5CDD8; color:#5A6A7E; text-transform:uppercase; font-size:0.75rem;">
            <th style="text-align:left; padding:0.4rem 0.5rem;">SSE Key</th>
            <th style="text-align:left; padding:0.4rem 0.5rem;">SSE Title</th>
            <th style="text-align:left; padding:0.4rem 0.5rem;">ETE Project</th>
            <th style="text-align:left; padding:0.4rem 0.5rem;">Relationship</th>
        </tr></thead><tbody>"""

        for ete_label in sorted(ete_groups.keys()):
            group = ete_groups[ete_label]
            for i, m in enumerate(group):
                sse_url = f"https://etedevops.atlassian.net/browse/{m['sse_key']}"
                sse_link = f'<a href="{sse_url}" target="_blank" style="color:#1565C0; text-decoration:none; font-weight:500;">{m["sse_key"]}</a>'
                title = (m.get("sse_title") or "")[:45]
                rel = m.get("relationship") or "subtask"
                rel_badge_color = {"subtask": "#1565C0", "support": "#27AE60", "related": "#F39C12"}.get(rel, "#5A6A7E")

                # Show ETE project name only on first row of group
                ete_cell = ete_label if i == 0 else ""
                ete_style = "font-weight:600;" if i == 0 else ""
                border = "border-top:2px solid #D5DCE5;" if i == 0 else "border-bottom:1px solid #F0F2F5;"

                html += f"""<tr style="{border}">
                    <td style="padding:0.4rem 0.5rem;">{sse_link}</td>
                    <td style="padding:0.4rem 0.5rem; color:#5A6A7E;">{title}</td>
                    <td style="padding:0.4rem 0.5rem; {ete_style}">{ete_cell}</td>
                    <td style="padding:0.4rem 0.5rem;">
                        <span style="font-size:0.75rem; padding:0.15rem 0.5rem; border-radius:10px;
                            background:{rel_badge_color}15; color:{rel_badge_color}; font-weight:500;">
                            {rel}
                        </span>
                    </td>
                </tr>"""

        html += "</tbody></table>"
        st.markdown(html, unsafe_allow_html=True)

    else:
        st.info("No project mappings configured yet. Map unmapped SSE tasks above, or add mappings manually below.")

    # ==================================================================
    # Hours by ETE Project (aggregated from timesheets via mapping)
    # ==================================================================
    if mappings:
        st.markdown("<div style='height: 1.25rem'></div>", unsafe_allow_html=True)
        section_header("Timesheet Hours by ETE Project")

        connector = _get_connector()
        try:
            all_entries = connector.read_timesheets()
            lookup = connector.get_mapping_lookup()
        finally:
            connector.close()

        ete_hours = defaultdict(lambda: {"project": 0.0, "support": 0.0})
        unmapped_total = {"project": 0.0, "support": 0.0}

        for e in all_entries:
            sse_key = e.get("project_key")
            hrs = e["hours"]
            wt = e.get("work_type", "Support")
            bucket = "project" if wt == "Project" else "support"

            if sse_key and sse_key in lookup:
                m = lookup[sse_key]
                label = f"{m['ete_project_id']}: {m['ete_project_name']}"
                ete_hours[label][bucket] += hrs
            else:
                unmapped_total[bucket] += hrs

        # Build chart data
        chart_rows = []
        for label, hrs in sorted(ete_hours.items(), key=lambda x: -(x[1]["project"] + x[1]["support"])):
            chart_rows.append({"ETE Project": label[:40], "Type": "Project", "Hours": hrs["project"]})
            chart_rows.append({"ETE Project": label[:40], "Type": "Support", "Hours": hrs["support"]})

        if unmapped_total["project"] + unmapped_total["support"] > 0:
            chart_rows.append({"ETE Project": "Unmapped / General", "Type": "Project", "Hours": unmapped_total["project"]})
            chart_rows.append({"ETE Project": "Unmapped / General", "Type": "Support", "Hours": unmapped_total["support"]})

        if chart_rows:
            chart_df = pd.DataFrame(chart_rows)
            chart = alt.Chart(chart_df).mark_bar(
                cornerRadiusTopRight=4, cornerRadiusBottomRight=4
            ).encode(
                y=alt.Y("ETE Project:N", title=None, sort="-x",
                        axis=alt.Axis(labelFontSize=11, labelLimit=280)),
                x=alt.X("Hours:Q", title="Hours", stack="zero",
                        axis=alt.Axis(labelFontSize=11)),
                color=alt.Color("Type:N", scale=alt.Scale(
                    domain=["Project", "Support"],
                    range=["#1B3A5C", "#8BA4C4"]
                ), legend=alt.Legend(orient="top", title=None)),
                tooltip=[
                    alt.Tooltip("ETE Project:N"),
                    alt.Tooltip("Type:N"),
                    alt.Tooltip("Hours:Q", format=".0f"),
                ],
            ).properties(height=max(len(ete_hours) * 40 + 40, 200))

            st.altair_chart(chart, use_container_width=True)

    # --- Manual Add Mapping ---
    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
    with st.expander("Add Mapping Manually"):
        with st.form("add_mapping_form", clear_on_submit=True):
            mc1, mc2 = st.columns(2)
            with mc1:
                new_sse = st.text_input("SSE Key", placeholder="SSE-526", key="_map_new_sse")
                new_title = st.text_input("SSE Title", placeholder="Task description",
                                          key="_map_new_title")
            with mc2:
                new_ete = st.selectbox("ETE Project", ete_options, key="_map_new_ete")
                new_rel = st.selectbox("Relationship",
                                       ["subtask", "support", "related"],
                                       key="_map_new_rel")
            new_notes = st.text_input("Notes", key="_map_new_notes")

            if st.form_submit_button("Save Mapping", use_container_width=True):
                ete_id = ete_id_map.get(new_ete)
                if new_sse.strip() and ete_id:
                    connector = _get_connector()
                    try:
                        err = connector.save_project_mapping({
                            "sse_key": new_sse.strip(),
                            "ete_project_id": ete_id,
                            "sse_title": new_title.strip() or None,
                            "relationship": new_rel,
                            "notes": new_notes.strip() or None,
                        })
                    finally:
                        connector.close()
                    if err:
                        st.error(err)
                    else:
                        st.success(f"Mapped {new_sse.strip()} → {ete_id}")
                        st.cache_data.clear()
                        st.rerun()
                else:
                    st.error("SSE Key and ETE Project are both required.")


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

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Time Entry", "Monthly Review", "Approvals",
        "Invoices", "Approved Work", "Project Mapping",
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

    with tab6:
        _render_mapping_tab(data)
