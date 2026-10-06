from io import BytesIO

import pytest
from PIL import Image

from services.user_avatar import UserAvatarError, normalize_user_avatar


def make_image(format_name: str) -> bytes:
    output = BytesIO()
    mode = "RGB" if format_name == "JPEG" else "RGBA"
    color = (20, 80, 160) if mode == "RGB" else (20, 80, 160, 128)
    Image.new(mode, (900, 600), color).save(output, format=format_name)
    return output.getvalue()


@pytest.mark.parametrize("source_format", ["JPEG", "PNG", "WEBP"])
def test_avatar_is_reencoded_as_small_jpeg(source_format):
    content = normalize_user_avatar(make_image(source_format))
    with Image.open(BytesIO(content)) as image:
        assert image.format == "JPEG"
        assert image.size == (512, 341)
        assert not image.getexif()


def test_avatar_rejects_unsupported_format():
    with pytest.raises(UserAvatarError):
        normalize_user_avatar(b"not an image")


def test_avatar_rejects_empty_content():
    with pytest.raises(UserAvatarError, match="Выберите изображение"):
        normalize_user_avatar(b"")


def test_avatar_rejects_oversized_file():
    with pytest.raises(UserAvatarError, match="5 МБ"):
        normalize_user_avatar(b"x" * (5 * 1024 * 1024 + 1))
