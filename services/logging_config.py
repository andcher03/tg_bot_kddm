from __future__ import annotations

import logging
import os
import re
from datetime import datetime
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_LOG_DIR = PROJECT_DIR / "logs"
DEFAULT_MAX_LINES = 1000
DEFAULT_LOG_LEVEL = "INFO"
MANAGED_HANDLER_ATTRIBUTE = "_kddm_logging_handler"


def _safe_process_name(process_name: str) -> str:
    safe_name = re.sub(
        r"[^A-Za-z0-9_.-]+",
        "_",
        process_name.strip(),
    ).strip("._-")

    if not safe_name:
        raise ValueError("Имя процесса для логирования не может быть пустым.")

    return safe_name


def _resolve_log_dir(log_dir: str | Path | None) -> Path:
    configured_dir = Path(
        log_dir
        if log_dir is not None
        else os.getenv("LOG_DIR", "logs")
    ).expanduser()

    if not configured_dir.is_absolute():
        configured_dir = PROJECT_DIR / configured_dir

    return configured_dir.resolve()


def _resolve_max_lines(max_lines: int | None) -> int:
    if max_lines is None:
        raw_value = os.getenv(
            "LOG_MAX_LINES",
            str(DEFAULT_MAX_LINES),
        )

        try:
            max_lines = int(raw_value)
        except ValueError as error:
            raise RuntimeError(
                "LOG_MAX_LINES должен быть целым числом."
            ) from error

    if max_lines < 1:
        raise RuntimeError("LOG_MAX_LINES должен быть больше нуля.")

    return max_lines


def _resolve_log_level(level: str | int | None) -> int:
    if isinstance(level, int):
        return level

    level_name = (
        level
        if level is not None
        else os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL)
    ).upper()
    resolved_level = getattr(logging, level_name, None)

    if not isinstance(resolved_level, int):
        raise RuntimeError(
            f"Неизвестный уровень логирования: {level_name}."
        )

    return resolved_level


class LineCountHandler(logging.FileHandler):
    """Записывает ограниченное число событий в один файл журнала."""

    def __init__(
        self,
        log_dir: Path,
        process_name: str,
        max_lines: int = DEFAULT_MAX_LINES,
    ) -> None:
        self.log_dir = log_dir
        self.process_name = _safe_process_name(process_name)
        self.max_lines = _resolve_max_lines(max_lines)
        self.line_count = 0
        self.part_number = 0
        self.started_at = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S_%f"
        )

        self.log_dir.mkdir(parents=True, exist_ok=True)

        super().__init__(
            self._next_filename(),
            mode="a",
            encoding="utf-8",
        )

    @property
    def current_log_file(self) -> Path:
        return Path(self.baseFilename)

    def _next_filename(self) -> Path:
        self.part_number += 1
        part_suffix = (
            ""
            if self.part_number == 1
            else f"_part-{self.part_number}"
        )

        return self.log_dir / (
            f"{self.process_name}_{self.started_at}"
            f"_pid-{os.getpid()}{part_suffix}.log"
        )

    def emit(self, record: logging.LogRecord) -> None:
        if self.line_count >= self.max_lines:
            self.flush()

            if self.stream:
                self.stream.close()

            self.baseFilename = str(
                self._next_filename().absolute()
            )
            self.stream = self._open()
            self.line_count = 0

        super().emit(record)
        self.line_count += 1


def _remove_previous_handlers(root_logger: logging.Logger) -> None:
    for handler in root_logger.handlers[:]:
        if getattr(handler, MANAGED_HANDLER_ATTRIBUTE, False):
            root_logger.removeHandler(handler)
            handler.close()


def _route_uvicorn_logs_to_root(level: int) -> None:
    for logger_name in (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
    ):
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
        uvicorn_logger.setLevel(level)


def setup_logging(
    process_name: str,
    *,
    log_dir: str | Path | None = None,
    max_lines: int | None = None,
    level: str | int | None = None,
    console: bool = True,
    include_uvicorn: bool = False,
) -> Path:
    """Настраивает единый журнал процесса и возвращает путь к файлу."""

    resolved_log_dir = _resolve_log_dir(log_dir)
    resolved_max_lines = _resolve_max_lines(max_lines)
    resolved_level = _resolve_log_level(level)
    safe_process_name = _safe_process_name(process_name)
    resolved_log_dir.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(resolved_level)
    _remove_previous_handlers(root_logger)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%d.%m.%Y %H:%M:%S",
    )

    file_handler = LineCountHandler(
        log_dir=resolved_log_dir,
        process_name=safe_process_name,
        max_lines=resolved_max_lines,
    )
    file_handler.setLevel(resolved_level)
    file_handler.setFormatter(formatter)
    setattr(file_handler, MANAGED_HANDLER_ATTRIBUTE, True)
    root_logger.addHandler(file_handler)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(resolved_level)
        console_handler.setFormatter(formatter)
        setattr(console_handler, MANAGED_HANDLER_ATTRIBUTE, True)
        root_logger.addHandler(console_handler)

    if include_uvicorn:
        _route_uvicorn_logs_to_root(resolved_level)

    logging.getLogger(__name__).info(
        "Логирование процесса %s настроено: %s",
        safe_process_name,
        file_handler.current_log_file,
    )

    return file_handler.current_log_file
