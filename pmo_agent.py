"""
ETE IT PMO AI Resource Planning Agent.
Chat interface powered by Claude with tool-use for portfolio queries,
capacity analysis, and what-if scenarios.
"""

import json
import os
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import anthropic

from excel_connector import ExcelConnector
from capacity_engine import CapacityEngine
from snapshot_store import SnapshotStore
from schedule_optimizer import ScheduleOptimizer

# ---------------------------------------------------------------------------
# Load API key from env or .env file
# ---------------------------------------------------------------------------
def _load_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key

    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("ANTHROPIC_API_KEY="):
                key = line.split("=", 1)[1].strip().strip("'\"")
                os.environ["ANTHROPIC_API_KEY"] = key
                return key

    print("ERROR: No API key found.")
    print("Set ANTHROPIC_API_KEY env var or create a .env file with:")
    print("  ANTHROPIC_API_KEY=sk-ant-...")
    sys.exit(1)


# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are the ETE IT PMO Resource Planning Agent. You help the PMO team make data-driven resource allocation decisions using live data from the ETE PMO Excel workbook.

RULES:
• Highest priority = immovable. Never delay.
• High priority = minimal flex (≤2 weeks).
• Medium/Low = flexible. Delay these first.
• Target utilization: 85%. Red ≥100% must be resolved.
• Demand = Est.Hours × Role% × SDLC Phase Effort% / Duration. Only if Role% > 0.
• Always provide 2-4 concrete options with specific numbers when suggesting trade-offs.
• Never overwrite source sheets without confirmation.
• Lead with the answer, then supporting detail.
• Cite specific numbers: "Developer at 106%" not "Developer is overloaded".

DATA MODEL:
• 8 roles: PM, DBA, BA (Business Analyst), Functional, Technical, Developer, Infrastructure, WMS
• Supply = sum of each person's project_capacity_hrs (weekly hrs × project capacity %)
• SDLC Phases: Discovery 10%, Planning 10%, Design 15%, Build 30%, Test 20%, Deploy 15%
• Each role has different effort weights per phase (e.g., Developer: 0% Discovery → 50% Build → 25% Test)
• Projects without start/end dates are "unscheduled" — they create NO demand until scheduled
• Bottom-up estimation: use estimate_timeline to compute how long a project will take based on actual capacity. The bottleneck role in each phase determines duration. If role allocations don't sum to 100%, flag the gap as unallocated hours.
• ALWAYS show durations in DAYS (business days), never weeks. Do not show weeks alongside days.
• When asked "how long will this take?" or "does this timeline make sense?", always use estimate_timeline.
• When asked "when can we start?" or "what dates should this project have?", use suggest_dates — it scans real role availability week by week to find the earliest viable window.

CHANGE DETECTION:
• Use detect_changes at the start of each session to proactively report what changed since last time.
• After a planning session or significant discussion, offer to save_snapshot to establish a new baseline.
• Use refresh_dashboard to regenerate the Excel dashboard when the user asks to update or refresh it, or after significant planning changes.
• When reporting changes, highlight anything that affects capacity or priority.

Use your tools to fetch live data before answering. Don't guess — always ground answers in the workbook data. Show the "Data as of" timestamp when reporting numbers."""


# ---------------------------------------------------------------------------
# Tool Definitions
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "name": "get_portfolio_status",
        "description": "Get the current project portfolio status. Returns all active projects with their health, priority, % complete, estimated hours, dates, and role allocations. Use this to answer questions about project status, what's on track, what's stuck, and project counts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filter_priority": {
                    "type": "string",
                    "enum": ["Highest", "High", "Medium", "Low", "all"],
                    "description": "Filter by priority level. Use 'all' for everything."
                },
                "include_inactive": {
                    "type": "boolean",
                    "description": "If true, include POSTPONED and completed projects too."
                }
            },
            "required": []
        }
    },
    {
        "name": "get_capacity_analysis",
        "description": "Get current resource utilization analysis by role. Shows supply (hrs/week), demand (hrs/week), utilization %, and status (GREEN/YELLOW/RED) for each role, plus demand breakdown by project. Use this to answer capacity questions, identify bottlenecks, and check role workloads.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_project_details",
        "description": "Get detailed information about a specific project by ID (e.g., ETE-83) or by name search. Returns full project data including role allocations, dates, demand calculations, and weekly timeline.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID like 'ETE-83' or partial name to search for."
                }
            },
            "required": ["project_id"]
        }
    },
    {
        "name": "get_team_roster",
        "description": "Get the team roster with all 23 resources. Shows each person's role, team, vendor, classification, weekly hours, support reserve %, and project capacity hours. Use to answer questions about team composition, who's available, and individual capacity.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filter_role": {
                    "type": "string",
                    "description": "Filter by role key: pm, dba, ba, functional, technical, developer, infrastructure, wms. Omit for all."
                }
            },
            "required": []
        }
    },
    {
        "name": "what_if_add_project",
        "description": "Run a what-if scenario: 'What if we add a new project with X hours and Y role allocations?' Calculates the impact on utilization for each affected role and flags any that would exceed thresholds. Use this to assess whether the team can absorb new work.",
        "input_schema": {
            "type": "object",
            "properties": {
                "est_hours": {
                    "type": "number",
                    "description": "Estimated total hours for the new project."
                },
                "duration_weeks": {
                    "type": "number",
                    "description": "Duration in weeks. If omitted, defaults to 12 weeks."
                },
                "role_allocations": {
                    "type": "object",
                    "description": "Role allocation percentages as decimals. Keys are role names (ba, functional, technical, developer, infrastructure, dba, pm, wms). Example: {\"developer\": 0.75, \"ba\": 0.10}",
                    "additionalProperties": {"type": "number"}
                },
                "priority": {
                    "type": "string",
                    "enum": ["Highest", "High", "Medium", "Low"],
                    "description": "Priority of the hypothetical project."
                }
            },
            "required": ["est_hours", "role_allocations"]
        }
    },
    {
        "name": "what_if_lose_resource",
        "description": "Run a what-if scenario: 'What if we lose a team member?' Recalculates supply and utilization for the affected role. Use to assess risk of losing a specific person or a role headcount.",
        "input_schema": {
            "type": "object",
            "properties": {
                "resource_name": {
                    "type": "string",
                    "description": "Name of the team member to remove (e.g., 'Colin Olson'). If omitted, use role_key to remove one generic headcount."
                },
                "role_key": {
                    "type": "string",
                    "description": "Role key (developer, ba, technical, etc.) to remove one headcount from. Used when resource_name is not provided."
                }
            },
            "required": []
        }
    },
    {
        "name": "detect_changes",
        "description": "Compare the current workbook state against the last saved snapshot. Reports new projects, removed projects, status/health changes, progress changes, date shifts, priority changes, and hours changes. Use this at the start of a session or when the user asks 'what changed?'",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "optimize_schedule",
        "description": "Run the OR-Tools constraint solver to find optimal project start dates. Assigns dates to unscheduled projects and adjusts scheduled ones to keep all roles under 85% utilization. Respects priority hierarchy: Highest=immovable, High=max 2wk shift, Medium=8wk, Low=16wk. Can also include hypothetical new projects in the optimization. Returns recommended dates, shifts, and post-optimization utilization.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target_utilization": {
                    "type": "number",
                    "description": "Max utilization target as decimal (default 0.85 = 85%). Use lower for more buffer."
                },
                "horizon_weeks": {
                    "type": "integer",
                    "description": "Planning horizon in weeks (default 26 = ~6 months)."
                },
                "extra_projects": {
                    "type": "array",
                    "description": "Hypothetical projects to include in optimization.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "est_hours": {"type": "number"},
                            "role_allocations": {"type": "object", "additionalProperties": {"type": "number"}},
                            "priority": {"type": "string", "enum": ["Highest", "High", "Medium", "Low"]},
                            "duration_weeks": {"type": "integer"}
                        },
                        "required": ["est_hours", "role_allocations"]
                    }
                }
            },
            "required": []
        }
    },
    {
        "name": "estimate_timeline",
        "description": "Bottom-up duration estimate: given a project's total hours and role allocations, compute how long each SDLC phase takes and total project duration based on actual team capacity. The bottleneck role in each phase determines phase length. Use this to answer 'how long will this take?' or 'does this estimate make sense?' Also validates that allocated hours reconcile to the project estimate. Can analyze an existing project by ID or a hypothetical project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Existing project ID (e.g., 'ETE-83') to estimate. If provided, uses that project's hours and role allocations."
                },
                "est_hours": {
                    "type": "number",
                    "description": "Estimated total hours (for hypothetical project, or to override an existing project's estimate)."
                },
                "role_allocations": {
                    "type": "object",
                    "description": "Role allocation percentages as decimals. Example: {\"developer\": 0.60, \"ba\": 0.20, \"pm\": 0.10}. Keys: ba, functional, technical, developer, infrastructure, dba, pm, wms.",
                    "additionalProperties": {"type": "number"}
                },
                "max_utilization": {
                    "type": "number",
                    "description": "Max utilization target as decimal (default 0.85 = 85%). Lower = more conservative estimate."
                },
                "concurrent_projects": {
                    "type": "integer",
                    "description": "Number of other projects competing for the same resources (default 0 = dedicated team). Higher = longer duration."
                }
            },
            "required": []
        }
    },
    {
        "name": "suggest_dates",
        "description": "Bottom-up date suggestion: scans forward week by week, checking existing project demand against role capacity, and finds the earliest start date where all required roles can handle the new project without exceeding utilization targets. Returns suggested start/end dates, role availability at that time, and full phase breakdown. Use this when asked 'when can we start?' or 'what dates should this project have?'",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Existing project ID to suggest dates for. Uses that project's hours and role allocations."
                },
                "est_hours": {
                    "type": "number",
                    "description": "Estimated total hours (for hypothetical project)."
                },
                "role_allocations": {
                    "type": "object",
                    "description": "Role allocation percentages as decimals. Example: {\"developer\": 0.30, \"ba\": 0.20}",
                    "additionalProperties": {"type": "number"}
                },
                "max_utilization": {
                    "type": "number",
                    "description": "Max utilization target as decimal (default 0.85). Lower = more conservative."
                },
                "horizon_weeks": {
                    "type": "integer",
                    "description": "How far ahead to scan for availability (default 52 weeks)."
                }
            },
            "required": []
        }
    },
    {
        "name": "save_snapshot",
        "description": "Save the current portfolio state as a snapshot for future change detection. Call this after reviewing changes or at the end of a planning session to establish a new baseline.",
        "input_schema": {
            "type": "object",
            "properties": {
                "notes": {
                    "type": "string",
                    "description": "Optional note describing why this snapshot was taken (e.g., 'After sprint planning', 'Post-rebalance')."
                }
            },
            "required": []
        }
    },
    {
        "name": "refresh_dashboard",
        "description": "Regenerate the Excel dashboard workbook with updated Resource Model, Capacity Summary, Role Capacity Planner, Capacity Heatmap, and Gantt chart sheets. Use this when the user asks to refresh, regenerate, or update the dashboard, or after making changes that should be reflected in the Excel output.",
        "input_schema": {
            "type": "object",
            "properties": {
                "output_path": {
                    "type": "string",
                    "description": "Optional custom output path for the dashboard file. If omitted, uses the default path (workbook name + '_Dashboard')."
                }
            },
            "required": []
        }
    },
]


# ---------------------------------------------------------------------------
# Tool Implementations
# ---------------------------------------------------------------------------
class PMOTools:
    def __init__(self):
        self.connector = ExcelConnector()
        self.engine = CapacityEngine(self.connector)
        self.snapshots = SnapshotStore()
        self.optimizer = ScheduleOptimizer(self.connector)

    def _data_timestamp(self) -> str:
        return self.connector.file_modified_time.strftime("%Y-%m-%d %H:%M")

    def _serialize_date(self, d) -> Optional[str]:
        if isinstance(d, (date, datetime)):
            return d.isoformat()
        return None

    def get_portfolio_status(self, filter_priority: str = "all",
                              include_inactive: bool = False) -> str:
        if include_inactive:
            projects = self.connector.read_portfolio()
        else:
            projects = self.connector.read_active_portfolio()

        if filter_priority and filter_priority != "all":
            projects = [p for p in projects if p.priority == filter_priority]

        result = {
            "data_as_of": self._data_timestamp(),
            "total_count": len(projects),
            "projects": []
        }

        for p in projects:
            roles = {k: f"{v:.0%}" for k, v in p.role_allocations.items() if v > 0}
            result["projects"].append({
                "id": p.id,
                "name": p.name,
                "health": p.health,
                "priority": p.priority,
                "pct_complete": f"{p.pct_complete:.0%}",
                "est_hours": p.est_hours,
                "start_date": self._serialize_date(p.start_date),
                "end_date": self._serialize_date(p.end_date),
                "duration_weeks": round(p.duration_weeks, 1) if p.duration_weeks else None,
                "sponsor": p.sponsor,
                "team": p.team,
                "pm": p.pm,
                "role_allocations": roles,
                "notes": p.notes,
            })

        return json.dumps(result, indent=2)

    def get_capacity_analysis(self) -> str:
        data = self.engine._load()
        utilization = self.engine.compute_utilization()

        scheduled = [p for p in data["active_portfolio"] if p.duration_weeks]
        unscheduled = [p for p in data["active_portfolio"] if not p.duration_weeks]

        roles_data = {}
        for role in ["pm", "dba", "ba", "functional", "technical", "developer",
                      "infrastructure", "wms"]:
            if role not in utilization:
                continue
            u = utilization[role]
            breakdown = []
            for d in sorted(u.demand_breakdown, key=lambda x: x.weekly_hours, reverse=True):
                breakdown.append({
                    "project_id": d.project_id,
                    "project_name": d.project_name,
                    "role_alloc": f"{d.role_alloc_pct:.0%}",
                    "weekly_hours": round(d.weekly_hours, 1),
                })
            roles_data[role] = {
                "supply_hrs_week": round(u.supply_hrs_week, 1),
                "demand_hrs_week": round(u.demand_hrs_week, 1),
                "utilization_pct": f"{u.utilization_pct:.0%}",
                "status": u.status,
                "demand_breakdown": breakdown,
            }

        unscheduled_list = []
        for p in unscheduled:
            roles = {k: f"{v:.0%}" for k, v in p.role_allocations.items() if v > 0}
            unscheduled_list.append({
                "id": p.id, "name": p.name, "priority": p.priority,
                "est_hours": p.est_hours, "roles": roles,
            })

        result = {
            "data_as_of": self._data_timestamp(),
            "active_projects": len(data["active_portfolio"]),
            "scheduled_projects": len(scheduled),
            "unscheduled_projects": len(unscheduled),
            "utilization_by_role": roles_data,
            "unscheduled_backlog": unscheduled_list,
        }
        return json.dumps(result, indent=2)

    def get_project_details(self, project_id: str) -> str:
        all_projects = self.connector.read_portfolio()
        search = project_id.upper().strip()

        # Try exact ID match first, then name search
        project = next((p for p in all_projects if p.id.upper() == search), None)
        if not project:
            matches = [p for p in all_projects
                       if search.lower() in p.name.lower() or search.lower() in p.id.lower()]
            if len(matches) == 1:
                project = matches[0]
            elif len(matches) > 1:
                return json.dumps({
                    "error": f"Multiple matches for '{project_id}'",
                    "matches": [{"id": p.id, "name": p.name} for p in matches]
                })
            else:
                return json.dumps({"error": f"No project found matching '{project_id}'"})

        roles = {k: v for k, v in project.role_allocations.items() if v > 0}
        demands = self.engine.compute_project_role_demand(project)

        demand_detail = []
        for d in demands:
            demand_detail.append({
                "role": d.role_key,
                "allocation": f"{d.role_alloc_pct:.0%}",
                "avg_weekly_hours": round(d.weekly_hours, 2),
                "phase_weekly_hours": {
                    phase: round(hrs, 2) for phase, hrs in d.phase_weekly_hours.items()
                }
            })

        result = {
            "data_as_of": self._data_timestamp(),
            "id": project.id,
            "name": project.name,
            "type": project.type,
            "portfolio": project.portfolio,
            "sponsor": project.sponsor,
            "health": project.health,
            "pct_complete": f"{project.pct_complete:.0%}",
            "priority": project.priority,
            "start_date": self._serialize_date(project.start_date),
            "end_date": self._serialize_date(project.end_date),
            "duration_weeks": round(project.duration_weeks, 1) if project.duration_weeks else None,
            "est_hours": project.est_hours,
            "team": project.team,
            "pm": project.pm,
            "ba": project.ba,
            "is_active": project.is_active,
            "role_allocations": {k: f"{v:.0%}" for k, v in roles.items()},
            "demand_analysis": demand_detail,
            "notes": project.notes,
        }
        return json.dumps(result, indent=2)

    def get_team_roster(self, filter_role: str = None) -> str:
        roster = self.connector.read_roster()
        if filter_role:
            roster = [m for m in roster if m.role_key == filter_role.lower()]

        members = []
        for m in roster:
            members.append({
                "name": m.name,
                "role": m.role,
                "role_key": m.role_key,
                "team": m.team,
                "vendor": m.vendor,
                "classification": m.classification,
                "weekly_hrs": m.weekly_hrs_available,
                "support_reserve_pct": f"{m.support_reserve_pct:.0%}",
                "project_capacity_pct": f"{m.project_capacity_pct:.0%}",
                "project_capacity_hrs": round(m.project_capacity_hrs, 1),
            })

        result = {
            "data_as_of": self._data_timestamp(),
            "count": len(members),
            "members": members,
        }
        return json.dumps(result, indent=2)

    def what_if_add_project(self, est_hours: float,
                             role_allocations: dict,
                             duration_weeks: float = 12,
                             priority: str = "Medium") -> str:
        # Current utilization
        current_util = self.engine.compute_utilization()
        supply = self.engine.compute_supply_by_role()
        assumptions = self.engine.assumptions

        impacts = []
        any_red = False

        for role_key, alloc_pct in role_allocations.items():
            if alloc_pct <= 0:
                continue
            avg_effort = assumptions.role_avg_efforts.get(role_key, 0.0)
            new_weekly_demand = est_hours * alloc_pct * avg_effort / duration_weeks

            current = current_util.get(role_key)
            current_demand = current.demand_hrs_week if current else 0.0
            role_supply = supply.get(role_key, 0.0)

            new_total_demand = current_demand + new_weekly_demand
            new_util = new_total_demand / role_supply if role_supply > 0 else float("inf")

            from capacity_engine import _utilization_status
            new_status = _utilization_status(new_util)
            if new_status == "RED":
                any_red = True

            impacts.append({
                "role": role_key,
                "allocation": f"{alloc_pct:.0%}",
                "new_weekly_demand_hrs": round(new_weekly_demand, 1),
                "current_demand_hrs": round(current_demand, 1),
                "new_total_demand_hrs": round(new_total_demand, 1),
                "supply_hrs": round(role_supply, 1),
                "current_utilization": f"{(current.utilization_pct if current else 0):.0%}",
                "new_utilization": f"{new_util:.0%}",
                "current_status": current.status if current else "GREEN",
                "new_status": new_status,
            })

        result = {
            "scenario": f"Add {est_hours:.0f}h project over {duration_weeks:.0f} weeks ({priority} priority)",
            "feasible": not any_red,
            "role_impacts": impacts,
        }

        if any_red:
            result["warning"] = "One or more roles would exceed 100% utilization. Mitigation needed."

        return json.dumps(result, indent=2)

    def what_if_lose_resource(self, resource_name: str = None,
                                role_key: str = None) -> str:
        roster = self.connector.read_roster()
        current_util = self.engine.compute_utilization()
        supply = self.engine.compute_supply_by_role()

        if resource_name:
            member = next((m for m in roster
                           if resource_name.lower() in m.name.lower()), None)
            if not member:
                return json.dumps({"error": f"No team member matching '{resource_name}'"})
            lost_hrs = member.project_capacity_hrs
            affected_role = member.role_key
            scenario_desc = f"Lose {member.name} ({member.role}, {lost_hrs:.1f} proj hrs/wk)"
        elif role_key:
            affected_role = role_key.lower()
            role_members = [m for m in roster if m.role_key == affected_role]
            if not role_members:
                return json.dumps({"error": f"No team members with role '{role_key}'"})
            avg_hrs = sum(m.project_capacity_hrs for m in role_members) / len(role_members)
            lost_hrs = avg_hrs
            scenario_desc = f"Lose 1 {affected_role} ({avg_hrs:.1f} avg proj hrs/wk)"
        else:
            return json.dumps({"error": "Provide either resource_name or role_key"})

        current = current_util.get(affected_role)
        old_supply = supply.get(affected_role, 0.0)
        new_supply = old_supply - lost_hrs
        demand = current.demand_hrs_week if current else 0.0

        new_util = demand / new_supply if new_supply > 0 else float("inf")
        from capacity_engine import _utilization_status
        new_status = _utilization_status(new_util)

        headcount = len([m for m in roster if m.role_key == affected_role])

        result = {
            "scenario": scenario_desc,
            "role": affected_role,
            "current_headcount": headcount,
            "new_headcount": headcount - 1,
            "current_supply_hrs": round(old_supply, 1),
            "new_supply_hrs": round(new_supply, 1),
            "demand_hrs": round(demand, 1),
            "current_utilization": f"{(current.utilization_pct if current else 0):.0%}",
            "new_utilization": f"{new_util:.0%}" if new_util != float("inf") else "INFINITE",
            "current_status": current.status if current else "GREEN",
            "new_status": new_status,
        }
        return json.dumps(result, indent=2)

    def optimize_schedule(self, target_utilization: float = 0.85,
                           horizon_weeks: int = 26,
                           extra_projects: list = None) -> str:
        result = self.optimizer.optimize_schedule(
            extra_projects=extra_projects,
            target_util=target_utilization,
            horizon_weeks=horizon_weeks,
        )
        return json.dumps(self.optimizer.result_to_json(result), indent=2)

    def suggest_dates(self, project_id: str = None,
                       est_hours: float = None,
                       role_allocations: dict = None,
                       max_utilization: float = 0.85,
                       horizon_weeks: int = 52) -> str:
        kwargs = {
            "max_util_pct": max_utilization,
            "horizon_weeks": horizon_weeks,
        }

        if project_id:
            all_projects = self.connector.read_portfolio()
            search = project_id.upper().strip()
            project = next((p for p in all_projects if p.id.upper() == search), None)
            if not project:
                matches = [p for p in all_projects
                           if search.lower() in p.name.lower() or search.lower() in p.id.lower()]
                if len(matches) == 1:
                    project = matches[0]
                else:
                    return json.dumps({"error": f"No project found matching '{project_id}'"})

            allocs = role_allocations or {k: v for k, v in project.role_allocations.items() if v > 0}
            hours = est_hours or project.est_hours
            kwargs["exclude_project_id"] = project.id
            result = self.engine.suggest_dates(hours, allocs, **kwargs)
            result["project_id"] = project.id
            result["project_name"] = project.name
        else:
            if not est_hours or not role_allocations:
                return json.dumps({
                    "error": "For hypothetical projects, provide both est_hours and role_allocations."
                })
            result = self.engine.suggest_dates(est_hours, role_allocations, **kwargs)

        return json.dumps(result, indent=2, default=str)

    def estimate_timeline(self, project_id: str = None,
                           est_hours: float = None,
                           role_allocations: dict = None,
                           max_utilization: float = 0.85,
                           concurrent_projects: int = 0) -> str:
        kwargs = {
            "max_util_pct": max_utilization,
            "concurrent_projects": concurrent_projects,
        }

        if project_id:
            # Existing project
            all_projects = self.connector.read_portfolio()
            search = project_id.upper().strip()
            project = next((p for p in all_projects if p.id.upper() == search), None)
            if not project:
                matches = [p for p in all_projects
                           if search.lower() in p.name.lower() or search.lower() in p.id.lower()]
                if len(matches) == 1:
                    project = matches[0]
                elif len(matches) > 1:
                    return json.dumps({
                        "error": f"Multiple matches for '{project_id}'",
                        "matches": [{"id": p.id, "name": p.name} for p in matches]
                    })
                else:
                    return json.dumps({"error": f"No project found matching '{project_id}'"})

            # Allow overrides
            if est_hours:
                from dataclasses import replace
                project = replace(project, est_hours=est_hours)
            if role_allocations:
                from dataclasses import replace
                merged = dict(project.role_allocations)
                merged.update(role_allocations)
                project = replace(project, role_allocations=merged)

            result = self.engine.estimate_project_duration(project, **kwargs)
        else:
            # Hypothetical project
            if not est_hours or not role_allocations:
                return json.dumps({
                    "error": "For hypothetical projects, provide both est_hours and role_allocations."
                })
            result = self.engine.estimate_duration(est_hours, role_allocations, **kwargs)

        return json.dumps(result, indent=2)

    def detect_changes(self) -> str:
        changes = self.snapshots.detect_changes(self.connector)
        return json.dumps(changes, indent=2)

    def save_snapshot(self, notes: str = "") -> str:
        snap_id = self.snapshots.save_snapshot(self.connector, notes=notes)
        snap = self.snapshots.get_latest_snapshot()
        return json.dumps({
            "snapshot_id": snap_id,
            "taken_at": snap["taken_at"],
            "project_count": snap["project_count"],
            "active_count": snap["active_count"],
            "notes": notes,
            "message": f"Snapshot #{snap_id} saved successfully.",
        }, indent=2)

    def refresh_dashboard(self, output_path: str = None) -> str:
        from excel_dashboard import DashboardGenerator
        try:
            gen = DashboardGenerator(connector=self.connector)
            path = gen.generate_all(output_path=output_path)
            return json.dumps({
                "status": "success",
                "output_path": path,
                "message": f"Dashboard regenerated successfully: {path}",
            }, indent=2)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e),
                "message": f"Dashboard generation failed: {str(e)}",
            }, indent=2)

    def execute_tool(self, name: str, input_data: dict) -> str:
        """Route tool calls to the appropriate method."""
        if name == "get_portfolio_status":
            return self.get_portfolio_status(**input_data)
        elif name == "get_capacity_analysis":
            return self.get_capacity_analysis()
        elif name == "get_project_details":
            return self.get_project_details(**input_data)
        elif name == "get_team_roster":
            return self.get_team_roster(**input_data)
        elif name == "what_if_add_project":
            return self.what_if_add_project(**input_data)
        elif name == "what_if_lose_resource":
            return self.what_if_lose_resource(**input_data)
        elif name == "optimize_schedule":
            return self.optimize_schedule(**input_data)
        elif name == "estimate_timeline":
            return self.estimate_timeline(**input_data)
        elif name == "suggest_dates":
            return self.suggest_dates(**input_data)
        elif name == "detect_changes":
            return self.detect_changes()
        elif name == "save_snapshot":
            return self.save_snapshot(**input_data)
        elif name == "refresh_dashboard":
            return self.refresh_dashboard(**input_data)
        else:
            return json.dumps({"error": f"Unknown tool: {name}"})


# ---------------------------------------------------------------------------
# Chat Loop
# ---------------------------------------------------------------------------
MODEL = "claude-sonnet-4-6"

def run_chat():
    api_key = _load_api_key()
    client = anthropic.Anthropic(api_key=api_key)
    tools = PMOTools()
    messages = []

    print("=" * 60)
    print("  ETE IT PMO Resource Planning Agent")
    print("  Powered by Claude — type 'quit' to exit")
    print("=" * 60)
    print()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        messages.append({"role": "user", "content": user_input})

        # Agentic loop: keep going until Claude stops calling tools
        while True:
            response = client.messages.create(
                model=MODEL,
                max_tokens=16000,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            # If Claude is done (no more tool calls), print and break
            if response.stop_reason == "end_turn":
                # Print text blocks
                for block in response.content:
                    if block.type == "text":
                        print(f"\nAgent: {block.text}\n")

                # Append assistant response to history
                messages.append({"role": "assistant", "content": response.content})
                break

            # Extract tool use blocks
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

            if not tool_use_blocks:
                # No tools and not end_turn — just print what we have
                for block in response.content:
                    if block.type == "text":
                        print(f"\nAgent: {block.text}\n")
                messages.append({"role": "assistant", "content": response.content})
                break

            # Append assistant response (includes tool_use blocks)
            messages.append({"role": "assistant", "content": response.content})

            # Execute each tool and collect results
            tool_results = []
            for tool_block in tool_use_blocks:
                print(f"  [calling {tool_block.name}...]")
                result = tools.execute_tool(tool_block.name, tool_block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": result,
                })

            # Send tool results back
            messages.append({"role": "user", "content": tool_results})

    tools.connector.close()
    tools.snapshots.close()


if __name__ == "__main__":
    run_chat()
