"""Daily workout notification and streak reminder worker for SportBot."""

import asyncio
from datetime import datetime
import html
import logging
from typing import Set, Tuple

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from sqlalchemy import select

from src.config import settings
from src.db.models import CycleDay, User, WorkoutLog
from src.db.session import async_session_factory

logger = logging.getLogger("sportbot.services.reminder")


async def send_pending_reminders(bot: Bot, today_str: str, notified_today: Set[Tuple[int, str]]) -> None:
    """Scan users without completed workout for current day and send a reminder."""
    async with async_session_factory() as session:
        try:
            users = (await session.scalars(select(User))).all()
        except Exception as ex:
            logger.error("Failed to query users in ReminderWorker: %s", ex)
            return

        for user in users:
            key = (user.id, today_str)
            if key in notified_today:
                continue

            # Verify if user has already completed workout for current_day in current_cycle
            try:
                completed = await session.scalar(
                    select(WorkoutLog).where(
                        WorkoutLog.user_id == user.id,
                        WorkoutLog.cycle_number == user.current_cycle,
                        WorkoutLog.day_number == user.current_day,
                    )
                )
                if completed:
                    # User completed workout today, record as handled to prevent reminders
                    notified_today.add(key)
                    continue

                # Fetch cycle day context
                cycle_day = await session.scalar(
                    select(CycleDay).where(CycleDay.day_number == user.current_day)
                )
                day_title = cycle_day.title if cycle_day else f"Day {user.current_day}"
                focus_areas = (
                    "Active Recovery & Joint Mobility"
                    if (cycle_day and cycle_day.is_rest_day)
                    else (cycle_day.focus_areas if cycle_day else "Calisthenics Protocol")
                )

                raw_name = user.username or "Athlete"
                name = html.escape(raw_name)
                escaped_title = html.escape(day_title)
                escaped_focus = html.escape(focus_areas)

                text = (
                    f"🌅 <b>Good morning, {name}!</b>\n\n"
                    f"Today is <b>Day {user.current_day} of 30</b>: <b>{escaped_title}</b>.\n"
                    f"🎯 <b>Focus:</b> {escaped_focus}\n\n"
                    f"Stay disciplined and conquer your session!"
                )

                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🚀 Open Today's Workout",
                                web_app=WebAppInfo(url=settings.get_webapp_url()),
                            )
                        ]
                    ]
                )

                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
                notified_today.add(key)
                logger.info(
                    "Sent daily reminder to user id=%d (tg_id=%d) for day %d",
                    user.id,
                    user.telegram_id,
                    user.current_day,
                )
            except TelegramForbiddenError:
                logger.warning("Athlete tg_id=%d blocked the bot. Skipping.", user.telegram_id)
                notified_today.add(key)
            except TelegramBadRequest as ex:
                logger.warning("TelegramBadRequest when notifying tg_id=%d: %s", user.telegram_id, ex)
                notified_today.add(key)
            except Exception as ex:
                logger.error("Failed to notify athlete tg_id=%d: %s", user.telegram_id, ex)


async def run_reminder_worker(bot: Bot, check_interval_seconds: int = 3600) -> None:
    """Infinite background task checking and delivering daily workout reminders."""
    logger.info("Starting ReminderWorker with %ds interval...", check_interval_seconds)
    notified_today: Set[Tuple[int, str]] = set()

    try:
        while True:
            now = datetime.now()
            today_str = now.strftime("%Y-%m-%d")
            # Prune records from previous calendar days
            notified_today = {entry for entry in notified_today if entry[1] == today_str}

            # Check and notify starting from 09:00 morning time
            if now.hour >= 9:
                await send_pending_reminders(bot, today_str, notified_today)

            await asyncio.sleep(check_interval_seconds)
    except asyncio.CancelledError:
        logger.info("ReminderWorker received cancellation.")
