from handlers.registration import UNIVERSITIES_BY_CALLBACK
from keyboards.registration import university_keyboard
from services.universities import UNIVERSITY_NAMES
from web_admin.routers.mailing import UNIVERSITIES


EXPECTED_UNIVERSITIES = (
    "КФУ",
    "КНИТУ",
    "КНИТУ-КАИ",
    "КГМУ",
    "КГЭУ",
    "КГАСУ",
    "КГАУ",
    "ВГУЮ",
    "КФ РГУП",
    "ТИСБИ",
    "ПГУФКСиТ",
    "КазГИК",
)


def test_university_list_matches_requested_order_everywhere():
    assert UNIVERSITY_NAMES == EXPECTED_UNIVERSITIES
    assert tuple(UNIVERSITIES_BY_CALLBACK.values()) == EXPECTED_UNIVERSITIES
    assert tuple(UNIVERSITIES) == EXPECTED_UNIVERSITIES


def test_registration_keyboard_contains_all_universities():
    keyboard = university_keyboard()
    button_names = tuple(
        row[0].text.split(" ", maxsplit=1)[1]
        for row in keyboard.inline_keyboard
    )

    assert button_names == EXPECTED_UNIVERSITIES
