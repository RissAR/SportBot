"""Base bot handlers: /start, /help, and JIT user provisioning."""

import html
import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import get_main_reply_keyboard
from src.db.models import User

logger = logging.getLogger("sportbot.handlers.base")

router = Router(name="base_handlers")


@router.message(CommandStart())
@router.message(Command("help"))
async def handle_start_or_help(message: Message, session: AsyncSession) -> None:
    """Handle /start and /help commands with JIT user provisioning and main menu reply keyboard."""
    telegram_user = message.from_user
    if not telegram_user:
        return

    # JIT User Provisioning
    user = await session.scalar(select(User).where(User.telegram_id == telegram_user.id))
    if not user:
        logger.info("JIT Bot Provisioning: registering athlete telegram_id=%d", telegram_user.id)
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
    else:
        # Sync username if changed
        if telegram_user.username and user.username != telegram_user.username:
            user.username = telegram_user.username
            await session.commit()

    raw_name = telegram_user.first_name or telegram_user.username or "Athlete"
    escaped_name = html.escape(raw_name)
    difficulty_label = html.escape(user.difficulty_mode.capitalize())

    welcome_text = (
        f"👋 Welcome to <b>SportBot</b>, {escaped_name}!\n\n"
        f"Your personal 30-day calisthenics & bodyweight workout companion.\n"
        f"• <b>Current Cycle:</b> Cycle {user.current_cycle} (Day {user.current_day}/30)\n"
        f"• <b>Difficulty:</b> {difficulty_label}\n\n"
        f"Use the menu below to launch the Mini App or explore today's workout."
    )

    await message.answer(
        welcome_text,
        reply_markup=get_main_reply_keyboard(),
        parse_mode="HTML",
    )
