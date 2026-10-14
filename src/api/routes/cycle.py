"""Cycle calendar, daily workout retrieval, and day inspection endpoints."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import get_current_user
from src.api.schemas import (
    DEFAULT_COOLDOWN_STEPS,
    DEFAULT_WARMUP_STEPS,
    CycleDaysOverviewResponse,
    CycleDaySummary,
    ExerciseDetailResponse,
    TodayWorkoutResponse,
)
from src.db.models import CycleDay, CycleDayExercise, Exercise, ExerciseProgression, User
from src.db.session import get_db

logger = logging.getLogger("sportbot.routes.cycle")

router = APIRouter()


async def get_workout_for_day(
    day_number: int,
    cycle_number: int,
    difficulty_mode: str,
    session: AsyncSession,
) -> TodayWorkoutResponse:
    """Helper to query CycleDay, associated exercises and progressions for a specific day."""
    cycle_day = await session.scalar(
        select(CycleDay).where(CycleDay.day_number == day_number)
    )
    if not cycle_day:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cycle day {day_number} not found in database.",
        )

    if cycle_day.is_rest_day:
        return TodayWorkoutResponse(
            day_number=cycle_day.day_number,
            cycle_number=cycle_number,
            block_type=cycle_day.block_type,
            title=cycle_day.title,
            focus_areas=cycle_day.focus_areas,
            is_rest_day=True,
            warmup_steps=[],
            exercises=[],
            cooldown_steps=[],
            recovery_guidelines=(
                "Active hydration (minimum 2.5-3L water), 8+ hours quality sleep, "
                "20-30 min brisk walk and light joint mobility. Prioritize CNS recovery."
            ),
        )

    # Fetch assigned exercises and matching progression tier
    query = (
        select(Exercise, ExerciseProgression)
        .join(CycleDayExercise, CycleDayExercise.exercise_id == Exercise.id)
        .join(
            ExerciseProgression,
            (ExerciseProgression.exercise_id == Exercise.id)
            & (ExerciseProgression.difficulty_tier == difficulty_mode),
        )
        .where(CycleDayExercise.cycle_day_id == cycle_day.id)
        .order_by(CycleDayExercise.order)
    )

    rows = (await session.execute(query)).all()

    exercises_list: List[ExerciseDetailResponse] = []
    for exercise, progression in rows:
        exercises_list.append(
            ExerciseDetailResponse(
                id=exercise.id,
                slug=exercise.slug,
                name=exercise.name,
                category=exercise.category,
                metric_type=exercise.metric_type,
                progression_name=progression.progression_name,
                target_sets=progression.target_sets,
                target_value=progression.target_value,
                tempo=progression.tempo,
                rest_seconds=progression.rest_seconds,
                description=exercise.description,
                technique_tips=exercise.technique_tips,
            )
        )

    return TodayWorkoutResponse(
        day_number=cycle_day.day_number,
        cycle_number=cycle_number,
        block_type=cycle_day.block_type,
        title=cycle_day.title,
        focus_areas=cycle_day.focus_areas,
        is_rest_day=False,
        warmup_steps=DEFAULT_WARMUP_STEPS,
        exercises=exercises_list,
        cooldown_steps=DEFAULT_COOLDOWN_STEPS,
        recovery_guidelines=None,
    )


@router.get("/today", response_model=TodayWorkoutResponse)
async def get_today_workout(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TodayWorkoutResponse:
    """Retrieve full workout protocol for the athlete's current active day."""
    return await get_workout_for_day(
        day_number=user.current_day,
        cycle_number=user.current_cycle,
        difficulty_mode=user.difficulty_mode,
        session=session,
    )


@router.get("/days", response_model=CycleDaysOverviewResponse)
async def get_cycle_days_overview(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> CycleDaysOverviewResponse:
    """Retrieve all 30 days of the training cycle with relative progress statuses."""
    cycle_days = (
        await session.scalars(select(CycleDay).order_by(CycleDay.day_number))
    ).all()

    summaries: List[CycleDaySummary] = []
    for day in cycle_days:
        if day.day_number < user.current_day:
            day_status = "completed"
        elif day.day_number == user.current_day:
            day_status = "current"
        else:
            day_status = "locked"

        summaries.append(
            CycleDaySummary(
                day_number=day.day_number,
                block_type=day.block_type,
                title=day.title,
                focus_areas=day.focus_areas,
                is_rest_day=day.is_rest_day,
                status=day_status,
            )
        )

    return CycleDaysOverviewResponse(
        cycle_number=user.current_cycle,
        current_day=user.current_day,
        days=summaries,
    )


@router.get("/days/{day_number}", response_model=TodayWorkoutResponse)
async def inspect_cycle_day(
    day_number: int = Path(..., ge=1, le=30, description="Cycle day number (1-30)"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TodayWorkoutResponse:
    """Inspect exercises and protocol of any day in the cycle (view-only)."""
    return await get_workout_for_day(
        day_number=day_number,
        cycle_number=user.current_cycle,
        difficulty_mode=user.difficulty_mode,
        session=session,
    )
