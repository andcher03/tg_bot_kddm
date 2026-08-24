import pytest

from services.telegram_bot import (
    create_telegram_bot,
    get_telegram_proxy_url,
)


def test_proxy_is_optional(monkeypatch):
    monkeypatch.delenv("TELEGRAM_PROXY_URL", raising=False)

    assert get_telegram_proxy_url() is None


@pytest.mark.parametrize(
    "proxy_url",
    [
        "http://proxy.example:8080",
        "socks4://proxy.example:1080",
        "socks5://user:password@proxy.example:1080",
    ],
)
def test_supported_proxy_urls(monkeypatch, proxy_url):
    monkeypatch.setenv("TELEGRAM_PROXY_URL", proxy_url)

    assert get_telegram_proxy_url() == proxy_url


@pytest.mark.parametrize(
    "proxy_url",
    [
        "proxy.example:1080",
        "ftp://proxy.example:21",
        "https://proxy.example:8443",
        "socks5://:1080",
        "socks5://proxy.example:not-a-port",
        "socks5://proxy.example",
    ],
)
def test_invalid_proxy_url_is_rejected(monkeypatch, proxy_url):
    monkeypatch.setenv("TELEGRAM_PROXY_URL", proxy_url)

    with pytest.raises(RuntimeError):
        get_telegram_proxy_url()


def test_bot_uses_configured_proxy(monkeypatch):
    proxy_url = "socks5://user:password@proxy.example:1080"
    monkeypatch.setenv("TELEGRAM_PROXY_URL", proxy_url)

    bot = create_telegram_bot(token="123456:abcdefghijklmnopqrstuvwxyzABCDE")

    assert bot.session._proxy == proxy_url
