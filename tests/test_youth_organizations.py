from handlers.youth_organizations import YOUTH_ORGANIZATIONS
from keyboards.youth_organizations import (
    YOUTH_ORGANIZATION_BUTTONS,
    youth_organization_page_keyboard,
    youth_organizations_menu,
)


def test_youth_organizations_menu_contains_document_sections():
    keyboard = youth_organizations_menu()
    page_keys = {
        page_key
        for _, page_key in YOUTH_ORGANIZATION_BUTTONS
    }

    assert len(YOUTH_ORGANIZATION_BUTTONS) == 9
    assert page_keys == set(YOUTH_ORGANIZATIONS)
    assert len(keyboard.inline_keyboard) == 10
    assert keyboard.inline_keyboard[-1][0].callback_data == (
        "youth_org:main_menu"
    )


def test_youth_organization_pages_have_real_links_and_back_button():
    total_links = 0

    for page in YOUTH_ORGANIZATIONS.values():
        links = page["links"]
        total_links += len(links)
        keyboard = youth_organization_page_keyboard(links)
        rendered_text = f"<b>{page['title']}</b>\n\n{page['text']}"

        assert page["title"]
        assert page["text"]
        assert len(rendered_text) <= 1024
        assert all(url.startswith("https://") for _, url in links)
        assert all("example.com" not in url for _, url in links)
        assert keyboard.inline_keyboard[-1][0].callback_data == (
            "youth_org:back"
        )

    assert total_links == 14


def test_enterprise_council_has_telegram_link_from_document():
    assert YOUTH_ORGANIZATIONS["enterprise_council"]["links"] == (
        ("Telegram", "https://t.me/smpo_kazan"),
    )


def test_youth_organization_callback_data_fits_telegram_limit():
    keyboard = youth_organizations_menu()

    for row in keyboard.inline_keyboard:
        callback_data = row[0].callback_data
        assert callback_data is not None
        assert len(callback_data.encode()) <= 64
