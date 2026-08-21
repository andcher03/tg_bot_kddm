from pathlib import Path


WEB_ADMIN_DIR = Path(__file__).resolve().parent.parent / "web_admin"
MAILING_UPLOAD_DIR = WEB_ADMIN_DIR / "static" / "uploads" / "mailing"


def resolve_mailing_photo_path(
    photo_url: str | None,
) -> Path | None:
    if not photo_url:
        return None

    prefix = "/static/uploads/mailing/"

    if not photo_url.startswith(prefix):
        return None

    file_path = MAILING_UPLOAD_DIR / Path(photo_url).name

    if not file_path.is_file():
        return None

    return file_path
