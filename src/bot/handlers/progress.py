"""Athlete progress dashboard and metrics card handler."""

import html
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User, WeightLog, WorkoutLog

logger = logging.getLogger("sportbot.handlers.progress")

router = Router(name="progress_handlers")


@router.message(F.text == "📊 My Progress")
@router.message(Command("progress"))
async def handle_progress(message: Message, session: AsyncSession) -> None:
    """Render comprehensive athlete stats, cycle completion bar, and weight tracking history."""
    telegram_user = message.from_user
    if not telegram_user:
        return

    # Fetch user
    user = await session.scalar(select(User).where(User.telegram_id == telegram_user.id))
    if not user:
        user = User(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            current_day=1,
            current_cycle=1,
            difficulty_mode="medium",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    # Aggregate total completed workouts
    total_workouts = (
        await session.scalar(
            select(func.count(WorkoutLog.id)).where(WorkoutLog.user_id == user.id)
        )
        or 0
    )

    # Fetch latest logged weight
    latest_weight = await session.scalar(
        select(WeightLog.weight_kg)
        .where(WeightLog.user_id == user.id)
        .order_by(WeightLog.logged_at.desc())
        .limit(1)
    )
    weight_str = f"{latest_weight:.1f} kg" if latest_weight else "Not recorded yet"

    # Calculate 30-day visual progress bar
    completed_days = max(0, user.current_day - 1)
    pct = int(min(100, max(0, (completed_days / 30) * 100)))
    filled_blocks = int(round(pct / 10))
    progress_bar = "▓" * filled_blocks + "░" * (10 - filled_blocks)

    raw_name = telegram_user.first_name or telegram_user.username or "Athlete"
    escaped_name = html.escape(raw_name)
    escaped_diff = html.escape(user.difficulty_mode.upper())

    text = (
        f"📊 <b>ATHLETE PROGRESS REPORT</b>\n\n"
        f"👤 <b>Athlete:</b> {escaped_name}\n"
        f"🔄 <b>Cycle:</b> Cycle {user.current_cycle}\n"
        f"🗓 <b>Current Day:</b> Day {user.current_day} of 30\n"
        f"📈 <b>Cycle Progress:</b> <code>{progress_bar}</code> {pct}%\n"
        f"⚡️ <b>Difficulty:</b> {escaped_diff}\n"
        f"🏆 <b>Total Workouts Completed:</b> {total_workouts}\n"
        f"⚖️ <b>Latest Weight:</b> {weight_str}\n\n"
        f"<i>Keep showing up. Consistency and progressive overload build athletic mastery.</i>"
    )

    await message.answer(text, parse_mode="HTML")
