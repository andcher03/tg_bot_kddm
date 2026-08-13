from datetime import datetime

import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


class LoggerService:

    def write(
        self,
        user="",
        role="",
        section="",
        action="",
        result="✅"
    ):
        logging.info(
            "%s | %s | %s | %s | %s",
            user,
            role,
            section,
            action,
            result
        )