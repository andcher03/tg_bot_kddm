from io import BytesIO
import math
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError


MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 50_000_000
TELEGRAM_SAFE_DIMENSION_SUM = 9_000
TELEGRAM_SAFE_ASPECT_RATIO = 19.5


class MailingImageError(ValueError):
    pass


def _flatten_to_rgb(image: Image.Image) -> Image.Image:
    if image.mode == "RGB":
        return image

    if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
        rgba = image.convert("RGBA")
        background = Image.new("RGBA", rgba.size, "white")
        background.alpha_composite(rgba)
        return background.convert("RGB")

    return image.convert("RGB")


def _pad_extreme_aspect_ratio(image: Image.Image) -> Image.Image:
    width, height = image.size
    if min(width, height) <= 0:
        raise MailingImageError("Фотография имеет некорректные размеры.")

    ratio = max(width, height) / min(width, height)
    if ratio <= TELEGRAM_SAFE_ASPECT_RATIO:
        return image

    if width > height:
        target_size = (
            width,
            math.ceil(width / TELEGRAM_SAFE_ASPECT_RATIO),
        )
    else:
        target_size = (
            math.ceil(height / TELEGRAM_SAFE_ASPECT_RATIO),
            height,
        )

    image = _flatten_to_rgb(image)
    canvas = Image.new("RGB", target_size, "white")
    offset = (
        (target_size[0] - width) // 2,
        (target_size[1] - height) // 2,
    )
    canvas.paste(image, offset)
    return canvas


def _resize_for_telegram(image: Image.Image) -> Image.Image:
    width, height = image.size
    if width + height <= TELEGRAM_SAFE_DIMENSION_SUM:
        return image

    scale = TELEGRAM_SAFE_DIMENSION_SUM / (width + height)
    target_size = (
        max(1, int(width * scale)),
        max(1, int(height * scale)),
    )
    return image.resize(target_size, Image.Resampling.LANCZOS)


def _encode_jpeg(image: Image.Image) -> bytes:
    image = _flatten_to_rgb(image)

    for _ in range(5):
        for quality in (90, 85, 80, 75, 70):
            output = BytesIO()
            image.save(
                output,
                format="JPEG",
                quality=quality,
                optimize=True,
            )
            content = output.getvalue()
            if len(content) <= MAX_UPLOAD_BYTES:
                return content

        width, height = image.size
        image = image.resize(
            (
                max(1, int(width * 0.85)),
                max(1, int(height * 0.85)),
            ),
            Image.Resampling.LANCZOS,
        )

    raise MailingImageError(
        "Не удалось подготовить фотографию размером до 10 МБ."
    )


def normalize_mailing_photo(content: bytes) -> bytes:
    if not content:
        raise MailingImageError("Загружена пустая фотография.")

    if len(content) > MAX_UPLOAD_BYTES:
        raise MailingImageError(
            "Размер каждой фотографии не должен превышать 10 МБ."
        )

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as source:
                if source.format not in {"JPEG", "PNG", "WEBP"}:
                    raise MailingImageError(
                        "Можно загрузить только JPG, PNG или WEBP."
                    )

                width, height = source.size
                if width * height > MAX_IMAGE_PIXELS:
                    raise MailingImageError(
                        "Разрешение фотографии слишком большое."
                    )

                source.load()
                image = ImageOps.exif_transpose(source).copy()
    except MailingImageError:
        raise
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        UnidentifiedImageError,
        OSError,
        ValueError,
    ) as error:
        raise MailingImageError(
            "Файл повреждён или не является поддерживаемым изображением."
        ) from error

    image = _pad_extreme_aspect_ratio(image)
    image = _resize_for_telegram(image)
    return _encode_jpeg(image)
