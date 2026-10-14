"""Middleware injecting database sessions into aiogram handlers."""

from collections.abc import Awaitable, Callable
from typing import Any, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src.db.session import async_session_factory


class DbSessionMiddleware(BaseMiddleware):
    """Provides an isolated AsyncSession to each event handler and ensures clean closure."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with async_session_factory() as session:
            data["session"] = session
            return await handler(event, data)
