from io import BytesIO
from pathlib import Path
import re
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError


MAX_AVATAR_BYTES = 5 * 1024 * 1024
MAX_AVATAR_PIXELS = 20_000_000
AVATAR_SIZE = (512, 512)


class UserAvatarError(ValueError):
    pass


def normalize_user_avatar(content: bytes) -> bytes:
    if not content:
        raise UserAvatarError("Выберите изображение для загрузки.")
    if len(content) > MAX_AVATAR_BYTES:
        raise UserAvatarError("Размер фотографии не должен превышать 5 МБ.")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as source:
                if source.format not in {"JPEG", "PNG", "WEBP"}:
                    raise UserAvatarError("Поддерживаются изображения JPG, PNG и WebP.")
                if source.width * source.height > MAX_AVATAR_PIXELS:
                    raise UserAvatarError("Разрешение фотографии слишком большое.")
                source.load()
                image = ImageOps.exif_transpose(source).convert("RGBA")
                background = Image.new("RGBA", image.size, "white")
                background.alpha_composite(image)
                image = background.convert("RGB")
                image.thumbnail(AVATAR_SIZE, Image.Resampling.LANCZOS)
    except UserAvatarError:
        raise
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        UnidentifiedImageError,
        OSError,
        ValueError,
    ) as error:
        raise UserAvatarError("Файл повреждён или не является изображением.") from error

    output = BytesIO()
    image.save(output, format="JPEG", quality=88, optimize=True)
    return output.getvalue()


def remove_user_avatar(avatar_path: str | None, upload_dir: Path) -> None:
    if not avatar_path:
        return
    filename = Path(avatar_path).name
    if not re.fullmatch(r"admin-[0-9a-f]{32}\.jpg", filename):
        return
    candidate = upload_dir / filename
    if candidate.parent.resolve() == upload_dir.resolve():
        candidate.unlink(missing_ok=True)
