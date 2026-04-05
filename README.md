# PMO Planner

An AI-powered resource planning tool for IT Project Management Office (PMO) teams. Make smarter resource allocation decisions with capacity-driven scheduling, what-if scenario analysis, and real-time utilization dashboards — without manually crunching spreadsheets.

---

## What Does This Tool Do?

Managing a portfolio of IT projects means constantly juggling people, timelines, and priorities. This tool reads your live PMO workbook and lets you have a conversation with your data:

- **"Can we take on a new 400-hour project?"** -- It calculates whether your team has the capacity, broken down by role, and tells you exactly where the bottlenecks are.
- **"What happens if we lose a developer?"** -- It runs the scenario instantly and shows you which roles go from green to red.
- **"Optimize the schedule for all projects"** -- It uses a constraint solver to find the best start dates that keep everyone under 85% utilization while respecting project priorities.
- **"What changed since last time?"** -- It compares the current workbook to the last saved snapshot and highlights new projects, date shifts, priority changes, and progress updates.

No formulas to build. No pivot tables to maintain. Just ask.

---

## Key Features

| Feature | Description |
|---|---|
| **Portfolio Status** | View all active projects with health, priority, completion %, estimated hours, dates, and role allocations. Filter by priority level. |
| **Capacity Analysis** | See supply vs. demand for each of the 8 roles (Developer, BA, Technical, Functional, PM, DBA, Infrastructure, WMS) with GREEN/YELLOW/RED status indicators. |
| **Project Deep Dive** | Look up any project by ID or name to see full details including per-role demand calculations broken down by SDLC phase. |
| **Team Roster** | Browse the full team roster with each person's role, weekly hours, support reserve, and available project capacity. |
| **What-If: Add Project** | Model the impact of adding a hypothetical project before committing. See exactly which roles would be pushed over capacity. |
| **What-If: Lose Resource** | Assess the risk of losing a specific team member or a headcount in any role. |
| **Schedule Optimization** | An OR-Tools constraint solver that assigns optimal start dates to unscheduled projects and adjusts existing ones, respecting priority hierarchy. |
| **Change Detection** | Snapshot-based diffing that tracks new projects, removed projects, status changes, progress updates, date shifts, priority changes, and hours changes between sessions. |
| **Planning** | Capacity-driven project scheduling + what-if scenario analysis. See below. |

---

## Planning Module

The Planning page is where scheduling and capacity decisions happen. It has two connected tabs that share state.

### How it works

```
                        ┌─────────────────────────────┐
                        │    Modification Stack        │
                        │  (shared between both tabs)  │
                        │                              │
                        │  + Add project               │
                        │  + Exclude person            │
                        │  + Add hire                  │
                        │  + Shift dates               │
                        │  + Change allocation         │
                        │  + Resize scope              │
                        │  + Cancel project            │
                        └──────────┬──────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼                             ▼
          ┌─────────────────┐          ┌──────────────────┐
          │   What-If Tab   │          │ Auto-Schedule Tab │
          │                 │          │                   │
          │ Before / After  │          │ Project placement │
          │ utilization     │          │ by capacity       │
          │ comparison      │          │                   │
          │ per role        │          │ Start dates       │
          │                 │          │ Wait times        │
          │ Status changes  │          │ Bottleneck roles  │
          │ Delta arrows    │          │ Feasibility       │
          └─────────────────┘          └──────────────────┘
```

### Typical workflow

**Step 1 — Check the baseline.** Open Planning. The Auto-Schedule tab runs automatically and shows which plannable projects can start now, which are queued behind capacity constraints, and which can't be scheduled at all. Note the bottleneck roles.

**Step 2 — Ask "what if?"** Switch to the What-If tab. Build a scenario by stacking modifications:

| Modification | What it answers |
|---|---|
| **Add project** | "Can we absorb a new 800-hour initiative starting in May?" |
| **Cancel project** | "If we drop this one, does anything else unblock?" |
| **Exclude person** | "What happens if we lose Marcus?" |
| **Add hire** | "If we hire another Developer at 40h/week, how much headroom opens up?" |
| **Shift dates** | "What if we push Project X out 6 weeks?" |
| **Change allocation** | "What if we bump Developer from 60% to 80% on this project?" |
| **Resize scope** | "What if this project turns out to be twice as big?" |

The right panel updates live — before/after utilization bars per role, delta arrows showing percentage-point changes, and a headline summarizing what broke or improved.

**Step 3 — See the scheduling impact.** Switch back to Auto-Schedule. Your modifications carry over (the tab badge shows how many are active). The scheduler re-runs against the modified portfolio and roster so you can see how your what-if changes affect project placement and timelines.

**Step 4 — Iterate.** Add, remove, or swap modifications. Both tabs re-compute instantly. When you find a combination that works, you have a data-backed answer to bring to the conversation.

### Key concepts

- **Nothing is saved.** Scenarios are ephemeral — they exist only while you're on the Planning page. No database writes, no side effects, no risk.
- **Modifications compose.** Stack as many as you want. "Add a project + exclude a person + hire a replacement" runs as a single scenario.
- **The scheduler respects admin thresholds.** The utilization ceiling defaults to the `util_stretched_max` value from Admin Settings (default 100%). Lower it to 85% if you want headroom built in.
- **Priority drives placement order.** The scheduler places Highest-priority projects first, then High, Medium, Low. Within a tier, larger projects (more hours) go first. This means a High-priority 200-hour project gets calendar space before a Medium-priority 50-hour one.
- **Bottleneck role** = the role that prevented an earlier start. If "Functional" is the bottleneck for 3 projects, that's a signal to either hire, reallocate, or push work around.

---

## Demo Data

The `seed_data.sql` file in this repo contains **anonymized demo data only** — fictional project names, fake people, fictional vendors, and scaled/jittered dollar amounts. Any fresh deploy (Railway, local dev) boots from this seed and shows the demo dataset.

To regenerate the demo seed from a private real database:

```bash
# 1. Keep your real data locally (never committed; *.db is gitignored)
cp pmo_data.db pmo_data.real.db

# 2. Run the anonymizer (deterministic — same input + seed → same output)
python3 scripts/anonymize_data.py \
  --source pmo_data.real.db \
  --dest pmo_data.demo.db

# 3. Dump the demo DB to the seed file
sqlite3 pmo_data.demo.db .dump > seed_data.sql
```

To force Railway (or any deployment) to wipe its volume and reseed from `seed_data.sql`, set `RESEED_ON_BOOT=true` in the service environment, redeploy, then remove the env var once the boot completes.

---

## How It Works

```
+---------------------+        +------------------+        +------------------+
|                     |        |                  |        |                  |
|   Excel Workbook    +------->+  Excel Connector +------->+  Capacity Engine |
|   (3 sheets)        |        |  (reads live     |        |  (supply/demand  |
|                     |        |   data)          |        |   calculations)  |
+---------------------+        +------------------+        +--------+---------+
                                                                    |
                                                                    v
+---------------------+        +------------------+        +------------------+
|                     |        |                  |        |                  |
|   Streamlit UI      +<-------+  PMO Agent       +<-------+  Claude API      |
|   (chat interface)  |        |  (tool router    |        |  (reasoning +    |
|                     |        |   + 9 tools)     |        |   tool calls)    |
+---------------------+        +--------+---------+        +------------------+
                                        |
                               +--------+---------+
                               |                  |
                          +----+----+     +-------+--------+
                          |         |     |                |
                          | Schedule|     | Snapshot Store |
                          |Optimizer|     | (SQLite change |
                          |(OR-Tools|     |  detection)    |
                          | solver) |     |                |
                          +---------+     +----------------+
```

**The flow:**
1. You type a question in the chat interface
2. Claude reads your question and decides which tools to call
3. The tools pull live data from your Excel workbook and run calculations
4. Claude synthesizes the results into a clear, actionable answer
5. Snapshots are saved to SQLite so you can track what changed between sessions

---

## Example Questions You Can Ask

**Portfolio overview:**
- "What's the status of all Highest priority projects?"
- "Show me projects that are behind schedule"
- "How many active projects do we have?"

**Capacity and utilization:**
- "Show me current capacity utilization"
- "Which roles are over 80% utilized?"
- "What's the demand breakdown for developers?"

**Scenario planning:**
- "Can we add a 400-hour project with 60% Developer and 20% BA allocation?"
- "What if we lose Colin Olson?"
- "What happens if we lose a developer headcount?"

**Scheduling:**
- "Optimize the schedule for all projects"
- "Find the best start dates to keep utilization under 80%"

**Change tracking:**
- "What changed since last time?"
- "Save a snapshot after this planning session"

**Project details:**
- "Tell me about DEMO-001"
- "Show me the details for the SAP project"

---

## Setup Instructions

### Prerequisites

- Python 3.9 or later
- An Anthropic API key (get one at [console.anthropic.com](https://console.anthropic.com))
- A PMO data source (SQLite database or Excel workbook) placed in the project directory

### 1. Install Dependencies

```bash
pip install streamlit anthropic openpyxl ortools
```

### 2. Configure Your API Key

Create a `.env` file in the project directory:

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Or set it as an environment variable:

```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

You can also enter the key directly in the Streamlit sidebar when the app launches.

### 3. Place the Excel Workbook

Ensure the file `ETE_PMO_Resource_Budget_Manager 3 (1).xlsx` is in the project root directory. The workbook must have these three sheets:

- **Project Portfolio** -- project list with IDs, names, priorities, dates, hours, and role allocation percentages
- **Team Roster** -- team members with roles, weekly hours, and support reserve percentages
- **RM_Assumptions** -- time allocation rules, SDLC phase weights, role effort percentages, and supply calculations

### 4. Run the Application

**Streamlit web interface (recommended):**

```bash
streamlit run app.py
```

Then open your browser to `http://localhost:8501`.

**Command-line interface:**

```bash
python pmo_agent.py
```

This starts an interactive terminal chat session.

---

## Architecture Overview

| File | Purpose |
|---|---|
| `app.py` | Streamlit web UI. Manages chat session state, renders the sidebar with live metrics, and runs the agent tool-use loop against the Claude API. |
| `pmo_agent.py` | Core agent logic. Defines the system prompt, 9 tool schemas, and the `PMOTools` class that routes tool calls to the appropriate engine. Also contains a standalone CLI chat loop. |
| `excel_connector.py` | Data access layer. Reads the three Excel sheets using openpyxl and returns structured dataclasses (`Project`, `TeamMember`, `RMAssumptions`). Handles all column mapping and type conversion. |
| `capacity_engine.py` | Business logic for resource planning. Computes supply by role (from roster), demand by role (from project allocations and SDLC phase weights), utilization percentages, and weekly demand timelines. |
| `schedule_optimizer.py` | Constraint-based schedule optimization using Google OR-Tools CP-SAT solver. Finds optimal project start dates that minimize delay while keeping all roles under target utilization. Enforces priority hierarchy (Highest = immovable, High = max 2-week shift, Medium = 8 weeks, Low = 16 weeks). |
| `snapshot_store.py` | SQLite-backed persistence layer. Saves portfolio snapshots for change detection between sessions. Also maintains a decision log for audit trails. |

### Key Design Decisions

- **Read-only by design.** The agent never writes back to the Excel workbook. All analysis is non-destructive.
- **Tool-use architecture.** Claude decides which tools to call based on the question, enabling multi-step reasoning (e.g., checking capacity before recommending a schedule).
- **SDLC-phase-aware demand.** Demand calculations account for how different roles have different effort levels across project phases (Discovery through Deploy), not just flat averages.
- **Priority hierarchy is absolute.** The optimizer treats Highest-priority projects as immovable anchors and only shifts lower-priority work to resolve conflicts.
- **Model:** Uses `claude-sonnet-4-6` for fast, cost-effective responses with strong tool-use capabilities.
