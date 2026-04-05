"""Capacity router — utilization summary + weekly heatmap.

Heatmap logic replicates `data_layer.load_weekly_heatmap` without the
Streamlit caching so we can return a JSON-friendly shape.
"""

from collections import defaultdict
from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, Depends, Query

from ..deps import get_capacity
from ..engines import CapacityEngine, ROLE_KEYS
from ..schemas.capacity import (
    HeatmapResponse,
    HeatmapRow,
    RoleUtilizationOut,
    UtilizationResponse,
)

router = APIRouter(prefix="/capacity", tags=["capacity"])


@router.get("/utilization", response_model=UtilizationResponse)
def utilization(engine: CapacityEngine = Depends(get_capacity)) -> UtilizationResponse:
    util = engine.compute_utilization()
    return UtilizationResponse(
        roles={k: RoleUtilizationOut.from_dataclass(v) for k, v in util.items()}
    )


@router.get("/heatmap", response_model=HeatmapResponse)
def heatmap(
    weeks: int = Query(26, ge=1, le=104),
    engine: CapacityEngine = Depends(get_capacity),
) -> HeatmapResponse:
    active = engine.active_projects
    supply = engine.compute_supply_by_role()

    today = date.today()
    days_to_monday = (7 - today.weekday()) % 7
    scan_start = today + timedelta(days=days_to_monday if days_to_monday else 0)

    demand_grid: "defaultdict[str, defaultdict[int, float]]" = defaultdict(
        lambda: defaultdict(float)
    )

    for project in active:
        timeline = engine.compute_weekly_demand_timeline(project)
        for role_key, snapshots in timeline.items():
            for snap in snapshots:
                delta_days = (snap.week_start - scan_start).days
                week_idx = 0 if delta_days < 0 else delta_days // 7
                if week_idx < weeks:
                    demand_grid[role_key][week_idx] += snap.role_demand_hrs

    week_labels: List[str] = [
        (scan_start + timedelta(weeks=i)).strftime("%b %d") for i in range(weeks)
    ]

    rows: List[HeatmapRow] = []
    for role in ROLE_KEYS:
        role_supply = supply.get(role, 0.0)
        cells: List[float] = []
        for i in range(weeks):
            demand = demand_grid.get(role, {}).get(i, 0.0)
            util = demand / role_supply if role_supply > 0 else 0.0
            cells.append(round(util, 4))
        rows.append(
            HeatmapRow(
                role_key=role,
                supply_hrs_week=round(role_supply, 2),
                cells=cells,
            )
        )

    return HeatmapResponse(weeks=week_labels, rows=rows)
