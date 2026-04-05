"""One-shot cleanup: zero out a role's allocation on all active projects.

Why this exists
===============
Stale role allocations produce phantom demand. Example from 2026-04:
- 3 Infrastructure team members all toggled to include_in_capacity=false
- 5 active projects still carried infrastructure allocations between
  10-20% (legacy defaults from the Excel workbook)
- Result: the dashboard showed 2 hrs/week of Infra demand with 0 supply,
  classified as "over capacity" even though nobody was actually assigned

If a role isn't actually needed on a set of projects, the right fix is
to zero those allocations so demand reflects reality. This script hits
the PATCH endpoint for each affected project so the write goes through
the normal data-integrity layer (_normalize_project rules apply).

Usage
=====
    export PMO_API_URL="https://pmo-agent-production.up.railway.app"
    export PMO_SHARE_KEY="your-shared-password"
    python3 scripts/zero_stale_role_allocations.py infrastructure

    # Dry run first (recommended):
    python3 scripts/zero_stale_role_allocations.py infrastructure --dry-run

    # Or target a different role:
    python3 scripts/zero_stale_role_allocations.py dba

The script:
1. Lists active projects with non-zero allocation for the given role
2. Prints what it will change
3. Asks for confirmation (unless --yes is passed)
4. PATCHes each project to set that role's allocation to 0
5. Reports the result

Idempotent — running twice is safe. Second run finds no projects to
touch and exits cleanly.
"""

import argparse
import os
import sys
from typing import Any, Dict, List, Optional

try:
    import httpx
except ImportError:
    print(
        "This script needs `httpx`. Install with:\n"
        "    pip install httpx\n"
        "(It's already a backend dependency for the test suite.)",
        file=sys.stderr,
    )
    sys.exit(1)


def _client(base_url: str, share_key: Optional[str]) -> httpx.Client:
    headers = {"Content-Type": "application/json"}
    if share_key:
        headers["X-Share-Key"] = share_key
    return httpx.Client(base_url=base_url, headers=headers, timeout=30.0)


def _list_active_projects(client: httpx.Client) -> List[Dict[str, Any]]:
    r = client.get("/api/v1/portfolio/", params={"active_only": True})
    r.raise_for_status()
    return r.json()


def _projects_with_role_demand(
    projects: List[Dict[str, Any]], role_key: str
) -> List[Dict[str, Any]]:
    out = []
    for p in projects:
        allocs = p.get("role_allocations") or {}
        if allocs.get(role_key, 0) > 0:
            out.append(p)
    return out


def _zero_allocation(
    client: httpx.Client, project: Dict[str, Any], role_key: str, dry_run: bool
) -> Optional[str]:
    pid = project["id"]
    if dry_run:
        return None

    # Build a patch that only touches the role_allocations for this role.
    # Merging with existing allocations is important — passing a bare
    # {role_key: 0} would drop the other roles in some implementations,
    # so we send the full dict with the target zeroed out.
    new_allocs = dict(project.get("role_allocations") or {})
    new_allocs[role_key] = 0.0

    r = client.patch(
        f"/api/v1/portfolio/{pid}",
        json={"role_allocations": new_allocs},
    )
    if r.status_code >= 400:
        return f"HTTP {r.status_code}: {r.text}"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Zero out a role's allocation on all active projects."
    )
    parser.add_argument(
        "role_key",
        help="Role key to zero (e.g. 'infrastructure', 'dba', 'wms')",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing anything",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the confirmation prompt",
    )
    parser.add_argument(
        "--url",
        default=os.environ.get("PMO_API_URL"),
        help="Backend URL (default: $PMO_API_URL)",
    )
    parser.add_argument(
        "--share-key",
        default=os.environ.get("PMO_SHARE_KEY"),
        help="X-Share-Key header value (default: $PMO_SHARE_KEY)",
    )
    args = parser.parse_args()

    if not args.url:
        print("ERROR: set PMO_API_URL or pass --url", file=sys.stderr)
        return 2

    print(f"Target: {args.url}")
    print(f"Role:   {args.role_key}")
    print(f"Mode:   {'DRY RUN' if args.dry_run else 'LIVE'}")
    print()

    with _client(args.url, args.share_key) as client:
        # Smoke-test connectivity first so we fail fast if the API is
        # unreachable or the share key is wrong.
        try:
            h = client.get("/api/v1/meta/health")
            h.raise_for_status()
        except Exception as exc:
            print(f"ERROR: cannot reach backend: {exc}", file=sys.stderr)
            return 3

        projects = _list_active_projects(client)
        affected = _projects_with_role_demand(projects, args.role_key)

        if not affected:
            print(f"Nothing to do — no active projects carry a non-zero "
                  f"{args.role_key!r} allocation.")
            return 0

        print(f"Found {len(affected)} project(s) with {args.role_key!r} > 0:")
        print()
        for p in affected:
            current = (p.get("role_allocations") or {}).get(args.role_key, 0)
            print(
                f"  {p['id']:<10}  {p['name'][:50]:<50}  "
                f"current: {current:.0%}  →  new: 0%"
            )
        print()

        if args.dry_run:
            print("Dry run — no changes made.")
            return 0

        if not args.yes:
            ans = input("Apply these changes? (yes/no) ").strip().lower()
            if ans not in ("yes", "y"):
                print("Aborted.")
                return 1

        errors: List[str] = []
        for p in affected:
            err = _zero_allocation(client, p, args.role_key, dry_run=False)
            if err:
                errors.append(f"{p['id']}: {err}")
                print(f"  ✗ {p['id']}  {err}")
            else:
                print(f"  ✓ {p['id']}  zeroed")

        print()
        if errors:
            print(f"Done with {len(errors)} error(s).")
            return 4
        print(f"Done — {len(affected)} project(s) updated.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
