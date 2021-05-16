import logging


def setup_logging(logger):
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    stream_log = logging.StreamHandler()
    stream_log.setLevel(logging.DEBUG)
    stream_log.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(stream_log)
