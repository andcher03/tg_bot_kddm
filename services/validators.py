import re
from datetime import datetime


def validate_full_name(full_name: str) -> tuple[bool, str]:
    """
    Проверка ФИО.
    """

    full_name = full_name.strip()

    if len(full_name.split()) < 2:
        return False, "❌ Введите минимум имя и фамилию."

    pattern = r"^[А-Яа-яЁёA-Za-z\s-]+$"

    if not re.fullmatch(pattern, full_name):
        return (
            False,
            "❌ ФИО может содержать только буквы, пробелы и дефисы."
        )

    return True, ""


def validate_birth_date(text: str) -> tuple[bool, str]:
    """
    Проверка даты рождения.
    """

    try:
        birthday = datetime.strptime(text, "%d.%m.%Y")

    except ValueError:
        return (
            False,
            "❌ Введите дату в формате ДД.ММ.ГГГГ\n\nНапример: 25.12.2004"
        )

    if birthday > datetime.now():
        return (
            False,
            "❌ Дата рождения не может быть в будущем."
        )

    age = (datetime.now() - birthday).days // 365

    if age < 14:
        return (
            False,
            "❌ Возраст должен быть не менее 14 лет."
        )

    return True, ""


def validate_education(text: str) -> tuple[bool, str]:
    """
    Проверка учебного заведения.
    """

    if len(text.strip()) < 3:
        return (
            False,
            "❌ Укажите корректное название учебного заведения."
        )

    return True, ""