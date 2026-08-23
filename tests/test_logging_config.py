import logging

from services.logging_config import (
    MANAGED_HANDLER_ATTRIBUTE,
    LineCountHandler,
    setup_logging,
)


def _remove_managed_root_handlers() -> None:
    root_logger = logging.getLogger()

    for handler in root_logger.handlers[:]:
        if getattr(handler, MANAGED_HANDLER_ATTRIBUTE, False):
            root_logger.removeHandler(handler)
            handler.close()


def test_setup_logging_creates_directory_and_file(tmp_path):
    log_dir = tmp_path / "nested" / "logs"

    try:
        log_file = setup_logging(
            "test_process",
            log_dir=log_dir,
            console=False,
        )
        logging.getLogger("test.application").warning("Проверка журнала")

        for handler in logging.getLogger().handlers:
            handler.flush()

        assert log_dir.is_dir()
        assert log_file.is_file()
        assert log_file.name.startswith("test_process_")
        assert "Проверка журнала" in log_file.read_text(encoding="utf-8")
    finally:
        _remove_managed_root_handlers()


def test_line_count_handler_rotates_files(tmp_path):
    handler = LineCountHandler(
        log_dir=tmp_path,
        process_name="rotation_test",
        max_lines=2,
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    test_logger = logging.getLogger("test.rotation")
    previous_handlers = test_logger.handlers[:]
    previous_propagate = test_logger.propagate
    test_logger.handlers = [handler]
    test_logger.propagate = False
    test_logger.setLevel(logging.INFO)

    try:
        test_logger.info("первая")
        test_logger.info("вторая")
        test_logger.info("третья")
    finally:
        handler.close()
        test_logger.handlers = previous_handlers
        test_logger.propagate = previous_propagate

    log_files = sorted(tmp_path.glob("rotation_test_*.log"))

    assert len(log_files) == 2
    assert log_files[0].read_text(encoding="utf-8") == "первая\nвторая\n"
    assert log_files[1].read_text(encoding="utf-8") == "третья\n"
