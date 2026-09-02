from handlers.youth_map import (
    YOUTH_LOCATION_PAGES,
    YOUTH_LOCATIONS_TEXT,
)
from keyboards.youth_map import (
    YOUTH_LOCATION_BUTTONS,
    youth_location_details_keyboard,
    youth_locations_keyboard,
    youth_map_keyboard,
)


def test_youth_map_contains_locations_button():
    keyboard = youth_map_keyboard()

    assert keyboard.inline_keyboard[1][0].text == "📍 Наши локации"
    assert keyboard.inline_keyboard[1][0].callback_data == (
        "youth_map:locations"
    )


def test_locations_menu_contains_five_organizations_and_back():
    keyboard = youth_locations_keyboard()

    assert len(YOUTH_LOCATION_BUTTONS) == 5
    assert [
        row[0].callback_data
        for row in keyboard.inline_keyboard
    ] == [
        "youth_map:location:gaidar",
        "youth_map:location:podrostok",
        "youth_map:location:doverie",
        "youth_map:location:yal",
        "youth_map:location:duslyk",
        "youth_map:overview",
    ]
    assert "пространства для развития" in YOUTH_LOCATIONS_TEXT


def test_location_pages_have_links_and_back_navigation():
    assert set(YOUTH_LOCATION_PAGES) == {
        "gaidar",
        "podrostok",
        "doverie",
        "yal",
        "duslyk",
    }

    for page in YOUTH_LOCATION_PAGES.values():
        keyboard = youth_location_details_keyboard(page["links"])
        link_buttons = keyboard.inline_keyboard[:-1]

        assert len(link_buttons) == 3
        assert all(row[0].url.startswith("https://") for row in link_buttons)
        assert (
            keyboard.inline_keyboard[-1][0].callback_data
            == "youth_map:locations"
        )
        assert len(f"<b>{page['title']}</b>\n\n{page['text']}") <= 4096


def test_location_links_match_supplied_sources():
    gaidar_links = dict(YOUTH_LOCATION_PAGES["gaidar"]["links"])
    podrostok_links = dict(YOUTH_LOCATION_PAGES["podrostok"]["links"])
    duslyk_links = dict(YOUTH_LOCATION_PAGES["duslyk"]["links"])

    assert "https://vk.ru/kmcgru" in gaidar_links.values()
    assert "https://t.me/kmcgru" in gaidar_links.values()
    assert "https://max.ru/id1657030349_gos" in gaidar_links.values()
    assert "https://vk.com/podrostokkzn" in podrostok_links.values()
    assert "https://t.me/podrostok116" in podrostok_links.values()
    assert "https://max.ru/podrostokkzn" in podrostok_links.values()
    assert "https://vk.com/duslik_kzn" in duslyk_links.values()
    assert "https://t.me/mbympd" in duslyk_links.values()
    assert "https://max.ru/id1658030253_gos" in duslyk_links.values()
