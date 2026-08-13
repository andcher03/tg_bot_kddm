from datetime import datetime

from services.google_service import GoogleService


class RegistrationService:

    def __init__(self):
        self.google = GoogleService()

    def get_registrations(self):
        return self.google.get_registrations()

    def is_registered(self, user_id, event_id):

        registrations = self.get_registrations()

        for registration in registrations:
            if (
                str(registration["user_id"]) == str(user_id)
                and str(registration["event_id"]) == str(event_id)
                and registration["status"] != "cancelled"
            ):
                return True

        return False

    def create_registration(self, user_id, event_id):

        if self.is_registered(user_id, event_id):
            return False

        registrations = self.get_registrations()

        registration_id = f"REG-{len(registrations) + 1:06d}"

        registration = {
            "id": registration_id,
            "user_id": str(user_id),
            "event_id": str(event_id),
            "registration_date": datetime.now().strftime(
                "%d.%m.%Y %H:%M:%S"
            ),
            "status": "registered",
        }

        self.google.add_registration(registration)

        return True

    def get_user_registrations(self, user_id):

        registrations = self.get_registrations()

        return [
            registration
            for registration in registrations
            if str(registration["user_id"]) == str(user_id)
            and registration["status"] != "cancelled"
        ]