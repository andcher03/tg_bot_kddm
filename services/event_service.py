from services.google_service import GoogleService


class EventService:

    def __init__(self):
        self.google = GoogleService()


    def get_active_events(self):

        events = self.google.get_events()

        return [
            event
            for event in events
            if event["status"] == "active"
        ]