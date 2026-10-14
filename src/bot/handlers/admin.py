"""Administrative command handler and system telemetry dashboard."""

import html
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import get_admin_metrics_kb
from src.config import settings
from src.db.models import User, WorkoutLog

logger = logging.getLogger("sportbot.handlers.admin")

router = Router(name="admin_handlers")


async def render_admin_metrics_text(session: AsyncSession) -> str:
    """Aggregate database statistics and format admin summary card."""
    total_athletes = (await session.scalar(select(func.count(User.id)))) or 0
    total_workouts = (await session.scalar(select(func.count(WorkoutLog.id)))) or 0

    diff_rows = (
        await session.execute(
            select(User.difficulty_mode, func.count(User.id)).group_by(User.difficulty_mode)
        )
    ).all()
    diff_map = {mode: count for mode, count in diff_rows}

    cycle_rows = (
        await session.execute(
            select(User.current_cycle, func.count(User.id)).group_by(User.current_cycle)
        )
    ).all()

    diff_lines = [
        f"  • {html.escape(m.capitalize())}: {diff_map.get(m, 0)}"
        for m in ("light", "medium", "hard")
    ]
    diff_text = "\n".join(diff_lines)

    cycle_lines = [f"  • Cycle {c}: {count} athletes" for c, count in cycle_rows]
    cycle_text = "\n".join(cycle_lines) if cycle_lines else "  • No cycle distribution data"

    return (
        f"🛠 <b>SPORTBOT // ADMIN SYSTEM DASHBOARD</b>\n\n"
        f"👥 <b>Total Registered Athletes:</b> {total_athletes}\n"
        f"🏋️‍♂️ <b>Total Completed Workouts:</b> {total_workouts}\n\n"
        f"📊 <b>Difficulty Distribution:</b>\n{diff_text}\n\n"
        f"🔄 <b>Active Cycles:</b>\n{cycle_text}\n\n"
        f"<i>Live system state from production SQLite database.</i>"
    )


@router.message(Command("admin"))
async def handle_admin(message: Message, session: AsyncSession) -> None:
    """Process /admin command and restrict access strictly to configured ADMIN_IDS."""
    telegram_user = message.from_user
    if not telegram_user or telegram_user.id not in settings.admin_ids_list:
        logger.warning(
            "Unauthorized /admin attempt by id=%s",
            telegram_user.id if telegram_user else "unknown",
        )
        await message.answer(
            "⛔️ <b>Access denied.</b> This command is restricted to administrators.",
            parse_mode="HTML",
        )
        return

    text = await render_admin_metrics_text(session)
    await message.answer(text, reply_markup=get_admin_metrics_kb(), parse_mode="HTML")


@router.callback_query(F.data == "admin_refresh")
async def handle_admin_refresh(callback: CallbackQuery, session: AsyncSession) -> None:
    """Refresh admin dashboard metrics on button tap."""
    telegram_user = callback.from_user
    if not telegram_user or telegram_user.id not in settings.admin_ids_list:
        await callback.answer("Access denied.", show_alert=True)
        return

    text = await render_admin_metrics_text(session)
    if callback.message:
        await callback.message.edit_text(
            text, reply_markup=get_admin_metrics_kb(), parse_mode="HTML"
        )

    await callback.answer("✅ Metrics refreshed!", show_alert=False)
