"""Weight check-in and cycle progression endpoints."""

import logging
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import get_current_user
from src.api.schemas import (
    WeightHistoryItem,
    WeightHistoryResponse,
    WeightLogRequest,
    WeightLogResponse,
)
from src.db.models import User, WeightLog
from src.db.session import get_db

logger = logging.getLogger("sportbot.routes.weight")

router = APIRouter()


@router.post("", response_model=WeightLogResponse)
async def log_weight(
    payload: WeightLogRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> WeightLogResponse:
    """Log athlete bodyweight check-in. If on Day 30, reset to Day 1 of the next cycle."""
    weight_log = WeightLog(
        user_id=user.id,
        weight_kg=payload.weight_kg,
        cycle_number=payload.cycle_number,
    )
    session.add(weight_log)

    is_cycle_reset = False
    if user.current_day == 30:
        logger.info(
            "Cycle %d finished for athlete %d. Resetting to Day 1 of Cycle %d",
            user.current_cycle,
            user.telegram_id,
            user.current_cycle + 1,
        )
        user.current_day = 1
        user.current_cycle += 1
        is_cycle_reset = True

    await session.commit()
    await session.refresh(weight_log)

    return WeightLogResponse(
        id=weight_log.id,
        weight_kg=weight_log.weight_kg,
        cycle_number=weight_log.cycle_number,
        logged_at=weight_log.logged_at.isoformat(),
        is_cycle_reset=is_cycle_reset,
    )


@router.get("/history", response_model=WeightHistoryResponse)
async def get_weight_history(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> WeightHistoryResponse:
    """Retrieve full chronological bodyweight history for the current athlete."""
    logs = (
        await session.scalars(
            select(WeightLog)
            .where(WeightLog.user_id == user.id)
            .order_by(WeightLog.logged_at.asc())
        )
    ).all()

    history_items: List[WeightHistoryItem] = [
        WeightHistoryItem(
            id=log.id,
            weight_kg=log.weight_kg,
            cycle_number=log.cycle_number,
            logged_at=log.logged_at.isoformat(),
        )
        for log in logs
    ]

    return WeightHistoryResponse(history=history_items)
