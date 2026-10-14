"""Telegram Mini App HMAC-SHA256 authentication and user dependencies."""

import hashlib
import hmac
import json
import logging
import time
import urllib.parse
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.models import User
from src.db.session import get_db

logger = logging.getLogger("sportbot.auth")


def validate_telegram_init_data(init_data: str, bot_token: str) -> dict:
    """Validate Telegram initData using HMAC-SHA256 signature and freshness check.

    Returns parsed dict of query parameters including 'user' dict.
    Raises HTTPException(401) on invalid signature, expired data, or malformed payload.
    """
    if not bot_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server misconfiguration: BOT_TOKEN is missing.",
        )

    try:
        parsed_qsl = urllib.parse.parse_qsl(init_data, keep_blank_values=True)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed Telegram initData query string.",
        ) from exc

    params = dict(parsed_qsl)
    received_hash = params.pop("hash", None)
    if not received_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing hash parameter in Telegram initData.",
        )

    # Reconstruct data_check_string: alphabetical sort by key, key=value joined by \n
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))

    # Secret key derivation: HMAC-SHA256 of bot token with key "WebAppData"
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram signature: verification failed.",
        )

    # Replay protection: max 86400 seconds (24h)
    auth_date_str = params.get("auth_date")
    if not auth_date_str or not auth_date_str.isdigit():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid auth_date in Telegram initData.",
        )

    auth_date = int(auth_date_str)
    if time.time() - auth_date > 86400:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telegram initData has expired (older than 24 hours).",
        )

    # Parse embedded user object
    user_str = params.get("user")
    if user_str:
        try:
            params["user"] = json.loads(user_str)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user JSON payload in Telegram initData.",
            ) from exc

    return params


async def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_telegram_init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
    x_dev_telegram_id: Optional[str] = Header(None, alias="X-Dev-Telegram-Id"),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Dependency that authenticates the user from Telegram initData and performs JIT provisioning."""
    raw_init_data: Optional[str] = None

    if authorization:
        if authorization.lower().startswith("tma "):
            raw_init_data = authorization[4:].strip()
        else:
            raw_init_data = authorization.strip()
    elif x_telegram_init_data:
        raw_init_data = x_telegram_init_data.strip()

    telegram_id: Optional[int] = None
    username: Optional[str] = None

    if raw_init_data:
        validated_data = validate_telegram_init_data(raw_init_data, settings.BOT_TOKEN)
        user_info = validated_data.get("user")
        if isinstance(user_info, dict) and "id" in user_info:
            telegram_id = int(user_info["id"])
            username = user_info.get("username")
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Telegram initData does not contain valid user information.",
            )
    else:
        # Development fallback (only when settings.DEBUG is True)
        if settings.DEBUG:
            if x_dev_telegram_id and x_dev_telegram_id.strip().isdigit():
                telegram_id = int(x_dev_telegram_id.strip())
                username = f"dev_user_{telegram_id}"
            elif settings.admin_ids_list:
                telegram_id = settings.admin_ids_list[0]
                username = "dev_admin"
            else:
                telegram_id = 999999999
                username = "dev_athlete"
            logger.debug("DEBUG mode active: emulated Telegram user %d", telegram_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required: missing Telegram initData.",
            )

    if not telegram_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to resolve athlete identity.",
        )

    # JIT User Provisioning (Fetch or create atomically)
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if not user:
        logger.info("JIT User Provisioning: creating new athlete telegram_id=%d", telegram_id)
        user = User(
            telegram_id=telegram_id,
            username=username,
            current_day=1,
            current_cycle=1,
            difficulty_mode="medium",
        )
        session.add(user)
        await session.flush()
    else:
        # Update username if changed
        if username and user.username != username:
            user.username = username
            await session.flush()

    return user


async def verify_admin(user: User = Depends(get_current_user)) -> User:
    """Dependency that asserts the authenticated user has administrative privileges."""
    if user.telegram_id not in settings.admin_ids_list:
        logger.warning(
            "Forbidden admin access attempt by telegram_id=%d (allowed: %s)",
            user.telegram_id,
            settings.admin_ids_list,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required: your Telegram ID is not authorized.",
        )
    return user
