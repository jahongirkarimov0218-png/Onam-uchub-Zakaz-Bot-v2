from unittest.mock import AsyncMock

from app.bots.customer import customer_router
from app.config import Settings


def _start_handler(router):
    return router.message.handlers[0].callback


async def test_start_with_webapp_url_sends_greeting_and_shop_button():
    settings = Settings(webapp_url="https://shop.example.com")
    router = customer_router(settings)
    message = AsyncMock()

    await _start_handler(router)(message)

    message.answer.assert_awaited_once()
    args, kwargs = message.answer.await_args
    assert "Assalomu" in args[0]
    markup = kwargs["reply_markup"]
    button = markup.inline_keyboard[0][0]
    assert button.web_app.url == "https://shop.example.com/app/"


async def test_start_without_webapp_url_sends_greeting_only_no_button():
    settings = Settings(webapp_url="")
    router = customer_router(settings)
    message = AsyncMock()

    await _start_handler(router)(message)

    message.answer.assert_awaited_once()
    args, kwargs = message.answer.await_args
    assert kwargs.get("reply_markup") is None
