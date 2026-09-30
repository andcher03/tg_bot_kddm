from collections import Counter

import pytest

from keyboards.quiz import quiz_question_keyboard
from keyboards.user_menu import user_menu
from services.quiz_data import (
    BACKROOMS,
    LAKE,
    QUESTIONS,
    RESULTS,
    ROUTE,
    SONG,
    STATION,
    TUBETEIKA,
    calculate_result,
    format_result,
    result_image_path,
)


def test_quiz_has_seven_questions_and_six_results():
    assert len(QUESTIONS) == 7
    assert len(RESULTS) == 6


def test_each_result_appears_once_in_every_question():
    for question in QUESTIONS:
        counts = Counter(
            result_id
            for option in question.options
            for result_id in option.results
        )
        assert counts == Counter({result_id: 1 for result_id in RESULTS})


@pytest.mark.parametrize(
    ("answers", "expected"),
    [
        ([0, 2, 0, 1, 4, 5, 0], ROUTE),
        ([0, 4, 2, 0, 5, 1, 5], BACKROOMS),
        ([1, 5, 4, 5, 3, 3, 1], STATION),
        ([2, 1, 5, 4, 1, 4, 4], SONG),
        ([3, 3, 1, 3, 2, 0, 3], LAKE),
        ([1, 0, 3, 2, 0, 2, 2], TUBETEIKA),
    ],
)
def test_calculate_result_for_clear_winner(answers, expected):
    assert calculate_result(answers) == expected


def test_calculate_result_rejects_incomplete_answers():
    with pytest.raises(ValueError):
        calculate_result([0])


def test_tie_is_resolved_by_values_question():
    # По баллам лидируют сразу три результата. Ответ о ценностях
    # однозначно выбирает «Маршрут» согласно приоритету вопросов.
    answers = [0, 0, 0, 0, 0, 0, 1]
    assert calculate_result(answers) == ROUTE


def test_negative_option_index_is_rejected():
    with pytest.raises(ValueError):
        calculate_result([-1, 0, 0, 0, 0, 0, 0])


def test_result_text_contains_only_short_personality_description():
    text = format_result(ROUTE)
    assert "Ваш результат" in text
    assert "ответственный" in text
    assert "Об аномалии" not in text
    assert "Опасность" not in text
    assert "Как выбраться" not in text
    assert len(text) < 4096


@pytest.mark.parametrize(
    ("result_id", "filename"),
    [
        (ROUTE, "route.png"),
        (BACKROOMS, "avenue.png"),
        (STATION, "railway.png"),
        (SONG, "musicians.png"),
        (LAKE, "lake.png"),
        (TUBETEIKA, "tubeteika.png"),
    ],
)
def test_result_has_matching_image(result_id, filename):
    image_path = result_image_path(result_id)
    assert image_path.name == filename
    assert image_path.is_file()


def test_every_result_fits_telegram_photo_caption_limit():
    for result_id in RESULTS:
        assert len(format_result(result_id)) <= 1024


def test_all_callback_data_fits_telegram_limit():
    for question_index in range(len(QUESTIONS)):
        keyboard = quiz_question_keyboard(question_index)
        for row in keyboard.inline_keyboard:
            assert len(row[0].callback_data.encode()) <= 64


def test_every_question_allows_return_to_main_menu():
    for question_index in range(len(QUESTIONS)):
        keyboard = quiz_question_keyboard(question_index)
        assert keyboard.inline_keyboard[-1][0].callback_data == (
            "quiz:main_menu"
        )


def test_quiz_is_first_green_main_menu_button():
    first_button = user_menu().keyboard[0][0]
    assert first_button.text == "🧩 Какая ты аномалия в Казани?"
    assert first_button.style == "success"
