"""aiogram 3 bot and dispatcher setup with database session middleware and modular handlers."""

import logging
from typing import Optional

from aiogram import Bot, Dispatcher

from src.bot.handlers import admin, base, guide, progress, settings as bot_settings, workout
from src.bot.middlewares import DbSessionMiddleware
from src.config import settings

logger = logging.getLogger("sportbot.bot")

# ---------------------------------------------------------
# Dispatcher Initialization & Middleware Registration
# ---------------------------------------------------------
dp = Dispatcher()

# Register database session injection across messages and callback queries
dp.message.middleware(DbSessionMiddleware())
dp.callback_query.middleware(DbSessionMiddleware())

# Include modular feature routers
dp.include_router(base.router)
dp.include_router(workout.router)
dp.include_router(progress.router)
dp.include_router(guide.router)
dp.include_router(bot_settings.router)
dp.include_router(admin.router)

# ---------------------------------------------------------
# Bot Instance with Safe Startup Fallback
# ---------------------------------------------------------
bot: Optional[Bot] = None
if settings.BOT_TOKEN.strip():
    bot = Bot(token=settings.BOT_TOKEN)
else:
    logger.warning("BOT_TOKEN is empty or not set. Telegram Bot initialization skipped.")
