"""Build a seed database with initiatives + pipeline projects.

Reads pmo_data.demo.db, adds the initiatives table, 31 initiatives,
links existing projects, inserts 3 pipeline projects, and dumps the
result to seed_data.sql.

Usage: python3 scripts/build_seed_with_initiatives.py
"""

import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from models import ROLE_KEYS

SRC = ROOT / "pmo_data.demo.db"
BUILD = Path("/tmp/seed_build.db")
DEST = ROOT / "seed_data.sql"


def main():
    if not SRC.exists():
        print(f"ERROR: {SRC} not found. Run the anonymizer first.")
        return 1

    shutil.copy(SRC, BUILD)
    conn = sqlite3.connect(str(BUILD))
    conn.execute("PRAGMA foreign_keys=OFF")

    # --- Schema additions ---
    conn.execute("""CREATE TABLE IF NOT EXISTS initiatives (
        id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT, sponsor TEXT,
        status TEXT NOT NULL DEFAULT 'Active', it_involvement INTEGER NOT NULL DEFAULT 0,
        priority TEXT, target_start TEXT, target_end TEXT, sort_order INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')), updated_at TEXT DEFAULT (datetime('now'))
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_init_status ON initiatives(status)")

    for col, ctype in [
        ("initiative_id", "TEXT REFERENCES initiatives(id)"),
        ("planned_it_start", "TEXT"),
    ]:
        try:
            conn.execute(f"ALTER TABLE projects ADD COLUMN {col} {ctype}")
        except Exception:
            pass

    # --- 31 initiatives ---
    initiatives = [
        ("INIT-01", "Supply Chain Modernization", "End-to-end overhaul of supply chain systems and processes", "Camille Okafor", "Active", 1, "Highest", "2025-01-15", "2026-09-30", 1),
        ("INIT-02", "Customer Experience Platform", "Unified platform for omnichannel customer engagement", "Nolan Pierce", "Active", 1, "High", "2025-03-01", "2026-12-31", 2),
        ("INIT-03", "Workforce Optimization", "Modernize workforce planning, scheduling, and productivity tools", "Beatrice Lin", "Active", 1, "High", "2025-04-01", "2026-10-31", 3),
        ("INIT-04", "Financial Close Transformation", "Accelerate month-end close from 10 days to 3 days", "Nolan Pierce", "Active", 1, "Highest", "2025-02-01", "2026-06-30", 4),
        ("INIT-05", "Data Analytics Center of Excellence", "Establish enterprise analytics capability and self-service BI", "Rafael Bauer", "Active", 1, "High", "2025-06-01", "2026-12-31", 5),
        ("INIT-06", "Cybersecurity Posture Enhancement", "Strengthen security controls, zero trust architecture, and compliance", "Rafael Bauer", "Active", 1, "Highest", "2025-01-01", "2026-12-31", 6),
        ("INIT-07", "ERP System Consolidation", "Consolidate three legacy ERPs into a single platform", "Nolan Pierce", "Active", 1, "High", "2025-03-15", "2026-12-31", 7),
        ("INIT-08", "Digital Commerce Expansion", "Expand e-commerce channels and digital storefront capabilities", "Camille Okafor", "Active", 1, "Medium", "2025-07-01", "2026-09-30", 8),
        ("INIT-09", "Fleet Management Overhaul", "Replace aging fleet management systems and optimize routing", "Camille Okafor", "Active", 1, "Medium", "2025-09-01", "2026-11-30", 9),
        ("INIT-10", "Vendor Risk Management Program", "Implement third-party risk assessment and continuous monitoring", "Beatrice Lin", "Active", 1, "High", "2025-05-01", "2026-08-31", 10),
        ("INIT-11", "Product Lifecycle Management", "Digital PLM system for product design through retirement", "Camille Okafor", "Active", 1, "Medium", "2025-08-01", "2026-12-31", 11),
        ("INIT-12", "Cloud Infrastructure Migration", "Migrate on-premise workloads to cloud with hybrid strategy", "Rafael Bauer", "Active", 1, "Highest", "2025-01-01", "2026-12-31", 12),
        ("INIT-13", "Employee Experience Modernization", "Redesign HR tech stack for improved employee lifecycle", "Beatrice Lin", "Active", 1, "Medium", "2025-06-15", "2026-10-31", 13),
        ("INIT-14", "Regulatory Compliance Automation", "Automate regulatory reporting and compliance workflows", "Nolan Pierce", "Active", 1, "High", "2025-04-01", "2026-09-30", 14),
        ("INIT-15", "Manufacturing Execution System", "Implement MES for real-time shop floor visibility", "Camille Okafor", "Active", 1, "Medium", "2025-10-01", "2026-12-31", 15),
        ("INIT-16", "Sustainability Reporting Platform", "ESG metrics collection, analysis, and regulatory reporting", "Grace Chandler", "Active", 1, "Low", "2025-09-01", "2026-12-31", 16),
        ("INIT-17", "Customer Loyalty Relaunch", "Redesign loyalty program with personalized rewards engine", "Nolan Pierce", "Active", 1, "High", "2025-05-01", "2026-08-31", 17),
        ("INIT-18", "Inventory Optimization Program", "AI-driven inventory balancing across distribution network", "Camille Okafor", "On Hold", 1, "Medium", "2025-07-01", "2026-10-31", 18),
        ("INIT-19", "Legacy System Decommission", "Retire 12 end-of-life applications and migrate data", "Rafael Bauer", "Complete", 1, "High", "2025-01-01", "2025-12-31", 19),
        ("INIT-20", "Corporate Real Estate Rationalization", "Optimize office footprint post-hybrid work model", "Beatrice Lin", "Active", 0, "Medium", "2025-06-01", "2026-06-30", 20),
        ("INIT-21", "Leadership Development Academy", "Build internal leadership pipeline and succession readiness", "Grace Chandler", "Active", 0, "High", "2025-03-01", "2026-12-31", 21),
        ("INIT-22", "Brand Refresh Campaign", "Update brand identity, messaging, and market positioning", "Camille Okafor", "Active", 0, "Medium", "2025-08-01", "2026-06-30", 22),
        ("INIT-23", "Safety Culture Transformation", "Zero-incident safety program across all facilities", "Camille Okafor", "Active", 0, "Highest", "2025-01-01", "2026-12-31", 23),
        ("INIT-24", "Community Engagement Program", "Corporate social responsibility and community partnerships", "Grace Chandler", "Active", 0, "Low", "2025-04-01", "2026-12-31", 24),
        ("INIT-25", "Diversity & Inclusion Strategy", "Enterprise D&I goals, programs, and metrics framework", "Grace Chandler", "Active", 0, "High", "2025-02-01", "2026-12-31", 25),
        ("INIT-26", "Operational Excellence (Lean/6Sigma)", "Enterprise-wide continuous improvement program", "Camille Okafor", "Active", 0, "Highest", "2025-01-01", "2026-12-31", 26),
        ("INIT-27", "New Market Entry - Southeast Region", "Expand operations into southeast US markets", "Nolan Pierce", "Active", 0, "High", "2025-06-01", "2026-09-30", 27),
        ("INIT-28", "Talent Acquisition Redesign", "Modernize recruiting process and employer brand", "Beatrice Lin", "Active", 0, "Medium", "2025-07-01", "2026-06-30", 28),
        ("INIT-29", "Executive Succession Planning", "Formal succession plans for top 50 leadership roles", "Grace Chandler", "Active", 0, "High", "2025-03-01", "2026-09-30", 29),
        ("INIT-30", "Environmental Compliance Review", "Audit and remediate environmental regulatory gaps", "Camille Okafor", "Active", 0, "Medium", "2025-05-01", "2026-08-31", 30),
        ("INIT-31", "Workplace Wellness Initiative", "Employee health, mental wellness, and benefits optimization", "Beatrice Lin", "Active", 0, "Low", "2025-09-01", "2026-12-31", 31),
    ]
    conn.executemany(
        "INSERT OR REPLACE INTO initiatives VALUES(?,?,?,?,?,?,?,?,?,?,datetime('now'),datetime('now'))",
        initiatives,
    )

    # --- Link projects to initiatives ---
    links = {
        "INIT-01": ["DEMO-026", "DEMO-003", "DEMO-037", "DEMO-008"],
        "INIT-02": ["DEMO-015", "DEMO-029", "DEMO-028"],
        "INIT-03": ["DEMO-020"],
        "INIT-04": ["DEMO-005", "DEMO-002", "DEMO-007", "DEMO-034"],
        "INIT-05": ["DEMO-006", "DEMO-009", "DEMO-033", "DEMO-014"],
        "INIT-06": ["DEMO-022", "DEMO-032"],
        "INIT-07": ["DEMO-019", "DEMO-017"],
        "INIT-08": ["DEMO-011", "DEMO-024"],
        "INIT-09": ["DEMO-016", "DEMO-018"],
        "INIT-10": ["DEMO-035", "DEMO-025"],
        "INIT-11": ["DEMO-031"],
        "INIT-12": ["DEMO-030"],
        "INIT-14": ["DEMO-013", "DEMO-001"],
        "INIT-15": ["DEMO-004"],
        "INIT-17": ["DEMO-012"],
        "INIT-18": ["DEMO-023", "DEMO-027", "DEMO-010"],
        "INIT-19": ["DEMO-021"],
        "INIT-26": ["DEMO-036", "DEMO-038"],
    }
    for init_id, proj_ids in links.items():
        for pid in proj_ids:
            conn.execute("UPDATE projects SET initiative_id = ? WHERE id = ?", (init_id, pid))

    # --- 3 Pipeline projects ---
    pipeline = [
        ("DEMO-039", "Warehouse Robotics Integration", "Operations", "Camille Okafor", "Medium", 200, "INIT-01", "2026-Q3", {"technical": 0.3, "developer": 0.4}),
        ("DEMO-040", "AI-Powered Demand Forecasting", "Finance Systems", "Nolan Pierce", "High", 400, "INIT-05", "2026-Q4", {"ba": 0.3, "developer": 0.5}),
        ("DEMO-041", "Zero Trust Network Architecture", "Platform Engineering", "Rafael Bauer", "Highest", 600, "INIT-06", "2026-Q3", {"technical": 0.4, "developer": 0.3, "infrastructure": 0.3}),
    ]
    for pid, name, portfolio, sponsor, priority, hours, init_id, quarter, allocs in pipeline:
        conn.execute(
            """INSERT OR REPLACE INTO projects
               (id, name, type, portfolio, sponsor, health, pct_complete, priority,
                est_hours, sort_order, initiative_id, planned_it_start)
               VALUES (?, ?, 'Key Initiative', ?, ?, '📋 PIPELINE', 0.0, ?, ?, 1, ?, ?)""",
            (pid, name, portfolio, sponsor, priority, hours, init_id, quarter),
        )
        for rk in ROLE_KEYS:
            conn.execute(
                "INSERT OR REPLACE INTO project_role_allocations VALUES(?,?,?)",
                (pid, rk, allocs.get(rk, 0.0)),
            )

    conn.commit()

    # --- Stats ---
    proj_count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    init_count = conn.execute("SELECT COUNT(*) FROM initiatives").fetchone()[0]
    pipe_q = conn.execute("SELECT COUNT(*) FROM projects WHERE health LIKE ?", ("%PIPELINE%",)).fetchone()[0]
    link_count = conn.execute("SELECT COUNT(*) FROM projects WHERE initiative_id IS NOT NULL").fetchone()[0]
    print(f"Projects: {proj_count}")
    print(f"Initiatives: {init_count}")
    print(f"Pipeline: {pipe_q}")
    print(f"Linked to initiatives: {link_count}")

    # --- Dump to seed_data.sql ---
    conn.close()
    dump_conn = sqlite3.connect(str(BUILD))
    with open(str(DEST), "w") as f:
        for line in dump_conn.iterdump():
            f.write(line + "\n")
    dump_conn.close()
    print(f"Seed written to {DEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
