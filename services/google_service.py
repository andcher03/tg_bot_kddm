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
        self.sheet = client.open_by_key(SPREADSHEET_ID).sheet1

    def get_all_users(self):
        return self.sheet.get_all_records()

    def append_user(self, data):
        self.sheet.append_row(data)