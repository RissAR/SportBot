"""Entry point for SportBot: Concurrent execution of FastAPI, aiogram Bot, and background workers with graceful shutdown."""

import asyncio
import logging
import signal
import sys
import uvicorn
from sqlalchemy import text

from src.api.app import app
from src.bot.instance import bot, dp
from src.config import settings
from src.db.seed import seed_initial_data
from src.db.session import async_session_factory, init_db
from src.services.backup import run_backup_worker
from src.services.reminder import run_reminder_worker

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("sportbot.main")


async def run_api(server: uvicorn.Server) -> None:
    """Run Uvicorn ASGI server."""
    logger.info("Starting FastAPI server on %s:%s...", settings.API_HOST, settings.API_PORT)
    try:
        await server.serve()
    except asyncio.CancelledError:
        logger.info("FastAPI server received cancellation.")


async def run_bot() -> None:
    """Run aiogram bot polling if token is configured."""
    if not bot or not settings.BOT_TOKEN.strip():
        logger.warning("BOT_TOKEN is empty or not configured. Skipping Telegram bot polling.")
        return

    logger.info("Starting Telegram Bot polling...")
    try:
        await dp.start_polling(bot, handle_signals=False)
    except asyncio.CancelledError:
        logger.info("Telegram Bot polling received cancellation.")
    finally:
        await bot.session.close()
        logger.info("Telegram Bot session closed.")


async def flush_database_wal() -> None:
    """Execute final WAL checkpoint on shutdown to ensure zero uncommitted disk pages."""
    try:
        logger.info("Executing final PRAGMA wal_checkpoint(TRUNCATE)...")
        async with async_session_factory() as session:
            await session.execute(text("PRAGMA wal_checkpoint(TRUNCATE)"))
        logger.info("SQLite WAL journal successfully truncated.")
    except Exception as ex:
        logger.warning("Failed to truncate WAL journal on shutdown: %s", ex)


async def main() -> None:
    """Initialize database, seed data, and manage concurrent services with graceful signal shutdown."""
    logger.info("Initializing database schema and initial data...")
    await init_db()
    await seed_initial_data()

    config = uvicorn.Config(
        app=app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="debug" if settings.DEBUG else "info",
    )
    server = uvicorn.Server(config)
    server.install_signal_handlers = False

    tasks: list[asyncio.Task] = []

    api_task = asyncio.create_task(run_api(server), name="fastapi_server")
    tasks.append(api_task)

    if bot and settings.BOT_TOKEN.strip():
        bot_task = asyncio.create_task(run_bot(), name="telegram_bot")
        tasks.append(bot_task)
        reminder_task = asyncio.create_task(run_reminder_worker(bot), name="reminder_worker")
        tasks.append(reminder_task)

    backup_task = asyncio.create_task(run_backup_worker(), name="backup_worker")
    tasks.append(backup_task)

    loop = asyncio.get_running_loop()

    def handle_shutdown_signal(sig_name: str) -> None:
        logger.info("Received %s signal, initiating graceful shutdown...", sig_name)
        server.should_exit = True
        if bot and settings.BOT_TOKEN.strip():
            asyncio.create_task(dp.stop_polling())
        for t in tasks:
            if not t.done():
                t.cancel()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, handle_shutdown_signal, sig.name)
        except NotImplementedError:
            pass

    # Wait until one of the primary tasks terminates or is cancelled
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    # Cancel any pending background loops (e.g. backup or reminder workers)
    for t in pending:
        if not t.done():
            t.cancel()

    if pending:
        await asyncio.gather(*pending, return_exceptions=True)

    # Final WAL flush
    await flush_database_wal()
    logger.info("SportBot services shut down gracefully.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("SportBot application terminated.")
