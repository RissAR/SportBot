"""aiogram 3 bot and dispatcher setup with safe startup fallback."""

import logging
from typing import Optional

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from src.config import settings

logger = logging.getLogger("sportbot.bot")

router = Router(name="base_router")


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """Handle /start command and present Mini App launch button."""
    webapp_url = settings.get_webapp_url()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔥 Open SportBot",
                    web_app=WebAppInfo(url=webapp_url),
                )
            ]
        ]
    )
    await message.answer(
        "👋 Welcome to **SportBot**!\n\n"
        "Your personal 30-day bodyweight workout cycle.\n"
        "Tap the button below to launch the app:",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


dp = Dispatcher()
dp.include_router(router)

bot: Optional[Bot] = None
if settings.BOT_TOKEN.strip():
    bot = Bot(token=settings.BOT_TOKEN)
else:
    logger.warning("BOT_TOKEN is empty or not set. Telegram Bot initialization skipped.")
