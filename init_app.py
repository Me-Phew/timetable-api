import logging

from scheduler import configure_and_start_scheduler

formatter = logging.Formatter(
    "%(thread)d;%(threadName)s;%(asctime)s;%(levelname)s;%(message)s",
    "%Y-%m-%d %H:%M:%S",
)

file_handler = logging.FileHandler(f"init_app.log")
file_handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)


def init_app():
    logger.info("Initializing application")

    configure_and_start_scheduler()

    logger.info("Scheduler started")
