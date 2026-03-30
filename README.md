# ETE PMO Resource Planning Agent

An AI-powered assistant that helps IT Project Management Office (PMO) teams make smarter resource allocation decisions. Instead of manually crunching spreadsheets, you ask questions in plain English and get instant, data-driven answers about your project portfolio, team capacity, and scheduling options.

Built for the ETE IT PMO team. Powered by Claude and connected directly to your existing Excel workbook.

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
- "Tell me about ETE-83"
- "Show me the details for the SAP project"

---

## Setup Instructions

### Prerequisites

- Python 3.9 or later
- An Anthropic API key (get one at [console.anthropic.com](https://console.anthropic.com))
- The ETE PMO Excel workbook placed in the project directory

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
