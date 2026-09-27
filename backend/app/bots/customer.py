"""Customer bot: /start greeting with the shop WebApp button.

Exposes `customer_router(settings) -> Router`. Status-change messages are sent
by `TelegramNotifier`, not from here.
"""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from .. import texts
from ..config import Settings


def customer_router(settings: Settings) -> Router:
    router = Router(name="customer")

    @router.message(CommandStart())
    async def start(message: Message) -> None:
        if settings.webapp_url:
            url = f"{settings.webapp_url.rstrip('/')}/app/"
            markup = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text=texts.BTN_OPEN_SHOP, web_app=WebAppInfo(url=url))]]
            )
            await message.answer(texts.CUSTOMER_GREETING, reply_markup=markup)
        else:
            await message.answer(texts.CUSTOMER_GREETING_NO_WEBAPP)

    return router
