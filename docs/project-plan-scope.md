# Project Plan Feature — Scope Tracker

A persistent record of what we've built, what's tested, what Brett has approved, and what's still on the table. Updated with every iteration.

**Status legend:**
- 🟢 **Done** — built, committed, pushed
- 🧪 **Tested** — automated tests passing
- ✅ **Approved** — Brett has reviewed on the live site and signed off
- 🟡 **In progress** — actively being worked on
- ⚪ **Not started** — planned but not begun
- 🔮 **Deferred** — explicitly on the list but not scheduled; decision point noted

---

## Iteration 1 — MVP (shipped)

The minimum to have a usable project plan on the Project Detail page.

### Backend

| Item | Status | Notes |
|---|---|---|
| `POST /api/v1/tasks/{project_id}` — create task | 🟢 🧪 | 201 on success, returns full TaskOut |
| `PATCH /api/v1/tasks/id/{task_id}` — update task | 🟢 🧪 | Partial update, requires project_id in body for audit |
| `DELETE /api/v1/tasks/id/{task_id}` — delete task | 🟢 🧪 | Hard delete, 204 on success |
| `POST /api/v1/tasks/id/{task_id}/complete` — mark done | 🟢 🧪 | Sets status=complete, progress_pct=100 |
| Pydantic schemas: `TaskCreate`, `TaskUpdate` (new file) + existing `TaskOut` | 🟢 | `backend/app/schemas/task_write.py` |
| Tests for task router | 🟢 🧪 | 8 tests: list, create, create-under-milestone, update, complete, delete, 404s |

### Frontend

| Item | Status | Notes |
|---|---|---|
| `PlanPanel.tsx` component | 🟢 | Grouped table: milestones as phases, tasks nested. Collapsible phases. |
| `EditTaskDialog.tsx` component | 🟢 | Create + edit form with delete button in edit mode |
| `useTasks.ts` hook extended | 🟢 | Adds useCreateTask, useUpdateTask, useCompleteTask, useDeleteTask |
| Task fields rendered: title, assignee, status, priority, start/end dates, est hours | 🟢 | Plus phase grouping, click-to-complete, hover-to-edit |
| "Add phase" button | 🟢 | Uses native prompt() for simplicity — upgrade later if needed |
| "Add task" button per phase | 🟢 | Pre-fills milestone_id in dialog |
| Unassigned tasks bucket | 🟢 | Auto-shown if tasks have `milestone_id = null` |
| PlanPanel integrated on ProjectDetail page | 🟢 | Full-width section above Milestones/Comments grid |

### Data model

| Item | Status | Notes |
|---|---|---|
| Milestones as phases (no new table) | 🟢 | Reusing existing `project_milestones` |
| No schema changes for Iteration 1 | 🟢 | All fields already exist on `project_tasks` |

### Test status

**273 backend tests passing** (8 new task tests + 265 existing).
Frontend has zero tests — same as before, consistent with existing gap.

### Awaiting Brett's approval

Open `/portfolio/DEMO-001` (or any project) on the live site after deploy and:
- [ ] Verify Plan section appears
- [ ] Click "Add phase", name it, confirm it shows
- [ ] Click "Add task" on that phase, fill in details, save
- [ ] Click the circle icon next to a task to mark complete
- [ ] Click a task title to edit it
- [ ] Delete a task via the edit dialog
- [ ] Collapse/expand a phase via the chevron

---

## Explicitly out of scope for Iteration 1 (decide later)

Each of these is a concrete future iteration. Brett decides if/when to implement.

| Feature | Brett's decision | Notes |
|---|---|---|
| **Per-phase rollups** (task count, hours sum, % complete, date range) | ⏳ Undecided | Visual upgrade — matches Monday.com style |
| **Drag to reorder tasks within a phase** | ⏳ Undecided | Uses existing `sort_order` column |
| **Drag to reorder phases** | ⏳ Undecided | Uses milestones `sort_order` |
| **Move tasks between phases** | ⏳ Undecided | Changes `milestone_id` |
| **Per-task budget** | ⏳ Undecided | Requires new `budget` column on `project_tasks` |
| **Deliverables as a distinct concept** | ⏳ Undecided | Could reuse `milestone_type='deliverable'` |
| **Task-level Gantt view** | ⏳ Undecided | Separate "Timeline" sub-tab; leverages existing start/end dates |
| **Task dependencies UI** | ⏳ Undecided | `task_dependencies` table already exists |
| **Subtasks / parent-child hierarchy** | ⏳ Undecided | `parent_task_id` column already exists |
| **Keyboard shortcuts** (Enter to add, Cmd+D to duplicate, etc.) | ⏳ Undecided | Quality-of-life for power users |
| **Inline editing** (vs. edit dialog) | ⏳ Undecided | Table cells become editable in place |
| **Task comments** | ⏳ Undecided | Separate comment thread per task |
| **Task attachments** | ⏳ Undecided | Requires file storage infrastructure |
| **Task activity log** | ⏳ Undecided | Who changed what and when |
| **Bulk operations** (select many, update status, delete) | ⏳ Undecided | Common PMO workflow |
| **Task templates** (reusable task patterns per project type) | ⏳ Undecided | Speeds up plan creation |
| **Baseline vs actual** (snapshot plan at kickoff, compare later) | ⏳ Undecided | Integrates with existing snapshot system |
| **Effort rollup into project capacity calculations** | ⏳ Undecided | Task `est_hours` could feed `compute_utilization` |
| **Auto-status from task completion** (all tasks done → phase marked complete) | ⏳ Undecided | Uses existing `rollup_milestone_progress` method |
| **Task filtering/search** (by assignee, status, etc.) | ⏳ Undecided | Standard table UX |
| **Export plan to CSV/PDF** | ⏳ Undecided | For sharing outside the app |
| **Critical path calculation** | ⏳ Undecided | Requires dependencies to be populated |
| **Auto-schedule tasks** based on dependencies + assignee capacity | ⏳ Undecided | Major feature; integrates with existing scheduler |

---

## Approval workflow

After each iteration ships:
1. Claude updates this document with status markers (🟢 Done, 🧪 Tested)
2. Brett reviews on the live site
3. Brett marks items as ✅ Approved or sends feedback
4. Any new scope items discovered during review get added to the "out of scope" table for future iteration decisions

---

## Change log

| Date | Iteration | Change |
|---|---|---|
| 2026-04-09 | Iteration 1 | Initial scope document created. Started building MVP. |
| 2026-04-09 | Iteration 1 | MVP shipped: task CRUD API, PlanPanel with phase grouping, EditTaskDialog, ProjectDetail integration. 273 tests passing. Awaiting Brett's approval. Also fixed 2 unrelated pre-existing test failures (demand formula + scheduler priority) that were drifting from the live engine. |
