"""Entry point for SportBot: Concurrent execution of FastAPI and aiogram Bot with graceful shutdown."""

import asyncio
import logging
import signal
import sys
import uvicorn

from src.api.app import app
from src.bot.instance import bot, dp
from src.config import settings

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


async def main() -> None:
    """Initialize services and manage concurrent lifecycle and signals."""
    config = uvicorn.Config(
        app=app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="debug" if settings.DEBUG else "info",
    )
    server = uvicorn.Server(config)
    server.install_signal_handlers = False

    loop = asyncio.get_running_loop()

    def handle_shutdown_signal(sig_name: str) -> None:
        logger.info("Received %s signal, initiating graceful shutdown...", sig_name)
        server.should_exit = True
        if bot and settings.BOT_TOKEN.strip():
            asyncio.create_task(dp.stop_polling())

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, handle_shutdown_signal, sig.name)
        except NotImplementedError:
            pass

    await asyncio.gather(
        run_api(server),
        run_bot(),
    )
    logger.info("SportBot services shut down gracefully.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("SportBot application terminated.")
