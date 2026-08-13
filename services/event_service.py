from datetime import datetime, date

from services.google_service import google_service


class EventService:

    def __init__(self):
        self.google = google_service

    def get_active_events(self):

        events = self.google.get_events()

        today = date.today()

        active_events = []

        for event in events:

            # Только опубликованные мероприятия
            status = str(
                event.get("status", "")
            ).strip().lower()

            if status != "active":
                continue

            # Получаем дату мероприятия
            raw_date = event.get("date")

            if not raw_date:
                continue

            event_date = None

            if isinstance(raw_date, datetime):
                event_date = raw_date.date()

            elif isinstance(raw_date, date):
                event_date = raw_date

            else:

                raw_date = str(raw_date).strip()

                date_formats = [
                    "%d.%m.%Y",
                    "%Y-%m-%d",
                    "%d/%m/%Y",
                    "%Y.%m.%d",
                ]

                for date_format in date_formats:

                    try:
                        event_date = datetime.strptime(
                            raw_date,
                            date_format
                        ).date()

                        break

                    except ValueError:
                        continue

            if event_date is None:
                print(
                    f"⚠️ Не удалось определить дату: "
                    f"{event.get('title')} | {raw_date}"
                )
                continue

            # Не показываем прошедшие мероприятия
            if event_date < today:
                continue

            active_events.append(event)

        return active_events
    
    def get_event_by_id(self, event_id):

        events = self.google.get_events()

        for event in events:
            if str(event["id"]) == str(event_id):
                return event

        return None