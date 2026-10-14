"""Administrative metrics and management endpoints."""

import logging
from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import verify_admin
from src.api.schemas import AdminMetricsResponse
from src.db.models import User, WorkoutLog
from src.db.session import get_db

logger = logging.getLogger("sportbot.routes.admin")

router = APIRouter()


@router.get("/metrics", response_model=AdminMetricsResponse)
async def get_admin_metrics(
    admin: User = Depends(verify_admin),
    session: AsyncSession = Depends(get_db),
) -> AdminMetricsResponse:
    """Retrieve global system metrics, user growth, and workout completions."""
    total_athletes = (await session.scalar(select(func.count(User.id)))) or 0
    total_workouts = (await session.scalar(select(func.count(WorkoutLog.id)))) or 0

    diff_rows = (
        await session.execute(
            select(User.difficulty_mode, func.count(User.id)).group_by(User.difficulty_mode)
        )
    ).all()
    difficulty_dist: Dict[str, int] = {str(mode): int(count) for mode, count in diff_rows}

    cycle_rows = (
        await session.execute(
            select(User.current_cycle, func.count(User.id)).group_by(User.current_cycle)
        )
    ).all()
    cycle_dist: Dict[int, int] = {int(cycle): int(count) for cycle, count in cycle_rows}

    logger.info("Admin %d requested system metrics", admin.telegram_id)

    return AdminMetricsResponse(
        total_athletes=total_athletes,
        total_workouts_completed=total_workouts,
        difficulty_distribution=difficulty_dist,
        active_cycles_distribution=cycle_dist,
    )
