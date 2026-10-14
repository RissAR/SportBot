"""Telegram bot Reply and Inline keyboard builders."""

from typing import Sequence

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from src.config import settings
from src.db.models import Exercise


def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Build permanent main menu Reply keyboard with WebApp launcher."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🔥 Open SportBot",
                    web_app=WebAppInfo(url=settings.get_webapp_url()),
                )
            ],
            [
                KeyboardButton(text="🗓 Today's Workout"),
                KeyboardButton(text="📊 My Progress"),
            ],
            [
                KeyboardButton(text="📖 Exercise Guide"),
                KeyboardButton(text="⚙️ Settings"),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def get_workout_inline_kb() -> InlineKeyboardMarkup:
    """Build inline keyboard leading to Mini App workout session."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Open in Mini App",
                    web_app=WebAppInfo(url=settings.get_webapp_url()),
                )
            ]
        ]
    )


def get_guide_categories_kb() -> InlineKeyboardMarkup:
    """Build inline keyboard selecting calisthenics movement categories."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💪 Push", callback_data="guide_cat:push"),
                InlineKeyboardButton(text="🧗 Pull", callback_data="guide_cat:pull"),
            ],
            [
                InlineKeyboardButton(text="🦵 Legs", callback_data="guide_cat:legs"),
                InlineKeyboardButton(text="⚡️ Core", callback_data="guide_cat:core"),
            ],
            [
                InlineKeyboardButton(text="🏃 Cardio", callback_data="guide_cat:cardio"),
            ],
        ]
    )


def get_guide_exercises_kb(category: str, exercises: Sequence[Exercise]) -> InlineKeyboardMarkup:
    """Build inline keyboard listing exercises for a category with a back button."""
    buttons: list[list[InlineKeyboardButton]] = []
    for ex in exercises:
        buttons.append([InlineKeyboardButton(text=ex.name, callback_data=f"guide_ex:{ex.slug}")])

    buttons.append([InlineKeyboardButton(text="⬅️ Back to Categories", callback_data="guide_home")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_exercise_detail_kb(category: str) -> InlineKeyboardMarkup:
    """Build inline keyboard on exercise detail view allowing quick navigation back."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Back to List",
                    callback_data=f"guide_cat:{category}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Guide Home",
                    callback_data="guide_home",
                )
            ],
        ]
    )


def get_settings_kb(current_difficulty: str) -> InlineKeyboardMarkup:
    """Build inline keyboard for toggling training difficulty modes."""
    cur = current_difficulty.lower()
    btn_light = f"🟢 Light {'(Current)' if cur == 'light' else ''}"
    btn_medium = f"🟡 Medium {'(Current)' if cur == 'medium' else ''}"
    btn_hard = f"🔴 Hard {'(Current)' if cur == 'hard' else ''}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=btn_light, callback_data="set_diff:light")],
            [InlineKeyboardButton(text=btn_medium, callback_data="set_diff:medium")],
            [InlineKeyboardButton(text=btn_hard, callback_data="set_diff:hard")],
        ]
    )


def get_admin_metrics_kb() -> InlineKeyboardMarkup:
    """Build inline keyboard for the administrative dashboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Refresh Metrics", callback_data="admin_refresh")]
        ]
    )
