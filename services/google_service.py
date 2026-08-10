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

    def __init__(self):

    # Основная таблица пользователей
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
    def get_all_users(self):
        return self.sheet.get_all_records()

    def append_user(self, data):
        self.sheet.append_row(data)

    def get_setting(self, key):

        records = self.settings.get_all_records()

        for row in records:
            if row["key"] == key:
                return row["value"]

        return None


    def set_setting(self, key, value):
        cell = self.settings.find(key)
        if cell:
            self.settings.update_cell(cell.row, 2, value)

    def update_user_field(self, telegram_id, field, value):
        users = self.sheet.get_all_records()
        headers = self.sheet.row_values(1)

        for index, user in enumerate(users, start=2):
            if str(user["telegram_id"]) == str(telegram_id):
                column = headers.index(field) + 1
                self.sheet.update_cell(
                    index,
                    column,
                    value
                )

                return True
    
        return False
    
    def get_events(self):
        return self.events.get_all_records()
    