"""Today's workout preview handler with structured exercises and protocol formatting."""

import html
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import get_workout_inline_kb
from src.db.models import CycleDay, CycleDayExercise, Exercise, ExerciseProgression, User

logger = logging.getLogger("sportbot.handlers.workout")

router = Router(name="workout_handlers")


@router.message(F.text == "🗓 Today's Workout")
@router.message(Command("today"))
async def handle_today_workout(message: Message, session: AsyncSession) -> None:
    """Send detailed overview of the athlete's current active cycle day."""
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

    # Fetch CycleDay
    cycle_day = await session.scalar(
        select(CycleDay).where(CycleDay.day_number == user.current_day)
    )
    if not cycle_day:
        await message.answer(
            f"⚠️ Cycle day {user.current_day} was not found. Please contact support.",
            parse_mode="HTML",
        )
        return

    day_num = cycle_day.day_number
    focus_areas = html.escape(cycle_day.focus_areas)
    diff_tier = html.escape(user.difficulty_mode.capitalize())

    if cycle_day.is_rest_day:
        text = (
            f"🌴 <b>DAY {day_num}/30: FULL RECOVERY & REST</b>\n\n"
            f"🎯 <b>Focus:</b> {focus_areas}\n\n"
            f"<b>RECOVERY GUIDELINES:</b>\n"
            f"• 💧 Hydration: Drink minimum 2.5–3L clean water throughout the day\n"
            f"• 😴 Sleep: Ensure 8+ hours of uninterrupted sleep for cellular repair\n"
            f"• 🚶 Mobility: 20–30 min brisk outdoor walk and gentle joint circles\n\n"
            f"<i>Adaptation and muscle hypertrophy occur while resting. Honor your recovery!</i>"
        )
        await message.answer(text, reply_markup=get_workout_inline_kb(), parse_mode="HTML")
        return

    # Fetch exercises with matching progression tier
    query = (
        select(Exercise, ExerciseProgression)
        .join(CycleDayExercise, CycleDayExercise.exercise_id == Exercise.id)
        .join(
            ExerciseProgression,
            (ExerciseProgression.exercise_id == Exercise.id)
            & (ExerciseProgression.difficulty_tier == user.difficulty_mode),
        )
        .where(CycleDayExercise.cycle_day_id == cycle_day.id)
        .order_by(CycleDayExercise.order)
    )

    rows = (await session.execute(query)).all()

    exercise_lines: list[str] = []
    for idx, (ex, prog) in enumerate(rows, start=1):
        metric_suffix = "reps" if ex.metric_type == "reps" else ("sec" if ex.metric_type == "seconds" else "min")
        ex_line = (
            f"{idx}. <b>{html.escape(ex.name)}</b> — {prog.target_sets} sets × {prog.target_value} {metric_suffix} "
            f"(Tempo: <code>{html.escape(prog.tempo)}</code>, Rest: {prog.rest_seconds}s)"
        )
        exercise_lines.append(ex_line)

    protocol_text = "\n".join(exercise_lines) if exercise_lines else "• Bodyweight protocol assigned in Mini App"
    block_title = html.escape(cycle_day.title)

    text = (
        f"⚡️ <b>{block_title}</b>\n"
        f"🎯 <b>Focus:</b> {focus_areas}\n"
        f"⏱ <b>Target Duration:</b> 50–55 min\n\n"
        f"<b>1. DYNAMIC WARM-UP (8–10 min):</b>\n"
        f"• Wrists, shoulders, scapula, hips, and knees mobility drills.\n\n"
        f"<b>2. MAIN PROTOCOL ({diff_tier}):</b>\n"
        f"{protocol_text}\n\n"
        f"<b>3. COOL-DOWN (5–7 min):</b>\n"
        f"• Chest & lats stretch, cat-cow spinal mobility, deep diaphragmatic breathing."
    )

    await message.answer(
        text,
        reply_markup=get_workout_inline_kb(),
        parse_mode="HTML",
    )
