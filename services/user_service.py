from datetime import datetime

from services.google_service import google_service


class UserService:

    def __init__(self):
        self.google = google_service

    def is_registered(self, telegram_id: int):

        users = self.google.get_all_users()

        for user in users:

            if str(user["telegram_id"]) == str(telegram_id):
                return True

        return False

    def generate_user_code(self):

        users = self.google.get_all_users()

        number = len(users) + 1

        return f"KZN-{number:06d}"

    def register_user(
        self,
        telegram_id,
        username,
        full_name,
        university
    ):

        # Проверяем, нет ли уже пользователя
        if self.is_registered(telegram_id):
            return False

        user_code = self.generate_user_code()

        self.google.append_user([
            user_code,
            telegram_id,
            username,
            full_name,
            university,
            "user",
            datetime.now().strftime("%d.%m.%Y %H:%M")
        ])

        return True

    def get_user(self, telegram_id: int):

        users = self.google.get_all_users()

        for user in users:

            if str(user["telegram_id"]) == str(telegram_id):
                return user

        return None

    def is_admin(self, telegram_id: int):

        user = self.get_user(telegram_id)

        if not user:
            return False

        return user.get("role") in (
            "admin",
            "moderator",
            "superadmin"
        )

    def update_user_field(
        self,
        telegram_id,
        field,
        value
    ):

        return self.google.update_user_field(
            telegram_id,
            field,
            value
        )