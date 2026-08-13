import time

import gspread
from google.oauth2.service_account import Credentials

from config import SPREADSHEET_ID, EVENTS_SPREADSHEET_ID


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


credentials = Credentials.from_service_account_file(
    "google/credentials.json",
    scopes=SCOPES
)

client = gspread.authorize(credentials)


class GoogleService:

    # Кэш пользователей
    USERS_CACHE_TTL = 30
    REGISTRATIONS_CACHE_TTL = 30
    EVENTS_CACHE_TTL = 30
    
    def __init__(self):

        # Таблица пользователей
        users_spreadsheet = client.open_by_key(
            SPREADSHEET_ID
        )

        self.sheet = users_spreadsheet.worksheet("Users")
        self.settings = users_spreadsheet.worksheet("Settings")
        self.logs = users_spreadsheet.worksheet("Logs")

        # Таблица мероприятий
        events_spreadsheet = client.open_by_key(
            EVENTS_SPREADSHEET_ID
        )

        self.events = events_spreadsheet.worksheet("Events")
        self.registrations = events_spreadsheet.worksheet("Registrations")

        # Кэш
        self._users_cache = None
        self._users_cache_time = 0
        self._registrations_cache = None
        self._registrations_cache_time = 0
        
        self._events_cache = None
        self._events_cache_time = 0

    # =========================
    # USERS
    # =========================

    def get_all_users(self, force_refresh=False):

        now = time.time()

        # Используем кэш
        if (
            not force_refresh
            and self._users_cache is not None
            and now - self._users_cache_time < self.USERS_CACHE_TTL
        ):
            return self._users_cache

        # Читаем Google Sheets
        users = self.sheet.get_all_records()

        # Сохраняем в кэш
        self._users_cache = users
        self._users_cache_time = now

        return users

    def append_user(self, data):

        self.sheet.append_row(data)

        # Обновляем локальный кэш,
        # чтобы следующий get_all_users()
        # не делал новый запрос к Google
        if self._users_cache is not None:
            headers = self.sheet.row_values(1)

            user = dict(zip(headers, data))

            self._users_cache.append(user)
            self._users_cache_time = time.time()

    def update_user_field(
        self,
        telegram_id,
        field,
        value
    ):

        users = self.get_all_users()

        headers = self.sheet.row_values(1)

        for index, user in enumerate(users, start=2):

            if str(user["telegram_id"]) == str(telegram_id):

                column = headers.index(field) + 1

                self.sheet.update_cell(
                    index,
                    column,
                    value
                )

                # Обновляем кэш
                user[field] = value

                return True

        return False

    # =========================
    # SETTINGS
    # =========================

    def get_setting(self, key):

        records = self.settings.get_all_records()

        for row in records:

            if row["key"] == key:
                return row["value"]

        return None

    def set_setting(self, key, value):

        cell = self.settings.find(key)

        if cell:
            self.settings.update_cell(
                cell.row,
                2,
                value
            )

    # =========================
    # EVENTS
    # =========================

    def get_events(self, force_refresh=False):
        now = time.time()

        if (
            not force_refresh
            and self._events_cache is not None
            and now - self._events_cache_time < self.EVENTS_CACHE_TTL
        ):
            return self._events_cache

        events = self.events.get_all_records()

        self._events_cache = events
        self._events_cache_time = now

        return events

    def get_registrations(self, force_refresh=False):

        now = time.time()

        if (
            not force_refresh
            and self._registrations_cache is not None
            and now - self._registrations_cache_time < self.REGISTRATIONS_CACHE_TTL
        ):
            return self._registrations_cache

        registrations = self.registrations.get_all_records()

        self._registrations_cache = registrations
        self._registrations_cache_time = now

        return registrations
    
    def add_registration(self, registration):

        headers = self.registrations.row_values(1)

        row = [
            registration.get(header, "")
            for header in headers
        ]

        self.registrations.append_row(row)

        # Обновляем кэш
        if self._registrations_cache is not None:
            self._registrations_cache.append(registration)
            self._registrations_cache_time = time.time()
        
google_service = GoogleService()