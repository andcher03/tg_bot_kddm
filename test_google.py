from services.google_service import google_service

google = google_service

google.append_user([
    "KZN-000001",
    123456789,
    "test_user",
    "Иван Иванов",
    "01.01.2000",
    "КГУ",
    "user",
    "2025-07-28"
])

print(google.get_all_users())
