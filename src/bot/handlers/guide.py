"""Interactive calisthenics exercise guide and biomechanics library handler."""

import html
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.bot.keyboards import (
    get_exercise_detail_kb,
    get_guide_categories_kb,
    get_guide_exercises_kb,
)
from src.db.models import Exercise

logger = logging.getLogger("sportbot.handlers.guide")

router = Router(name="guide_handlers")


CATEGORY_DESCRIPTIONS = {
    "push": "💪 <b>PUSH MOVEMENTS</b>\nFocus on chest, anterior deltoids, and triceps hypertrophy and joint protection.",
    "pull": "🧗 <b>PULL MOVEMENTS</b>\nFocus on lats, upper back, rear delts, and biceps strength with scapular control.",
    "legs": "🦵 <b>LEG MOVEMENTS</b>\nUnilateral quad, glute, hamstring, and tendon resilience without spinal compression.",
    "core": "⚡️ <b>CORE & ANTERIOR CHAIN</b>\nIsometric and dynamic anti-extension abdominal control on bars.",
    "cardio": "🏃 <b>CARDIO & AEROBIC CONDITIONING</b>\nSprint intervals and Zone 2 mitochondrial recovery protocols.",
}


@router.message(F.text == "📖 Exercise Guide")
@router.message(Command("guide"))
async def handle_guide_home(message: Message) -> None:
    """Send movement category selector."""
    text = (
        "📖 <b>CALISTHENICS EXERCISE GUIDE</b>\n\n"
        "Explore movement biomechanics, form execution, and injury-prevention cues tailored for 85 kg athletes.\n\n"
        "Select a movement category below:"
    )
    await message.answer(text, reply_markup=get_guide_categories_kb(), parse_mode="HTML")


@router.callback_query(F.data == "guide_home")
async def handle_guide_home_cb(callback: CallbackQuery) -> None:
    """Navigate back to category selection."""
    text = (
        "📖 <b>CALISTHENICS EXERCISE GUIDE</b>\n\n"
        "Explore movement biomechanics, form execution, and injury-prevention cues tailored for 85 kg athletes.\n\n"
        "Select a movement category below:"
    )
    if callback.message:
        await callback.message.edit_text(
            text, reply_markup=get_guide_categories_kb(), parse_mode="HTML"
        )
    await callback.answer()


@router.callback_query(F.data.startswith("guide_cat:"))
async def handle_guide_category(callback: CallbackQuery, session: AsyncSession) -> None:
    """List all exercises belonging to the selected category."""
    category = callback.data.split(":", 1)[1].strip()
    exercises = (
        await session.scalars(
            select(Exercise).where(Exercise.category == category).order_by(Exercise.id)
        )
    ).all()

    header = CATEGORY_DESCRIPTIONS.get(category, f"<b>{html.escape(category.upper())} MOVEMENTS</b>")
    text = f"{header}\n\nSelect an exercise to review full biomechanics and safety cues:"

    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=get_guide_exercises_kb(category, exercises),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data.startswith("guide_ex:"))
async def handle_guide_exercise_detail(callback: CallbackQuery, session: AsyncSession) -> None:
    """Render comprehensive biomechanics card, safety tips, and progression tiers for a single exercise."""
    slug = callback.data.split(":", 1)[1].strip()

    exercise = await session.scalar(
        select(Exercise)
        .options(selectinload(Exercise.progressions))
        .where(Exercise.slug == slug)
    )

    if not exercise or not callback.message:
        await callback.answer("Exercise not found.", show_alert=True)
        return

    name = html.escape(exercise.name)
    category_title = html.escape(exercise.category.upper())
    description = html.escape(exercise.description)
    tips = html.escape(exercise.technique_tips)

    # Format progression tiers
    prog_lines: list[str] = []
    # Sort progressions light -> medium -> hard
    tier_order = {"light": 1, "medium": 2, "hard": 3}
    sorted_progs = sorted(exercise.progressions, key=lambda p: tier_order.get(p.difficulty_tier, 9))

    metric_name = "reps" if exercise.metric_type == "reps" else ("seconds" if exercise.metric_type == "seconds" else "minutes")
    for p in sorted_progs:
        tier_label = html.escape(p.difficulty_tier.capitalize())
        prog_name = html.escape(p.progression_name)
        prog_lines.append(
            f"• <b>{tier_label}:</b> {prog_name} — {p.target_sets} sets × {p.target_value} {metric_name} "
            f"(Tempo: <code>{html.escape(p.tempo)}</code>, Rest: {p.rest_seconds}s)"
        )

    progressions_text = "\n".join(prog_lines)

    card_text = (
        f"🎯 <b>{name}</b> [{category_title}]\n\n"
        f"<b>📖 BIOMECHANICS:</b>\n{description}\n\n"
        f"💡 <b>SAFETY & CUES (85 KG ATHLETE):</b>\n{tips}\n\n"
        f"📊 <b>PROGRESSION TIERS:</b>\n{progressions_text}"
    )

    await callback.message.edit_text(
        card_text,
        reply_markup=get_exercise_detail_kb(exercise.category),
        parse_mode="HTML",
    )
    await callback.answer()
