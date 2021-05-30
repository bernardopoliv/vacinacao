import logging


def setup_logging(module_name: str) -> logging.Logger:
    logger = logging.getLogger(module_name)
    logger.propagate = False
    logger.setLevel(logging.DEBUG)

    stream_log = logging.StreamHandler()
    stream_log.setLevel(logging.DEBUG)
    stream_log.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    logger.addHandler(stream_log)

    return logger
