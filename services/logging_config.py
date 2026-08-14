import logging
from datetime import datetime
from pathlib import Path


LOG_DIR = Path("logs")
MAX_LINES = 1000

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True
)


class LineCountHandler(logging.FileHandler):

    def __init__(self):
        self.line_count = 0

        timestamp = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        filename = LOG_DIR / f"log_{timestamp}.txt"

        super().__init__(
            filename,
            mode="a",
            encoding="utf-8"
        )

    def emit(self, record):

        if self.line_count >= MAX_LINES:

            if self.stream:
                self.stream.close()

            timestamp = datetime.now().strftime(
                "%Y-%m-%d_%H-%M-%S"
            )

            filename = (
                LOG_DIR
                / f"log_{timestamp}.txt"
            )

            self.baseFilename = str(
                filename.absolute()
            )

            self.stream = self._open()

            self.line_count = 0

        super().emit(record)

        self.line_count += 1


def setup_logging():

    root_logger = logging.getLogger()

    root_logger.setLevel(
        logging.INFO
    )

    root_logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s",
        datefmt="%d.%m.%Y %H:%M:%S"
    )

    # Логи в файл
    file_handler = LineCountHandler()

    file_handler.setFormatter(
        formatter
    )

    root_logger.addHandler(
        file_handler
    )

    # Те же логи в терминал
    console_handler = logging.StreamHandler()

    console_handler.setFormatter(
        formatter
    )

    root_logger.addHandler(
        console_handler
    )