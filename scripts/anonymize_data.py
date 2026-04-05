"""Anonymize a PMO database for public/demo use.

Reads a source SQLite DB and writes a new DB with:
  - All personal names replaced with fictional people (deterministic map —
    "Alice" appears as the same fake name everywhere)
  - Project names / IDs replaced with industry-flavored fake initiatives
  - Sponsors, portfolios, teams, vendors, Jira keys replaced
  - Comments, milestone titles, notes rewritten
  - Dollar amounts scaled by 0.9× and jittered ±25% per row
  - Hours, dates, pct_complete, health, priority, structural data
    preserved so charts still look realistic

Structure-preserving: the same relationships exist, the same tables
have the same row counts, the same foreign keys resolve. Only the
labels change.

Usage
=====
    python3 scripts/anonymize_data.py --source pmo_data.db --dest pmo_data.demo.db

    # Overwrite the source (only if you're sure — keep a backup first):
    python3 scripts/anonymize_data.py --source pmo_data.db --dest pmo_data.db --force

    # Reproducible output (same seed → same fake names):
    python3 scripts/anonymize_data.py --source pmo_data.db --dest demo.db --seed 42
"""

import argparse
import hashlib
import os
import random
import shutil
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Fake data pools
# ---------------------------------------------------------------------------

FIRST_NAMES = [
    "Marcus", "Elena", "Priya", "James", "Sophia", "Liam", "Zara",
    "David", "Isabella", "Ethan", "Maya", "Noah", "Aria", "Oliver",
    "Chloe", "Lucas", "Amara", "Henry", "Layla", "Theo", "Naomi",
    "Caleb", "Iris", "Jonas", "Vera", "Max", "Stella", "Leo", "Hazel",
    "Felix", "Rosa", "Owen", "Mila", "Arlo", "June", "Silas", "Ivy",
    "Jasper", "Cleo", "Atlas", "Sage",
]

LAST_NAMES = [
    "Bell", "Patel", "Chen", "Garcia", "Nakamura", "Okafor",
    "Santos", "Kim", "Rivera", "Wagner", "Nguyen", "Andersen",
    "Flores", "Jensen", "Morales", "Krause", "Brennan", "Dupont",
    "Haruki", "Svensson", "Romano", "Fischer", "Lindqvist", "Reyes",
    "Okonkwo", "Ivanov", "Costa", "Fontaine", "Vasquez", "Bauer",
    "Harris", "Thompson", "Campbell", "Hughes", "Wright",
]

# Industry-flavored project initiatives (mid-size enterprise flavor).
# Pulled from common IT/operations patterns so the app looks like
# a real PMO dashboard rather than a toy.
PROJECT_NAMES = [
    "Warehouse Returns Automation",
    "Customer Portal Rebuild",
    "Financial Close Acceleration",
    "Supplier Onboarding Workflow",
    "Legacy Payments Modernization",
    "Inventory Sync Platform",
    "Sales Forecasting ML Pilot",
    "Procurement Approval Overhaul",
    "Employee Directory Migration",
    "Shipping Label Automation",
    "Invoice OCR Integration",
    "Data Lake Foundation",
    "CRM Contact Deduplication",
    "Expense Report Redesign",
    "Order Routing Optimization",
    "Vendor Portal MVP",
    "Mobile Dispatch App",
    "Billing Cycle Automation",
    "Product Catalog Unification",
    "Analytics Self-Service Platform",
    "Identity Access Management",
    "Single Sign-On Rollout",
    "Cost Center Realignment",
    "Time Tracking Replatform",
    "Returns Portal Upgrade",
    "Price List Automation",
    "Demand Planning Enhancements",
    "Quality Audit Module",
    "Contract Lifecycle Tool",
    "Capacity Planning Dashboard",
    "Help Desk Ticket Triage",
    "Loyalty Program Launch",
    "Distribution Network Optimization",
    "Reorder Point Calculator",
    "Fleet Tracking Integration",
    "Shop Floor Digitization",
    "Budget Variance Reporting",
    "Compliance Documentation System",
    "Inventory Turn Analytics",
    "Cross-Dock Scheduling Tool",
]

PORTFOLIOS = [
    "Operations",
    "Customer Experience",
    "Finance Systems",
    "Platform Engineering",
    "Supply Chain",
    "Corporate Services",
]

TEAMS = [
    "Platform",
    "Business Analysis",
    "Applications",
    "Delivery",
    "Fulfillment Tech",
    "Infrastructure",
]

VENDOR_COMPANIES = [
    "Orbital Partners",
    "Meridian Tech",
    "Northwind Consulting",
    "Blue Harbor Group",
]

SPONSOR_NAMES = [
    "Harper Wells", "Grace Chandler", "Dominic Torres",
    "Vivienne Park", "Rafael Bauer", "Camille Okafor",
    "Nolan Pierce", "Beatrice Lin",
]

# Generic milestone / comment filler so nothing leaks through free-text
MILESTONE_TEMPLATES = [
    "Discovery Complete",
    "Requirements Signed Off",
    "Technical Design Review",
    "Build Phase Kickoff",
    "Integration Testing",
    "UAT Sign-Off",
    "Production Cutover",
    "Hypercare Complete",
    "Vendor Contract Signed",
    "Stakeholder Demo",
]

COMMENT_TEMPLATES = [
    "Kickoff meeting scheduled for next week.",
    "Scope aligned with sponsor. Moving to design phase.",
    "Vendor engaged. Statement of work under review.",
    "Risk log updated after steering committee.",
    "Status: on track. No blockers at this time.",
    "Requirements gathering complete.",
    "Testing cycle begins Monday.",
    "Cutover plan finalized with ops team.",
    "Budget reforecast submitted for approval.",
    "Timeline adjusted to account for dependency shift.",
]

AUDIT_NOTE_TEMPLATES = [
    "Updated health status",
    "Progress updated",
    "Milestone completed",
    "Comment added",
    "Assignment updated",
]


# ---------------------------------------------------------------------------
# Deterministic mappers
# ---------------------------------------------------------------------------

class Mapper:
    """Caches fake-name mappings so the same real name always becomes the
    same fake name across every table."""

    def __init__(self, rng: random.Random):
        self.rng = rng
        self.people: Dict[str, str] = {}
        self.projects: Dict[str, str] = {}  # real project ID → fake project ID
        self.project_names: Dict[str, str] = {}  # real ID → fake name
        self.portfolios: Dict[str, str] = {}
        self.teams: Dict[str, str] = {}
        self.vendors: Dict[str, str] = {}
        self.sponsors: Dict[str, str] = {}
        self._used_people: set = set()
        self._used_projects: set = set()
        self._used_project_names: set = set()
        self._next_project_idx = 1

    def person(self, name: Optional[str]) -> Optional[str]:
        if not name:
            return name
        key = name.strip()
        if not key:
            return name
        if key in self.people:
            return self.people[key]
        # Pick a deterministic fake from the pools. Keep trying until we
        # get one that hasn't been used yet (preserves uniqueness).
        for _ in range(200):
            first = self.rng.choice(FIRST_NAMES)
            last = self.rng.choice(LAST_NAMES)
            candidate = f"{first} {last}"
            if candidate not in self._used_people:
                self.people[key] = candidate
                self._used_people.add(candidate)
                return candidate
        # Pool exhausted — fall back to numbered
        candidate = f"Team Member {len(self._used_people) + 1}"
        self.people[key] = candidate
        self._used_people.add(candidate)
        return candidate

    def project(self, real_id: str) -> str:
        if real_id in self.projects:
            return self.projects[real_id]
        fake = f"DEMO-{self._next_project_idx:03d}"
        self._next_project_idx += 1
        self.projects[real_id] = fake
        return fake

    def project_name(self, real_id: str, real_name: Optional[str]) -> str:
        if real_id in self.project_names:
            return self.project_names[real_id]
        for _ in range(200):
            candidate = self.rng.choice(PROJECT_NAMES)
            if candidate not in self._used_project_names:
                self.project_names[real_id] = candidate
                self._used_project_names.add(candidate)
                return candidate
        # Pool exhausted — numbered fallback
        candidate = f"Project Beta {len(self._used_project_names) + 1}"
        self.project_names[real_id] = candidate
        self._used_project_names.add(candidate)
        return candidate

    def portfolio(self, name: Optional[str]) -> Optional[str]:
        if not name:
            return name
        if name in self.portfolios:
            return self.portfolios[name]
        # Map deterministically to one of the fake portfolios (preserves
        # distribution of projects per portfolio)
        h = int(hashlib.md5(name.encode()).hexdigest(), 16)
        fake = PORTFOLIOS[h % len(PORTFOLIOS)]
        self.portfolios[name] = fake
        return fake

    def team(self, name: Optional[str]) -> Optional[str]:
        if not name:
            return name
        if name in self.teams:
            return self.teams[name]
        h = int(hashlib.md5(name.encode()).hexdigest(), 16)
        fake = TEAMS[h % len(TEAMS)]
        self.teams[name] = fake
        return fake

    def vendor(self, name: Optional[str]) -> Optional[str]:
        if not name:
            return name
        if name in self.vendors:
            return self.vendors[name]
        h = int(hashlib.md5(name.encode()).hexdigest(), 16)
        fake = VENDOR_COMPANIES[h % len(VENDOR_COMPANIES)]
        self.vendors[name] = fake
        return fake

    def sponsor(self, name: Optional[str]) -> Optional[str]:
        """Sponsors are executive-level — draw from a separate smaller pool
        so they feel distinct from rank-and-file team members."""
        if not name:
            return name
        if name in self.sponsors:
            return self.sponsors[name]
        # Use the same deterministic map as people so an exec mentioned in
        # both fields stays consistent, but prefer the sponsor pool.
        h = int(hashlib.md5(name.encode()).hexdigest(), 16)
        fake = SPONSOR_NAMES[h % len(SPONSOR_NAMES)]
        self.sponsors[name] = fake
        return fake


# ---------------------------------------------------------------------------
# Amount scaling
# ---------------------------------------------------------------------------

def scale_amount(value: Optional[float], rng: random.Random) -> Optional[float]:
    """Scale a monetary value by 0.9× then jitter ±25% per row.
    Distributions stay similar but no single number maps back."""
    if value is None or value == 0:
        return value
    jitter = rng.uniform(0.75, 1.25)
    return round(value * 0.9 * jitter, 2)


def scale_rate(value: Optional[float], rng: random.Random) -> Optional[float]:
    """Contract rates get a wider random substitute (obscures real contracts)."""
    if value is None or value == 0:
        return value
    return round(rng.uniform(75, 185), 0)


# ---------------------------------------------------------------------------
# Main anonymizer
# ---------------------------------------------------------------------------

def anonymize(src_path: str, dest_path: str, seed: int = 1337) -> None:
    rng = random.Random(seed)
    mapper = Mapper(rng)

    # Copy source to dest first so we operate on a duplicate (preserves
    # source schema + all rows, including tables we don't touch like
    # app_settings, rm_assumptions, sdlc_phase_weights, etc.).
    shutil.copy(src_path, dest_path)
    conn = sqlite3.connect(dest_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")  # we'll rewrite IDs

    # -----------------------------------------------------------------
    # Build the people map FIRST by scanning every name-carrying column
    # -----------------------------------------------------------------
    # This ensures "Alice" → "Maya Bell" everywhere, not different fakes
    # per table.
    name_sources = [
        ("team_members", "name"),
        ("projects", "pm"),
        ("projects", "ba"),
        ("projects", "functional_lead"),
        ("projects", "technical_lead"),
        ("projects", "developer_lead"),
        ("project_comments", "author"),
        ("project_audit_log", "actor"),
        ("project_assignments", "person_name"),
        ("vendor_consultants", "name"),
    ]
    for table, col in name_sources:
        try:
            for row in conn.execute(f"SELECT DISTINCT {col} FROM {table} WHERE {col} IS NOT NULL AND {col} != ''"):
                mapper.person(row[0])
        except sqlite3.OperationalError:
            pass  # table/column might not exist in older DBs

    # Sponsors get their own (smaller) pool
    for row in conn.execute("SELECT DISTINCT sponsor FROM projects WHERE sponsor IS NOT NULL AND sponsor != ''"):
        mapper.sponsor(row[0])

    # -----------------------------------------------------------------
    # Build the project ID map (stable ordering so DEMO-001 is always
    # the same real project for a given seed)
    # -----------------------------------------------------------------
    project_rows = list(conn.execute("SELECT id, name FROM projects ORDER BY id"))
    for row in project_rows:
        mapper.project(row["id"])
        mapper.project_name(row["id"], row["name"])

    # -----------------------------------------------------------------
    # projects
    # -----------------------------------------------------------------
    # Two-pass: create new rows under new IDs, delete old rows, copy
    # back with FK cascades remapped. Easier approach: update in place.
    # We do in-place because we turned off FK enforcement.
    old_to_new: Dict[str, str] = dict(mapper.projects)
    # To avoid collisions (old ID ETE-1 → new DEMO-001, then update hits
    # another ETE-X that maps to DEMO-XYZ which might clash), we rename
    # all projects to temporary unique tokens first, then to final fake IDs.
    for old_id in list(old_to_new.keys()):
        tmp = f"__TMP__{abs(hash(old_id))}"
        conn.execute("UPDATE projects SET id = ? WHERE id = ?", (tmp, old_id))
        conn.execute("UPDATE project_role_allocations SET project_id = ? WHERE project_id = ?", (tmp, old_id))
        conn.execute("UPDATE project_assignments SET project_id = ? WHERE project_id = ?", (tmp, old_id))
        try:
            conn.execute("UPDATE project_comments SET project_id = ? WHERE project_id = ?", (tmp, old_id))
            conn.execute("UPDATE project_audit_log SET project_id = ? WHERE project_id = ?", (tmp, old_id))
            conn.execute("UPDATE project_attachments SET project_id = ? WHERE project_id = ?", (tmp, old_id))
            conn.execute("UPDATE project_milestones SET project_id = ? WHERE project_id = ?", (tmp, old_id))
            conn.execute("UPDATE project_tasks SET project_id = ? WHERE project_id = ?", (tmp, old_id))
            conn.execute("UPDATE project_mapping SET ete_project_id = ? WHERE ete_project_id = ?", (tmp, old_id))
        except sqlite3.OperationalError:
            pass

    for old_id, new_id in old_to_new.items():
        tmp = f"__TMP__{abs(hash(old_id))}"
        conn.execute("UPDATE projects SET id = ? WHERE id = ?", (new_id, tmp))
        conn.execute("UPDATE project_role_allocations SET project_id = ? WHERE project_id = ?", (new_id, tmp))
        conn.execute("UPDATE project_assignments SET project_id = ? WHERE project_id = ?", (new_id, tmp))
        try:
            conn.execute("UPDATE project_comments SET project_id = ? WHERE project_id = ?", (new_id, tmp))
            conn.execute("UPDATE project_audit_log SET project_id = ? WHERE project_id = ?", (new_id, tmp))
            conn.execute("UPDATE project_attachments SET project_id = ? WHERE project_id = ?", (new_id, tmp))
            conn.execute("UPDATE project_milestones SET project_id = ? WHERE project_id = ?", (new_id, tmp))
            conn.execute("UPDATE project_tasks SET project_id = ? WHERE project_id = ?", (new_id, tmp))
            conn.execute("UPDATE project_mapping SET ete_project_id = ? WHERE ete_project_id = ?", (new_id, tmp))
        except sqlite3.OperationalError:
            pass

    # Now rewrite the text columns on projects (names, portfolio, sponsor, leads, notes, $ amounts)
    for row in conn.execute("SELECT id FROM projects"):
        new_id = row["id"]
        # Look up the real name of this project via reverse map
        real_id = next(k for k, v in old_to_new.items() if v == new_id)
        fake_name = mapper.project_name(real_id, None)

        # Pull current values
        cur = conn.execute(
            "SELECT portfolio, sponsor, pm, ba, functional_lead, technical_lead, developer_lead, notes, budget, actual_cost, forecast_cost FROM projects WHERE id = ?",
            (new_id,),
        ).fetchone()

        conn.execute(
            """UPDATE projects SET
                name = ?,
                portfolio = ?,
                sponsor = ?,
                pm = ?,
                ba = ?,
                functional_lead = ?,
                technical_lead = ?,
                developer_lead = ?,
                notes = NULL,
                budget = ?,
                actual_cost = ?,
                forecast_cost = ?
               WHERE id = ?""",
            (
                fake_name,
                mapper.portfolio(cur["portfolio"]),
                mapper.sponsor(cur["sponsor"]),
                mapper.person(cur["pm"]),
                mapper.person(cur["ba"]),
                mapper.person(cur["functional_lead"]),
                mapper.person(cur["technical_lead"]),
                mapper.person(cur["developer_lead"]),
                scale_amount(cur["budget"], rng),
                scale_amount(cur["actual_cost"], rng),
                scale_amount(cur["forecast_cost"], rng),
                new_id,
            ),
        )

    # -----------------------------------------------------------------
    # team_members
    # -----------------------------------------------------------------
    # Two-pass rename to avoid PK collisions on "name"
    for row in conn.execute("SELECT name FROM team_members"):
        old = row["name"]
        tmp = f"__TMP_TM__{abs(hash(old))}"
        conn.execute("UPDATE team_members SET name = ? WHERE name = ?", (tmp, old))
        conn.execute("UPDATE project_assignments SET person_name = ? WHERE person_name = ?", (tmp, old))

    for old, new in list(mapper.people.items()):
        tmp = f"__TMP_TM__{abs(hash(old))}"
        # Only rename if that tmp row exists (some people may not be team_members)
        exists = conn.execute("SELECT 1 FROM team_members WHERE name = ?", (tmp,)).fetchone()
        if exists:
            conn.execute("UPDATE team_members SET name = ? WHERE name = ?", (new, tmp))
        conn.execute("UPDATE project_assignments SET person_name = ? WHERE person_name = ?", (new, tmp))

    # Any __TMP__ rows remaining are members we didn't hit via the name pool
    # (shouldn't happen, but be safe)
    leftover = list(conn.execute("SELECT name FROM team_members WHERE name LIKE '__TMP_TM__%'"))
    for row in leftover:
        # Pull a fresh fake name
        fake = mapper.person(row["name"])
        conn.execute("UPDATE team_members SET name = ? WHERE name = ?", (fake, row["name"]))
        conn.execute("UPDATE project_assignments SET person_name = ? WHERE person_name = ?", (fake, row["name"]))

    # Team + vendor columns
    for row in conn.execute("SELECT DISTINCT team FROM team_members WHERE team IS NOT NULL"):
        fake = mapper.team(row["team"])
        conn.execute("UPDATE team_members SET team = ? WHERE team = ?", (fake, row["team"]))
    for row in conn.execute("SELECT DISTINCT vendor FROM team_members WHERE vendor IS NOT NULL"):
        fake = mapper.vendor(row["vendor"])
        conn.execute("UPDATE team_members SET vendor = ? WHERE vendor = ?", (fake, row["vendor"]))

    # Rates
    for row in conn.execute("SELECT name, rate_per_hour FROM team_members WHERE rate_per_hour > 0"):
        new_rate = scale_rate(row["rate_per_hour"], rng)
        conn.execute("UPDATE team_members SET rate_per_hour = ? WHERE name = ?", (new_rate, row["name"]))

    # -----------------------------------------------------------------
    # Comments (free-text — scrub entirely)
    # -----------------------------------------------------------------
    try:
        for row in conn.execute("SELECT id, author FROM project_comments"):
            new_body = rng.choice(COMMENT_TEMPLATES)
            conn.execute(
                "UPDATE project_comments SET author = ?, body = ? WHERE id = ?",
                (mapper.person(row["author"]), new_body, row["id"]),
            )
    except sqlite3.OperationalError:
        pass

    # -----------------------------------------------------------------
    # Audit log
    # -----------------------------------------------------------------
    try:
        for row in conn.execute("SELECT id, actor, old_value, new_value, details FROM project_audit_log"):
            conn.execute(
                """UPDATE project_audit_log
                   SET actor = ?, old_value = NULL, new_value = NULL, details = ?
                   WHERE id = ?""",
                (mapper.person(row["actor"]), rng.choice(AUDIT_NOTE_TEMPLATES), row["id"]),
            )
    except sqlite3.OperationalError:
        pass

    # -----------------------------------------------------------------
    # Milestones
    # -----------------------------------------------------------------
    try:
        for row in conn.execute("SELECT id, owner FROM project_milestones"):
            conn.execute(
                "UPDATE project_milestones SET title = ?, owner = ?, notes = NULL, jira_epic_key = NULL WHERE id = ?",
                (rng.choice(MILESTONE_TEMPLATES), mapper.person(row["owner"]), row["id"]),
            )
    except sqlite3.OperationalError:
        pass

    # -----------------------------------------------------------------
    # Tasks
    # -----------------------------------------------------------------
    try:
        for row in conn.execute("SELECT id, assignee FROM project_tasks"):
            conn.execute(
                "UPDATE project_tasks SET title = ?, description = NULL, assignee = ?, jira_key = NULL WHERE id = ?",
                (f"Task {row['id']}", mapper.person(row["assignee"]), row["id"]),
            )
    except sqlite3.OperationalError:
        pass

    # -----------------------------------------------------------------
    # Vendor consultants — same people pool as team_members
    # -----------------------------------------------------------------
    try:
        for row in conn.execute("SELECT id, name, hourly_rate FROM vendor_consultants"):
            conn.execute(
                "UPDATE vendor_consultants SET name = ?, hourly_rate = ? WHERE id = ?",
                (mapper.person(row["name"]), scale_rate(row["hourly_rate"], rng), row["id"]),
            )
    except sqlite3.OperationalError:
        pass

    # -----------------------------------------------------------------
    # Vendor timesheets — scrub task descriptions + scale hours slightly
    # -----------------------------------------------------------------
    try:
        for row in conn.execute("SELECT id, project_name FROM vendor_timesheets"):
            conn.execute(
                "UPDATE vendor_timesheets SET project_name = NULL, task_description = NULL, notes = NULL WHERE id = ?",
                (row["id"],),
            )
        # Project key references → remap or null
        for row in conn.execute("SELECT id, project_key FROM vendor_timesheets WHERE project_key IS NOT NULL"):
            conn.execute(
                "UPDATE vendor_timesheets SET project_key = NULL WHERE id = ?",
                (row["id"],),
            )
    except sqlite3.OperationalError:
        pass

    # -----------------------------------------------------------------
    # Vendor invoices — scale amounts + scrub numbers
    # -----------------------------------------------------------------
    try:
        for row in conn.execute("SELECT id, msa_amount, tm_amount, total_amount FROM vendor_invoices"):
            m = scale_amount(row["msa_amount"], rng)
            t = scale_amount(row["tm_amount"], rng)
            tot = (m or 0) + (t or 0)
            conn.execute(
                "UPDATE vendor_invoices SET msa_amount = ?, tm_amount = ?, total_amount = ?, invoice_number = ?, notes = NULL WHERE id = ?",
                (m, t, tot, f"INV-{row['id']:04d}", row["id"]),
            )
    except sqlite3.OperationalError:
        pass

    # -----------------------------------------------------------------
    # Vendor approvals — scrub approver names
    # -----------------------------------------------------------------
    try:
        for row in conn.execute("SELECT id, vendor_approved_by, ete_approved_by FROM vendor_approvals"):
            conn.execute(
                "UPDATE vendor_approvals SET vendor_approved_by = ?, ete_approved_by = ? WHERE id = ?",
                (mapper.person(row["vendor_approved_by"]), mapper.person(row["ete_approved_by"]), row["id"]),
            )
    except sqlite3.OperationalError:
        pass

    # -----------------------------------------------------------------
    # Approved work — scrub titles + keys
    # -----------------------------------------------------------------
    try:
        for row in conn.execute("SELECT id, approver FROM approved_work"):
            conn.execute(
                "UPDATE approved_work SET title = ?, jira_key = NULL, approver = ?, notes = NULL WHERE id = ?",
                (f"Work Item {row['id']}", mapper.person(row["approver"]), row["id"]),
            )
    except sqlite3.OperationalError:
        pass

    # -----------------------------------------------------------------
    # Project mapping (SSE → ETE) — remap both sides
    # -----------------------------------------------------------------
    try:
        rows = list(conn.execute("SELECT id, sse_key, ete_project_id, sse_title FROM project_mapping"))
        for i, row in enumerate(rows, start=1):
            conn.execute(
                "UPDATE project_mapping SET sse_key = ?, sse_title = ?, notes = NULL WHERE id = ?",
                (f"DEMO-SSE-{i:03d}", f"Related work item {i}", row["id"]),
            )
    except sqlite3.OperationalError:
        pass

    # -----------------------------------------------------------------
    # Attachments — drop free-text filenames, keep counts
    # -----------------------------------------------------------------
    try:
        for row in conn.execute("SELECT id FROM project_attachments"):
            conn.execute(
                "UPDATE project_attachments SET filename = ?, stored_path = ?, uploaded_by = ? WHERE id = ?",
                (f"attachment_{row['id']}.pdf", f"/uploads/{row['id']}", "Demo User", row["id"]),
            )
    except sqlite3.OperationalError:
        pass

    # -----------------------------------------------------------------
    # Clean up any lingering __TMP__ IDs
    # -----------------------------------------------------------------
    for row in conn.execute("SELECT id FROM projects WHERE id LIKE '__TMP__%'"):
        # Shouldn't happen but fail loud if it does
        raise RuntimeError(f"Leftover temp project ID: {row['id']}")

    conn.commit()
    conn.execute("VACUUM")
    conn.close()

    print(f"  People remapped:       {len(mapper.people)}")
    print(f"  Projects remapped:     {len(mapper.projects)}")
    print(f"  Portfolios remapped:   {len(mapper.portfolios)}")
    print(f"  Teams remapped:        {len(mapper.teams)}")
    print(f"  Vendors remapped:      {len(mapper.vendors)}")
    print(f"  Sponsors remapped:     {len(mapper.sponsors)}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Anonymize a PMO database for demo/public use."
    )
    parser.add_argument("--source", required=True, help="Source .db file")
    parser.add_argument("--dest", required=True, help="Destination .db file")
    parser.add_argument("--seed", type=int, default=1337, help="RNG seed (default: 1337)")
    parser.add_argument("--force", action="store_true", help="Overwrite dest if exists")
    args = parser.parse_args()

    if not os.path.exists(args.source):
        print(f"ERROR: source {args.source!r} not found", file=sys.stderr)
        return 2

    if os.path.exists(args.dest) and not args.force:
        print(
            f"ERROR: dest {args.dest!r} exists (use --force to overwrite)",
            file=sys.stderr,
        )
        return 2

    if os.path.exists(args.dest):
        os.remove(args.dest)

    print(f"Anonymizing {args.source} → {args.dest} (seed={args.seed})")
    print()
    anonymize(args.source, args.dest, seed=args.seed)
    print()
    print(f"Done. Demo DB written to {args.dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
