from services.google_service import GoogleService
from datetime import datetime

google = GoogleService()


class UserService:

    def is_registered(self, telegram_id: int):
        users = google.get_all_users()

        for user in users:
            if str(user["telegram_id"]) == str(telegram_id):
                return True

        return False

    def generate_user_code(self):
        users = google.get_all_users()

        number = len(users) + 1

        return f"KZN-{number:06d}"

    def register_user(
        self,
        telegram_id,
        username,
        full_name,
        birth_date,
        education
    ):

        user_code = self.generate_user_code()

        google.append_user([
            user_code,
            telegram_id,
            username,
            full_name,
            birth_date,
            education,
            "user",
            datetime.now().strftime("%d.%m.%Y %H:%M")
        ])