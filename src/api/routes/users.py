"""User profile and difficulty configuration endpoints."""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import get_current_user
from src.api.schemas import DifficultyUpdateRequest, UserProfileResponse
from src.db.models import User, WeightLog, WorkoutLog
from src.db.session import get_db

logger = logging.getLogger("sportbot.routes.users")

router = APIRouter()


async def build_user_profile_response(user: User, session: AsyncSession) -> UserProfileResponse:
    """Helper to aggregate athlete statistics into UserProfileResponse."""
    total_workouts = (
        await session.scalar(
            select(func.count(WorkoutLog.id)).where(WorkoutLog.user_id == user.id)
        )
        or 0
    )

    latest_weight = await session.scalar(
        select(WeightLog.weight_kg)
        .where(WeightLog.user_id == user.id)
        .order_by(WeightLog.logged_at.desc())
        .limit(1)
    )

    return UserProfileResponse(
        telegram_id=user.telegram_id,
        username=user.username,
        current_day=user.current_day,
        current_cycle=user.current_cycle,
        difficulty_mode=user.difficulty_mode,
        total_workouts_completed=total_workouts,
        latest_weight=latest_weight,
    )


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """Retrieve current authenticated athlete profile and workout metrics."""
    return await build_user_profile_response(user, session)


@router.patch("/difficulty", response_model=UserProfileResponse)
async def update_difficulty(
    payload: DifficultyUpdateRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """Update training difficulty mode (light, medium, hard)."""
    logger.info(
        "Athlete %d updated difficulty from %s to %s",
        user.telegram_id,
        user.difficulty_mode,
        payload.difficulty_mode,
    )
    user.difficulty_mode = payload.difficulty_mode
    await session.commit()
    await session.refresh(user)
    return await build_user_profile_response(user, session)
