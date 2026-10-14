"""Settings handler for switching athlete difficulty tiers in chat."""

import html
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import get_settings_kb
from src.db.models import User

logger = logging.getLogger("sportbot.handlers.settings")

router = Router(name="settings_handlers")


def build_settings_message(current_mode: str) -> str:
    """Format description of difficulty tiers and current selection."""
    mode_escaped = html.escape(current_mode.capitalize())
    return (
        f"⚙️ <b>TRAINING DIFFICULTY SETTINGS</b>\n\n"
        f"• <b>Active Difficulty:</b> <code>{mode_escaped}</code>\n\n"
        f"<b>DIFFICULTY TIERS:</b>\n"
        f"🟢 <b>Light:</b> Controlled base volume, joint adaptation, and foundation motor patterns.\n"
        f"🟡 <b>Medium:</b> Balanced hypertrophy protocol, parallel bars, and progressive levers.\n"
        f"🔴 <b>Hard:</b> Peak mechanical disadvantage, deficit ranges, and strict tempos.\n\n"
        f"Select a new difficulty mode below to apply across all upcoming workouts:"
    )


@router.message(F.text == "⚙️ Settings")
@router.message(Command("settings"))
async def handle_settings(message: Message, session: AsyncSession) -> None:
    """Send settings menu with difficulty toggles."""
    telegram_user = message.from_user
    if not telegram_user:
        return

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

    text = build_settings_message(user.difficulty_mode)
    await message.answer(
        text,
        reply_markup=get_settings_kb(user.difficulty_mode),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("set_diff:"))
async def handle_set_difficulty(callback: CallbackQuery, session: AsyncSession) -> None:
    """Toggle difficulty mode, commit to DB, and update inline keyboard status."""
    new_mode = callback.data.split(":", 1)[1].strip().lower()
    if new_mode not in ("light", "medium", "hard"):
        await callback.answer("Invalid difficulty option.", show_alert=True)
        return

    telegram_user = callback.from_user
    user = await session.scalar(select(User).where(User.telegram_id == telegram_user.id))
    if not user:
        await callback.answer("Athlete profile not found.", show_alert=True)
        return

    if user.difficulty_mode == new_mode:
        await callback.answer(f"Already set to {new_mode.capitalize()}.", show_alert=False)
        return

    old_mode = user.difficulty_mode
    user.difficulty_mode = new_mode
    await session.commit()
    await session.refresh(user)

    logger.info("Athlete %d changed difficulty from %s to %s", user.telegram_id, old_mode, new_mode)

    text = build_settings_message(user.difficulty_mode)
    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=get_settings_kb(user.difficulty_mode),
            parse_mode="HTML",
        )

    await callback.answer(f"✅ Difficulty updated to {new_mode.capitalize()}!", show_alert=False)
