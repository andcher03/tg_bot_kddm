from io import BytesIO

import pytest
from PIL import Image
from starlette.datastructures import FormData

from web_admin.routers import mailing
from web_admin.routers.mailing import (
    get_recipients,
    mailing_users_search_query,
    normalized_photo_urls,
    parse_mailing_form,
    save_uploaded_photos,
)


class EmptyScalars:
    def all(self):
        return []


class EmptyResult:
    def scalars(self):
        return EmptyScalars()


class CapturingSession:
    def __init__(self):
        self.statement = None

    async def execute(self, statement):
        self.statement = statement
        return EmptyResult()


class FakeUpload:
    def __init__(self, filename, content_type="image/jpeg", content=None):
        self.filename = filename
        self.content_type = content_type
        self.content = content if content is not None else jpeg_bytes()

    async def read(self):
        return self.content


class PhotoForm:
    def __init__(self, photos):
        self.photos = photos

    def getlist(self, name):
        return self.photos if name == "photos" else []


def jpeg_bytes(size=(32, 24)):
    output = BytesIO()
    Image.new("RGB", size, "green").save(output, format="JPEG")
    return output.getvalue()


def test_parse_mailing_form_keeps_unique_valid_user_ids():
    form = FormData([
        ("message", "  Проверка  "),
        ("user_ids", "7"),
        ("user_ids", "7"),
        ("user_ids", "12"),
        ("user_ids", "invalid"),
        ("user_ids", "-1"),
    ])

    (
        message,
        all_users,
        universities,
        event_ids,
        user_ids,
    ) = parse_mailing_form(form)

    assert message == "Проверка"
    assert all_users is False
    assert universities == []
    assert event_ids == []
    assert user_ids == [7, 12]


def test_user_search_checks_all_supported_fields():
    query = mailing_users_search_query("КФУ")
    sql = str(query.compile()).lower()

    assert "users.full_name" in sql
    assert "users.user_code" in sql
    assert "users.username" in sql
    assert "users.university" in sql
    assert "users.telegram_id" in sql
    assert 50 in query.compile().params.values()


@pytest.mark.asyncio
async def test_specific_users_are_added_to_recipient_query():
    session = CapturingSession()

    await get_recipients(
        session=session,
        all_users=False,
        selected_universities=[],
        selected_event_ids=[],
        selected_user_ids=[7, 12],
    )

    sql = str(
        session.statement.compile(
            compile_kwargs={"literal_binds": True}
        )
    )

    assert "users.id IN (7, 12)" in sql


def test_photo_urls_are_deduplicated_in_original_order():
    assert normalized_photo_urls([" one.jpg ", "two.jpg", "one.jpg"]) == [
        "one.jpg",
        "two.jpg",
    ]


@pytest.mark.asyncio
async def test_nine_photos_can_be_uploaded(tmp_path, monkeypatch):
    monkeypatch.setattr(mailing, "UPLOAD_DIR", tmp_path)
    photos = [FakeUpload(f"photo-{index}.jpg") for index in range(9)]

    photo_urls, error = await save_uploaded_photos(PhotoForm(photos))

    assert error is None
    assert len(photo_urls) == 9
    assert len(list(tmp_path.iterdir())) == 9
    assert all(path.suffix == ".jpg" for path in tmp_path.iterdir())


@pytest.mark.asyncio
async def test_tenth_photo_is_rejected_without_writing_files(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(mailing, "UPLOAD_DIR", tmp_path)
    photos = [FakeUpload(f"photo-{index}.jpg") for index in range(10)]

    photo_urls, error = await save_uploaded_photos(PhotoForm(photos))

    assert photo_urls == []
    assert error == "К рассылке можно прикрепить не более 9 фотографий."
    assert list(tmp_path.iterdir()) == []


@pytest.mark.asyncio
async def test_invalid_image_is_rejected_without_writing_files(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(mailing, "UPLOAD_DIR", tmp_path)
    photos = [FakeUpload("broken.jpg", content=b"not-an-image")]

    photo_urls, error = await save_uploaded_photos(PhotoForm(photos))

    assert photo_urls == []
    assert error == (
        "Файл повреждён или не является поддерживаемым изображением."
    )
    assert list(tmp_path.iterdir()) == []
