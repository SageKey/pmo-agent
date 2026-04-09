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

## Iteration 1 — MVP ✅ APPROVED (2026-04-09)

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

### Brett approved (2026-04-09)

All items in Iteration 1 are ✅ Approved.

- [x] Plan section appears on project detail page
- [x] Add phase works
- [x] Add task works with phase pre-fill
- [x] Click circle → mark complete
- [x] Click title → edit dialog
- [x] Delete via edit dialog
- [x] Collapse/expand phases

---

## Iteration 2 — Inline editing + phase rollups (shipped)

Two deferred items pulled in by Brett to transform the plan from "a grouped table" into "a Monday.com-style board."

### Frontend — Inline editing

| Item | Status | Notes |
|---|---|---|
| Title: click to edit inline (text input) | 🟢 | Blur or Enter saves, Escape cancels |
| Assignee: click to edit inline (text input) | 🟢 | Empty string becomes null |
| Status: click to open dropdown, select, save | 🟢 | Pill-style trigger, popover menu, click-outside to close |
| Priority: same dropdown pattern | 🟢 | 4 options: Highest/High/Medium/Low |
| Est hours: click to edit inline (number input) | 🟢 | Right-aligned, tabular-nums |
| Start/end dates: click to open native date picker | 🟢 | Each editable independently |
| Edit dialog retained for advanced fields (description, delete) | 🟢 | Pencil icon on hover opens full dialog |
| `InlineText` / `InlineSelect` / `InlineDate` / `InlineNumber` primitives | 🟢 | Reusable in PlanPanel.tsx |

### Frontend — Per-phase rollups

| Item | Status | Notes |
|---|---|---|
| Task count pill | 🟢 | "N tasks" pill next to phase title |
| Total estimated hours | 🟢 | Sum of `est_hours` for tasks in phase |
| % complete (weighted by hours) | 🟢 | sum(complete hours) / sum(all hours) |
| Earliest start → latest end date range | 🟢 | Min start / max end across phase tasks |
| Mini progress bar next to % | 🟢 | Sky bar, turns emerald at 100% |
| `computeRollup()` helper function | 🟢 | Pure function, memoized per phase |

### Tests

| Item | Status | Notes |
|---|---|---|
| Backend tests unchanged | 🧪 | 273 passing — no new backend work this iteration |
| Inline editing verified via existing task PATCH endpoint tests | 🧪 | Each field change goes through PATCH /tasks/id/{id} |
| Rollup calculations: visual verification only | ⏳ | Frontend still has 0 tests (existing gap) |

### Awaiting Brett's approval

Open any project on the live site after deploy and:
- [ ] Phase headers show: count pill, hours, % complete bar, date range
- [ ] Click a status pill → dropdown opens → select different → saves
- [ ] Click priority pill → same pattern
- [ ] Click task title → becomes input → Enter saves
- [ ] Click assignee → becomes input → blur saves
- [ ] Click a date → date picker opens → pick new date → saves
- [ ] Click est hours → numeric input → Enter saves
- [ ] Pencil icon on hover still opens full edit dialog
- [ ] Escape cancels in-progress edit without saving

---

## Explicitly out of scope for Iteration 1 (decide later)

Each of these is a concrete future iteration. Brett decides if/when to implement.

| Feature | Brett's decision | Notes |
|---|---|---|
| **Per-phase rollups** (task count, hours sum, % complete, date range) | 🟡 Iteration 2 | Pulled in 2026-04-09 |
| **Drag to reorder tasks within a phase** | ⏳ Undecided | Uses existing `sort_order` column |
| **Drag to reorder phases** | ⏳ Undecided | Uses milestones `sort_order` |
| **Move tasks between phases** | ⏳ Undecided | Changes `milestone_id` |
| **Per-task budget** | ⏳ Undecided | Requires new `budget` column on `project_tasks` |
| **Deliverables as a distinct concept** | ⏳ Undecided | Could reuse `milestone_type='deliverable'` |
| **Task-level Gantt view** | ⏳ Undecided | Separate "Timeline" sub-tab; leverages existing start/end dates |
| **Task dependencies UI** | ⏳ Undecided | `task_dependencies` table already exists |
| **Subtasks / parent-child hierarchy** | ⏳ Undecided | `parent_task_id` column already exists |
| **Keyboard shortcuts** (Enter to add, Cmd+D to duplicate, etc.) | ⏳ Undecided | Quality-of-life for power users |
| **Inline editing** (vs. edit dialog) | 🟡 Iteration 2 | Pulled in 2026-04-09 |
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
| 2026-04-09 | Iteration 1 | ✅ Brett approved Iteration 1 on the live site. Ready for Iteration 2 scope selection from the deferred list. |
| 2026-04-09 | Iteration 2 | Brett picked inline editing + phase rollups. Shipped: 4 inline editor primitives (InlineText/Select/Date/Number), all task columns editable in place, rollup strip on every phase header with count/hours/%/dates + progress bar. 273 tests passing. Awaiting review. |
