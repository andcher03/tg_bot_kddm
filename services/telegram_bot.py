import os
from urllib.parse import urlsplit

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession

from config import BOT_TOKEN


SUPPORTED_PROXY_SCHEMES = {
    "http",
    "socks4",
    "socks5",
}


def get_telegram_proxy_url() -> str | None:
    """Return and validate the optional Telegram-only proxy URL."""

    proxy_url = (os.getenv("TELEGRAM_PROXY_URL") or "").strip()
    if not proxy_url:
        return None

    parsed = urlsplit(proxy_url)
    if parsed.scheme.lower() not in SUPPORTED_PROXY_SCHEMES:
        raise RuntimeError(
            "TELEGRAM_PROXY_URL должен начинаться с http://, socks4:// "
            "или socks5://."
        )

    if not parsed.hostname:
        raise RuntimeError(
            "В TELEGRAM_PROXY_URL не указан адрес прокси-сервера."
        )

    try:
        port = parsed.port
    except ValueError as error:
        raise RuntimeError(
            "В TELEGRAM_PROXY_URL указан некорректный порт."
        ) from error

    if port is None:
        raise RuntimeError(
            "В TELEGRAM_PROXY_URL необходимо указать порт прокси-сервера."
        )

    return proxy_url


def create_telegram_bot(*, token: str | None = None) -> Bot:
    """Create a Bot whose Telegram API traffic uses the configured proxy."""

    proxy_url = get_telegram_proxy_url()
    session = (
        AiohttpSession(proxy=proxy_url)
        if proxy_url is not None
        else AiohttpSession()
    )
    return Bot(token=token or BOT_TOKEN, session=session)
