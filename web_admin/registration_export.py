from datetime import datetime
from io import BytesIO
from typing import Any

from openpyxl import Workbook

from web_admin.review_export import excel_safe_text


REGISTRATION_EXPORT_HEADERS = (
    "KZN ID",
    "Имя",
    "Логин Telegram",
    "ВУЗ",
    "Дата регистрации",
    "Статус регистрации",
    "Подтверждение участия",
)

_CONFIRMATION_LABELS = {
    "not_requested": "Ожидает запроса",
    "sending": "Отправляется",
    "pending": "Ожидает ответа",
    "confirmed": "Подтвердил участие",
    "delivery_failed": "Запрос не доставлен",
    "declined": "Отказался",
    "expired": "Не подтвердил вовремя",
}


def registrations_export_filename(event: Any) -> str:
    event_code = excel_safe_text(event.event_code or event.id)
    safe_code = "".join(
        character
        for character in event_code
        if character.isascii() and (character.isalnum() or character in "_-")
    )
    return f"registrations_{safe_code or event.id}.xlsx"


def build_registrations_workbook(
    registrations: list[dict[str, Any]],
    *,
    confirmations_enabled: bool,
) -> BytesIO:
    """Build a plain worksheet with one row per active event registration."""
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Регистрации"
    worksheet.append(REGISTRATION_EXPORT_HEADERS)

    for registration in registrations:
        registration_status = registration.get("status")
        confirmation_status = registration.get("confirmation_status")

        if not confirmations_enabled:
            confirmation_label = "Не требуется"
        else:
            confirmation_label = _CONFIRMATION_LABELS.get(
                confirmation_status,
                excel_safe_text(confirmation_status),
            )
            if registration_status == "confirmed":
                confirmation_label = "Подтвердил участие"

        registration_date = registration.get("registration_date")
        if isinstance(registration_date, datetime):
            registration_date = registration_date.strftime("%d.%m.%Y %H:%M")

        username = registration.get("username")
        if username:
            username = f"@{str(username).lstrip('@')}"

        worksheet.append(
            (
                excel_safe_text(registration.get("user_code")),
                excel_safe_text(registration.get("full_name")),
                excel_safe_text(username),
                excel_safe_text(registration.get("university")),
                excel_safe_text(registration_date),
                "Зарегистрирован",
                confirmation_label,
            )
        )

    for column_cells in worksheet.columns:
        column_letter = column_cells[0].column_letter
        content_width = max(
            len(str(cell.value or ""))
            for cell in column_cells
        )
        worksheet.column_dimensions[column_letter].width = content_width + 2

    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return output
