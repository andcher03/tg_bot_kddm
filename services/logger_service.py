import logging


logger = logging.getLogger("kddm_bot.audit")


class LoggerService:
    """Пишет аудит действий в журнал текущего процесса."""

    def write(
        self,
        user: str = "",
        role: str = "",
        section: str = "",
        action: str = "",
        result: str = "успешно",
    ) -> None:
        logger.info(
            "user=%s | role=%s | section=%s | action=%s | result=%s",
            user,
            role,
            section,
            action,
            result,
        )
