import logging_loki
from multiprocessing import Queue
from galloper.constants import INTERNAL_LOKI_HOST, LOKI_PORT


def init_logger_handler():
    return logging_loki.LokiQueueHandler(
        Queue(-1),
        url=f"{INTERNAL_LOKI_HOST}:{LOKI_PORT}/loki/api/v1/push",
        tags={"application": "galloper"},
        version="1",
    )

