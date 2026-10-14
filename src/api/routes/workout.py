"""Workout completion endpoint with per-user asyncio concurrency locking."""

import asyncio
from collections import defaultdict
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import get_current_user
from src.api.schemas import WorkoutCompleteRequest, WorkoutCompleteResponse
from src.db.models import User, WorkoutExerciseLog, WorkoutLog
from src.db.session import get_db

logger = logging.getLogger("sportbot.routes.workout")

router = APIRouter()

# In-memory per-user locks preventing race conditions / double-tap submissions
_user_locks: defaultdict[int, asyncio.Lock] = defaultdict(asyncio.Lock)


def get_user_lock(user_id: int) -> asyncio.Lock:
    """Retrieve or initialize asyncio.Lock for a given athlete user_id."""
    return _user_locks[user_id]


@router.post("/complete", response_model=WorkoutCompleteResponse)
async def complete_workout(
    payload: WorkoutCompleteRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> WorkoutCompleteResponse:
    """Submit completed workout logs, enforce strict current-day validation, and advance cycle day."""
    # Strict rule: only user.current_day can be completed
    if payload.day_number != user.current_day:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only the current day workout can be completed. Past days are view-only.",
        )

    # Concurrency control per user
    async with get_user_lock(user.id):
        # Check if already completed in the current cycle
        existing = await session.scalar(
            select(WorkoutLog).where(
                WorkoutLog.user_id == user.id,
                WorkoutLog.cycle_number == user.current_cycle,
                WorkoutLog.day_number == payload.day_number,
            )
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Workout for Day {payload.day_number} in Cycle {user.current_cycle} is already completed.",
            )

        # Record Workout session
        workout_log = WorkoutLog(
            user_id=user.id,
            cycle_number=user.current_cycle,
            day_number=payload.day_number,
            difficulty_mode=payload.difficulty_mode or user.difficulty_mode,
            duration_seconds=payload.duration_seconds,
        )
        session.add(workout_log)
        await session.flush()

        # Record individual exercise performances
        for ex in payload.exercises:
            session.add(
                WorkoutExerciseLog(
                    workout_log_id=workout_log.id,
                    exercise_id=ex.exercise_id,
                    sets_completed=ex.sets_completed,
                    value_completed=ex.value_completed,
                    is_completed=ex.is_completed,
                )
            )

        # Day transition logic
        if user.current_day < 30:
            user.current_day += 1
            cycle_completed = False
            next_day = user.current_day
            next_cycle = user.current_cycle
            message = f"Workout Day {payload.day_number} successfully completed. Advanced to Day {next_day}."
        else:
            cycle_completed = True
            next_day = 30
            next_cycle = user.current_cycle
            message = "Cycle completed! Log your bodyweight in /api/weight to advance to the next 30-day cycle."

        await session.commit()
        await session.refresh(user)

        logger.info(
            "Athlete %d completed Day %d (Cycle %d). Next: Day %d, Cycle %d",
            user.telegram_id,
            payload.day_number,
            user.current_cycle,
            next_day,
            next_cycle,
        )

        return WorkoutCompleteResponse(
            success=True,
            message=message,
            cycle_completed=cycle_completed,
            next_day=next_day,
            next_cycle=next_cycle,
        )
