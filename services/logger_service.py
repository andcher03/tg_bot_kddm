from datetime import datetime

from services.google_service import google_service


google = google_service


class LoggerService:

    def write(
        self,
        user="",
        role="",
        section="",
        action="",
        result="✅"
    ):

        google.logs.append_row([
            datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            user,
            role,
            section,
            action,
            result
        ])