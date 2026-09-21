"""Merkezi, yapılandırılmış (JSON) loglama. stdout -> Promtail -> Loki."""

import logging
import sys

from pythonjsonlogger import jsonlogger

from .correlation import get_correlation_id

_RESERVED = [*jsonlogger.RESERVED_ATTRS, "taskName", "color_message"]


class _ContextFilter(logging.Filter):
    def __init__(self, service_name: str, environment: str) -> None:
        super().__init__()
        self.service_name = service_name
        self.environment = environment

    def filter(self, record: logging.LogRecord) -> bool:
        record.service = self.service_name
        record.environment = self.environment
        record.correlation_id = get_correlation_id()
        record.__dict__.pop("color_message", None)
        return True


def configure_logging(service_name: str, level: str = "INFO", environment: str = "development") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s %(service)s %(environment)s %(correlation_id)s",
            rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger"},
            datefmt="%Y-%m-%dT%H:%M:%S%z",
            json_ensure_ascii=False,
            reserved_attrs=_RESERVED,
        )
    )
    handler.addFilter(_ContextFilter(service_name, environment))

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(name)
        lg.handlers = []
        lg.propagate = True
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    # pika her bağlantı denemesinde çok satırlı ERROR basar; hatayı kendi sarmalayıcılarımız tek satırda logluyor
    logging.getLogger("pika").setLevel(logging.CRITICAL)
    logging.getLogger("httpx").setLevel(logging.WARNING)
