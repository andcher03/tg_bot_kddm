import logging
from datetime import datetime
from pathlib import Path


LOG_DIR = Path("logs")
MAX_LINES = 1000


class LineCountHandler(logging.FileHandler):

    def __init__(self, log_dir: Path, max_lines: int = 1000):
        self.log_dir = log_dir
        self.max_lines = max_lines
        self.line_count = 0

        self.log_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        filename = self._generate_filename()

        super().__init__(
            filename,
            mode="a",
            encoding="utf-8"
        )

    def _generate_filename(self):

        timestamp = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        return self.log_dir / f"log_{timestamp}.txt"

    def emit(self, record):

        # Если достигли 1000 строк —
        # закрываем старый файл
        # и создаём новый.
        if self.line_count >= self.max_lines:

            self.close()

            filename = self._generate_filename()

            self.baseFilename = str(
                filename.absolute()
            )

            self.stream = self._open()

            self.line_count = 0

        super().emit(record)

        self.line_count += 1


logger = logging.getLogger("kddm_bot")

logger.setLevel(logging.INFO)

logger.propagate = False


# Чтобы при повторном импорте
# обработчики не дублировались.
if not logger.handlers:

    handler = LineCountHandler(
        LOG_DIR,
        MAX_LINES
    )

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%d.%m.%Y %H:%M:%S"
    )

    handler.setFormatter(formatter)

    logger.addHandler(handler)


class LoggerService:

    def write(
        self,
        user="",
        role="",
        section="",
        action="",
        result="✅"
    ):

        logger.info(
            "%s | %s | %s | %s | %s",
            user,
            role,
            section,
            action,
            result
        )