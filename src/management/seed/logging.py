import logging
import sys


def setup_cli_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter(fmt="%(levelname)s [%(name)s] %(message)s")
    handler.setFormatter(formatter)

    # не дублируем хендлеры при повторных запусках
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False

    return logger
