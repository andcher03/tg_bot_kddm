import gspread
from google.oauth2.service_account import Credentials
from config import SPREADSHEET_ID

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

        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        self.sheet = spreadsheet.worksheet("Users")
        self.settings = spreadsheet.worksheet("Settings")
        self.logs = spreadsheet.worksheet("Logs")

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