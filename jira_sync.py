"""
Jira Sync for ETE PMO Dashboard.
Pulls % Complete and Health from Jira issues and updates the SQLite database.

Usage:
    # From command line:
    python jira_sync.py

    # From dashboard (called by app.py):
    from jira_sync import sync_from_jira
    results = sync_from_jira(api_key="...", dry_run=False)
"""

import json
import os
import sqlite3
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
JIRA_CLOUD_ID = "b79a437a-0282-4f3c-a737-558c675a8308"
JIRA_SITE_URL = "https://etedevops.atlassian.net"
JIRA_BASE_URL = f"{JIRA_SITE_URL}/rest/api/3"

# Custom field IDs discovered from Jira field metadata
FIELD_PCT_COMPLETE = "customfield_11529"       # Select: 0% - 100%
FIELD_PROJECT_HEALTH = "customfield_11496"     # Select: health statuses
FIELD_BUSINESS_PORTFOLIO = "customfield_12123"  # Select: portfolio names

# Jira projects that contain PMO-tracked issues
JIRA_PROJECTS = ["ETE", "DEV", "SSE"]

DB_PATH = Path(__file__).parent / "pmo_data.db"

# ---------------------------------------------------------------------------
# Jira Health → PMO Health mapping
# ---------------------------------------------------------------------------
# Jira has granular workflow statuses; PMO has broader categories.
# Strip emojis and normalize before lookup.
JIRA_HEALTH_MAP = {
    "NOT STARTED":              "⚪ NOT STARTED",
    "NEEDS FUNCTIONAL SPEC":    "🔵 NEEDS FUNCTIONAL SPEC",
    "NEEDS TECHNICAL SPEC":     "🔵 NEEDS TECHNICAL SPEC",
    "NEEDS SPEC":               None,  # Ignore generic — use granular versions
    "NEEDS KICKSTART BRIEF":    "⚪ NOT STARTED",
    "KICKSTART RECEIVED":       "⚪ NOT STARTED",
    "SPEC REVIEW IN PROGRESS":  "🟢 ON TRACK",
    "PROJECT APPROVED":         "🟢 ON TRACK",
    "ESTIMATE RECEIVED":        "🟢 ON TRACK",
    "APPROVED FOR DEV":         "🟢 ON TRACK",
    "GROOMED/REFINED":          "🟢 ON TRACK",
    "GROOM NEXT":               "🟢 ON TRACK",
    "ON-TRACK":                 "🟢 ON TRACK",
    "ON TRACK":                 "🟢 ON TRACK",
    "AT RISK":                  "🟡 AT RISK",
    "NEEDS HELP":               "🔴 NEEDS HELP",
    "COMPLETE":                 "✅ COMPLETE",
    "POSTPONED":                "⏸️ POSTPONED",
}


def _map_jira_health(jira_health_raw: str) -> Optional[str]:
    """Convert a Jira health value to a PMO health value."""
    if not jira_health_raw:
        return None
    # Strip emojis and whitespace: "🟢ON-TRACK" → "ON-TRACK"
    import re
    stripped = re.sub(r'[^\x00-\x7F]+', '', jira_health_raw).strip()
    stripped = stripped.upper()
    return JIRA_HEALTH_MAP.get(stripped)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class SyncResult:
    """Result of syncing a single project."""
    project_id: str
    project_name: str
    old_pct: float
    new_pct: float
    old_health: str
    new_health: str
    pct_changed: bool = False
    health_changed: bool = False
    error: Optional[str] = None

    @property
    def changed(self) -> bool:
        return self.pct_changed or self.health_changed


@dataclass
class SyncSummary:
    """Overall sync summary."""
    timestamp: str
    total_projects: int
    matched: int
    updated: int
    skipped: int
    errors: int
    results: list


# ---------------------------------------------------------------------------
# Jira API helpers
# ---------------------------------------------------------------------------
def _build_auth_header(api_key: str) -> str:
    """Build Authorization header value.

    Accepts either:
      - "email:api_token" → Basic auth
      - bare token → Bearer auth
    """
    import base64
    if ":" in api_key:
        encoded = base64.b64encode(api_key.encode()).decode()
        return f"Basic {encoded}"
    return f"Bearer {api_key}"


def _jira_request(jql: str, fields: list[str], api_key: str,
                  max_results: int = 100) -> list[dict]:
    """Execute JQL search via Jira REST API."""
    import urllib.parse
    params = urllib.parse.urlencode({
        "jql": jql,
        "fields": ",".join(fields),
        "maxResults": max_results,
    })
    url = f"{JIRA_BASE_URL}/search/jql?{params}"

    req = urllib.request.Request(url, headers={
        "Authorization": _build_auth_header(api_key),
        "Accept": "application/json",
    }, method="GET")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("issues", [])
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Jira API error {e.code}: {body}") from e


def _parse_pct_complete(field_value: Optional[dict]) -> Optional[float]:
    """Parse the % Complete select field into a 0.0-1.0 float."""
    if not field_value:
        return None
    val = field_value.get("value", "")
    try:
        return int(val.replace("%", "").strip()) / 100.0
    except (ValueError, AttributeError):
        return None


# PMO Health → Jira Health option IDs (for pushing to Jira)
PMO_TO_JIRA_HEALTH = {
    "NOT STARTED":              "11281",  # 🔵NOT STARTED
    "NEEDS FUNCTIONAL SPEC":    "12701",  # 🔵 NEEDS FUNCTIONAL SPEC
    "NEEDS TECHNICAL SPEC":     "12700",  # 🔵 NEEDS TECHNICAL SPEC
    "🟢 ON TRACK":              "11282",  # 🟢ON-TRACK
    "🟡 AT RISK":               "11283",  # 🟡AT RISK
    "🔴 NEEDS HELP":             "11284",  # 🔴NEEDS HELP
    "COMPLETE":                 "11285",  # ✅COMPLETE
    "POSTPONED":                "11286",  # 🟡 POSTPONED
}


def _parse_health(field_value: Optional[dict]) -> Optional[str]:
    """Parse the Project Health select field and map to PMO health."""
    if not field_value:
        return None
    raw = field_value.get("value", "")
    return _map_jira_health(raw)


# ---------------------------------------------------------------------------
# Core sync logic
# ---------------------------------------------------------------------------
def sync_from_jira(
    api_key: str,
    db_path: Optional[Path] = None,
    dry_run: bool = False,
) -> SyncSummary:
    """
    Pull % Complete and Health from Jira for all PMO projects and update SQLite.

    Rules:
      - % Complete: only sync forward (Jira >= PMO), except 100% always wins
      - Health: always accept Jira's value (Jira owns execution status)
      - If Jira is 100%, also force health to COMPLETE

    Args:
        api_key: Jira API token (email:token for basic auth, or PAT for bearer)
        db_path: Path to SQLite database (defaults to pmo_data.db)
        dry_run: If True, don't write changes — just report what would change

    Returns:
        SyncSummary with details of what was updated
    """
    if db_path is None:
        db_path = DB_PATH

    # 1. Get all project IDs from SQLite
    conn = sqlite3.connect(str(db_path))
    rows = conn.execute(
        "SELECT id, name, pct_complete, health FROM projects ORDER BY id"
    ).fetchall()

    pmo_projects = {
        row[0]: {"name": row[1], "pct": row[2], "health": row[3] or ""}
        for row in rows
    }

    if not pmo_projects:
        conn.close()
        return SyncSummary(
            timestamp=datetime.now().isoformat(),
            total_projects=0, matched=0, updated=0, skipped=0, errors=0,
            results=[],
        )

    # 2. Build JQL to fetch matching Jira issues
    id_list = ", ".join(pmo_projects.keys())
    jql = f"key in ({id_list})"

    try:
        jira_issues = _jira_request(
            jql=jql,
            fields=["summary", FIELD_PCT_COMPLETE, FIELD_PROJECT_HEALTH],
            api_key=api_key,
            max_results=100,
        )
    except RuntimeError as e:
        conn.close()
        return SyncSummary(
            timestamp=datetime.now().isoformat(),
            total_projects=len(pmo_projects),
            matched=0, updated=0, skipped=0, errors=1,
            results=[SyncResult(
                project_id="*", project_name="API Error",
                old_pct=0, new_pct=0,
                old_health="", new_health="",
                error=str(e),
            )],
        )

    # 3. Build lookup of Jira values by key
    jira_data = {}
    for issue in jira_issues:
        key = issue["key"]
        fields = issue.get("fields", {})
        pct = _parse_pct_complete(fields.get(FIELD_PCT_COMPLETE))
        health = _parse_health(fields.get(FIELD_PROJECT_HEALTH))
        jira_data[key] = {"pct": pct, "health": health}

    # 4. Compare and update
    results = []
    updated_count = 0
    skipped_count = 0
    error_count = 0

    for pid, pmo in pmo_projects.items():
        jira = jira_data.get(pid)
        if not jira:
            skipped_count += 1
            continue

        old_pct = pmo["pct"]
        old_health = pmo["health"]
        jira_pct = jira["pct"]
        jira_health = jira["health"]

        # --- Determine % Complete change ---
        pct_changed = False
        new_pct = old_pct

        if jira_pct is not None and abs(old_pct - jira_pct) > 0.001:
            is_jira_100 = abs(jira_pct - 1.0) < 0.001
            if jira_pct > old_pct or is_jira_100:
                # Sync forward, or 100% always wins
                new_pct = jira_pct
                pct_changed = True

        # --- Determine Health change ---
        health_changed = False
        new_health = old_health
        pmo_is_complete = (
            "COMPLETE" in old_health.upper() or abs(old_pct - 1.0) < 0.001
        )

        # If Jira is 100%, force COMPLETE regardless of Jira health field
        if abs(new_pct - 1.0) < 0.001 and "COMPLETE" not in old_health.upper():
            new_health = "COMPLETE"
            health_changed = True
        elif pmo_is_complete and (not jira_health or "COMPLETE" not in jira_health.upper()):
            # PMO is already complete — don't regress health
            pass
        elif jira_health and jira_health != old_health:
            new_health = jira_health
            health_changed = True

        # --- Skip if nothing changed ---
        if not pct_changed and not health_changed:
            results.append(SyncResult(
                project_id=pid,
                project_name=pmo["name"],
                old_pct=old_pct, new_pct=new_pct,
                old_health=old_health, new_health=new_health,
            ))
            continue

        results.append(SyncResult(
            project_id=pid,
            project_name=pmo["name"],
            old_pct=old_pct, new_pct=new_pct,
            old_health=old_health, new_health=new_health,
            pct_changed=pct_changed,
            health_changed=health_changed,
        ))

        if not dry_run:
            try:
                conn.execute(
                    "UPDATE projects SET pct_complete = ?, health = ?, "
                    "updated_at = datetime('now') WHERE id = ?",
                    (new_pct, new_health, pid),
                )
                updated_count += 1
            except Exception as e:
                results[-1].error = str(e)
                error_count += 1
        else:
            updated_count += 1

    if not dry_run:
        conn.commit()
    conn.close()

    return SyncSummary(
        timestamp=datetime.now().isoformat(),
        total_projects=len(pmo_projects),
        matched=len(jira_data),
        updated=updated_count,
        skipped=skipped_count,
        errors=error_count,
        results=sorted(results, key=lambda r: r.project_id),
    )


# Backward-compatible alias
sync_pct_complete = sync_from_jira


# ---------------------------------------------------------------------------
# Push health to Jira
# ---------------------------------------------------------------------------
def push_health_to_jira(
    project_id: str,
    health: str,
    api_key: str,
) -> Optional[str]:
    """
    Push a project's health status from PMO to Jira.

    Args:
        project_id: Jira issue key (e.g. "ETE-68")
        health: PMO health value (e.g. "🟢 ON TRACK", "COMPLETE")
        api_key: Jira API token (email:token format)

    Returns:
        None on success, error message string on failure.
    """
    # Normalize health — strip emojis from legacy values for lookup
    import re
    normalized = health.strip()

    # Try direct lookup first
    option_id = PMO_TO_JIRA_HEALTH.get(normalized)

    # If not found, try stripping emojis and matching uppercase
    if not option_id:
        stripped = re.sub(r'[^\x00-\x7F]+', '', normalized).strip().upper()
        for pmo_key, oid in PMO_TO_JIRA_HEALTH.items():
            pmo_stripped = re.sub(r'[^\x00-\x7F]+', '', pmo_key).strip().upper()
            if stripped == pmo_stripped:
                option_id = oid
                break

    if not option_id:
        return f"No Jira mapping for health: {health}"

    # PUT to Jira issue
    url = f"{JIRA_BASE_URL}/issue/{project_id}"
    payload = {
        "fields": {
            FIELD_PROJECT_HEALTH: {"id": option_id}
        }
    }
    data_bytes = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url, data=data_bytes, headers={
        "Authorization": _build_auth_header(api_key),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }, method="PUT")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return None  # Success — Jira returns 204 No Content
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return f"Jira API error {e.code}: {body[:200]}"


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    # Try to get API key from environment or .env
    api_key = os.environ.get("JIRA_API_TOKEN", "")
    if not api_key:
        env_path = Path(__file__).parent / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("JIRA_API_TOKEN="):
                    api_key = line.split("=", 1)[1].strip().strip("'\"")
                    break

    if not api_key:
        print("Error: Set JIRA_API_TOKEN environment variable (email:api_token format)")
        print("  export JIRA_API_TOKEN='user@company.com:your-api-token'")
        sys.exit(1)

    # Run sync
    dry = "--dry-run" in sys.argv
    if dry:
        print("DRY RUN — no changes will be written\n")

    summary = sync_from_jira(api_key=api_key, dry_run=dry)

    print(f"Jira Sync Complete — {summary.timestamp}")
    print(f"  PMO Projects: {summary.total_projects}")
    print(f"  Jira Matches: {summary.matched}")
    print(f"  Updated:      {summary.updated}")
    print(f"  Skipped:      {summary.skipped}")
    print(f"  Errors:       {summary.errors}")
    print()

    changes = [r for r in summary.results if r.changed]
    if changes:
        print("Changes:")
        for r in changes:
            parts = []
            if r.pct_changed:
                parts.append(f"{r.old_pct*100:.0f}% → {r.new_pct*100:.0f}%")
            if r.health_changed:
                parts.append(f"health: {r.old_health or '(none)'} → {r.new_health}")
            print(f"  {r.project_id}: {', '.join(parts)}  ({r.project_name})")
    else:
        print("No changes needed — all values in sync.")
