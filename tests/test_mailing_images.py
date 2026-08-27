from io import BytesIO

from PIL import Image

from services import mailing_images


def image_bytes(size, image_format="PNG"):
    output = BytesIO()
    Image.new("RGB", size, "blue").save(output, format=image_format)
    return output.getvalue()


def open_normalized(content):
    image = Image.open(BytesIO(content))
    image.load()
    return image


def test_photo_dimensions_are_reduced_to_telegram_safe_sum(monkeypatch):
    monkeypatch.setattr(
        mailing_images,
        "TELEGRAM_SAFE_DIMENSION_SUM",
        100,
    )

    content = mailing_images.normalize_mailing_photo(
        image_bytes((80, 60))
    )
    image = open_normalized(content)

    assert image.format == "JPEG"
    assert sum(image.size) <= 100


def test_extreme_aspect_ratio_is_padded(monkeypatch):
    monkeypatch.setattr(
        mailing_images,
        "TELEGRAM_SAFE_ASPECT_RATIO",
        2,
    )

    content = mailing_images.normalize_mailing_photo(
        image_bytes((100, 10))
    )
    image = open_normalized(content)

    assert max(image.size) / min(image.size) <= 2
